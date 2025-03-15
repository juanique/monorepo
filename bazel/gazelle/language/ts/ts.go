package ts

import (
	"bufio"
	"encoding/json"
	"flag"
	"log"
	"os"
	"path/filepath"
	"strings"

	"github.com/bazelbuild/bazel-gazelle/config"
	"github.com/bazelbuild/bazel-gazelle/label"
	"github.com/bazelbuild/bazel-gazelle/language"
	"github.com/bazelbuild/bazel-gazelle/repo"
	"github.com/bazelbuild/bazel-gazelle/resolve"
	"github.com/bazelbuild/bazel-gazelle/rule"
	"github.com/juanique/monorepo/salsa/go/files"
)

type packageJSON struct {
	Dependencies    map[string]string `json:"dependencies"`
	DevDependencies map[string]string `json:"devDependencies"`
}

type tsLang struct {
	packageJSON *packageJSON
}

func NewLanguage() language.Language {
	return &tsLang{}
}

func (lang *tsLang) GetThirdPartyImport(args language.GenerateArgs, packageName string) string {
	if lang.packageJSON == nil {
		filePath := filepath.Join(args.Config.RepoRoot, "package.json")
		// Read package.json
		packageJsonExists, err := files.FileExists(filePath)
		if err != nil {
			log.Fatalf("failed to check if package.json exists: %v", err)
		}

		packageJSON := &packageJSON{}
		if packageJsonExists {
			data, err := os.ReadFile("package.json")
			if err != nil {
				log.Fatalf("failed to read package.json: %v", err)
			}

			if err := json.Unmarshal(data, packageJSON); err != nil {
				log.Fatalf("failed to parse package.json: %v", err)
			}
		}
		lang.packageJSON = packageJSON
	}

	// if it exists on the map:
	if _, ok := lang.packageJSON.Dependencies[packageName]; ok {
		return "//:node_modules/" + packageName
	}

	// if it exists on the devDependencies map:
	if _, ok := lang.packageJSON.DevDependencies[packageName]; ok {
		return "//:node_modules/" + packageName
	}

	return ""
}

func (*tsLang) KnownDirectives() []string {
	return []string{}
}

func (*tsLang) Resolve(c *config.Config, ix *resolve.RuleIndex, rc *repo.RemoteCache, r *rule.Rule, imports interface{}, from label.Label) {
}

func (*tsLang) RegisterFlags(fs *flag.FlagSet, cmd string, c *config.Config) {
}

func (*tsLang) Name() string { return "typescript" }

func (*tsLang) Embeds(r *rule.Rule, from label.Label) []label.Label {
	return nil
}

func (*tsLang) CheckFlags(fs *flag.FlagSet, c *config.Config) error {
	return nil
}

func (*tsLang) Kinds() map[string]rule.KindInfo {
	return map[string]rule.KindInfo{
		"ts_library": {
			NonEmptyAttrs: map[string]bool{
				"srcs": true,
			},
			MergeableAttrs: map[string]bool{
				"srcs": true,
				"deps": true,
			},
		},
		"ts_binary": {
			NonEmptyAttrs: map[string]bool{
				"srcs": true,
			},
			MergeableAttrs: map[string]bool{
				"srcs": true,
				"deps": true,
			},
		},
	}
}

func (*tsLang) Loads() []rule.LoadInfo {
	return []rule.LoadInfo{
		{
			Name:    "//bazel/ts:defs.bzl",
			Symbols: []string{"ts_library", "ts_binary"},
		},
	}
}

func (l *tsLang) GenerateRules(args language.GenerateArgs) language.GenerateResult {
	nilImport := 0
	// Check if there are any .ts files in the package
	var tsFiles []string
	var cssFiles []string
	hasMainTs := false
	for _, f := range args.RegularFiles {
		if strings.HasSuffix(f, ".ts") || strings.HasSuffix(f, ".tsx") {
			tsFiles = append(tsFiles, f)
			if f == "main.ts" {
				hasMainTs = true
			}
		} else if strings.HasSuffix(f, ".css") {
			cssFiles = append(cssFiles, f)
		}
	}

	if len(tsFiles) == 0 {
		return language.GenerateResult{}
	}

	deps := make(map[string]bool)

	// Process imports in each file
	for _, file := range tsFiles {
		filePath := filepath.Join(args.Dir, file)
		l.processImports(filePath, deps, args)
	}

	dirName := filepath.Base(args.Dir)
	// Create ts_binary rule if main.ts exists, otherwise create ts_library
	var ruleKind string
	if hasMainTs {
		ruleKind = "ts_binary"
	} else {
		ruleKind = "ts_library"
	}

	r := rule.NewRule(ruleKind, dirName)
	r.SetAttr("srcs", tsFiles)

	if len(cssFiles) > 0 {
		r.SetAttr("data", cssFiles)
	}

	if len(deps) > 0 {
		depsList := make([]string, 0, len(deps))
		for dep := range deps {
			depsList = append(depsList, dep)
		}
		r.SetAttr("deps", depsList)
	}

	imports := []interface{}{nilImport}
	return language.GenerateResult{
		Gen:     []*rule.Rule{r},
		Imports: imports,
	}
}

func (l *tsLang) processImports(filePath string, deps map[string]bool, args language.GenerateArgs) {
	file, err := os.Open(filePath)
	if err != nil {
		return
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := scanner.Text()
		if !strings.HasPrefix(line, "import") {
			continue
		}

		// Extract import path
		parts := strings.Split(line, "from")
		if len(parts) != 2 {
			continue
		}

		importPath := strings.Trim(parts[1], " \"';")

		// Case 1: Package from package.json
		if !strings.HasPrefix(importPath, ".") && !strings.HasPrefix(importPath, "/") {
			packageName := strings.Split(importPath, "/")[0]

			dep := l.GetThirdPartyImport(args, packageName)
			if dep != "" {
				deps[dep] = true
				// Check for @types package
				typesPackage := "@types/" + packageName

				if typesDep := l.GetThirdPartyImport(args, typesPackage); typesDep != "" {
					deps[typesDep] = true
				}
				continue
			}
		}

		// Case 2: Relative import
		if strings.HasPrefix(importPath, ".") {
			fileDir := filepath.Dir(filePath)
			importFile := filepath.Join(fileDir, importPath)
			importDir := filepath.Dir(importFile)
			if importDir == args.Dir {
				// Same directory, nothing to do
				continue
			}

			relImportDir, err := filepath.Rel(args.Config.RepoRoot, importDir)
			if err != nil {
				log.Fatalf("failed to get relative import dir: %v", err)
			}
			dep := "//" + relImportDir
			deps[dep] = true
			continue
		}

		// Case 3: Absolute import
		// The package of the current file
		currPackage := strings.ReplaceAll(args.Dir, args.Config.RepoRoot+"/", "")

		// Last part of the path is the filename, so we remove it to get the package name
		// e.g. /path/to/package/file -> /path/to/package
		packageName := strings.TrimSuffix(importPath, "/"+filepath.Base(importPath))
		if currPackage == packageName {
			// Same package, nothing to do
			continue
		}
		deps["//"+packageName] = true

	}
}

func (*tsLang) Fix(c *config.Config, f *rule.File) {
}

func (*tsLang) Imports(c *config.Config, r *rule.Rule, f *rule.File) []resolve.ImportSpec {
	return nil
}

func (*tsLang) Configure(c *config.Config, rel string, f *rule.File) {
}
