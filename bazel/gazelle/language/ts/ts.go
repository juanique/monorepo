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

var nodeBuiltins = map[string]bool{
	"fs":      true,
	"path":    true,
	"crypto":  true,
	"http":    true,
	"https":   true,
	"url":     true,
	"util":    true,
	"os":      true,
	"stream":  true,
	"events":  true,
	"buffer":  true,
	"process": true,
	// Add other Node.js built-in modules as needed
}

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
		"js_library": {
			NonEmptyAttrs: map[string]bool{
				"srcs": true,
			},
			MergeableAttrs: map[string]bool{
				"srcs": true,
				"deps": true,
			},
		},
		"js_binary": {
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
		{
			Name:    "//bazel/js:js.bzl",
			Symbols: []string{"js_library", "js_binary"},
		},
	}
}

func (l *tsLang) GenerateRules(args language.GenerateArgs) language.GenerateResult {
	nilImport := 0
	var tsFiles []string
	var jsFiles []string
	var cssFiles []string
	hasMainTs := false
	hasMainJs := false

	for _, f := range args.RegularFiles {
		if strings.HasSuffix(f, ".ts") || strings.HasSuffix(f, ".tsx") {
			tsFiles = append(tsFiles, f)
			if f == "main.ts" || f == "main.tsx" {
				hasMainTs = true
			}
		} else if strings.HasSuffix(f, ".js") || strings.HasSuffix(f, ".jsx") {
			jsFiles = append(jsFiles, f)
			if f == "main.js" || f == "main.jsx" {
				hasMainJs = true
			}
		} else if strings.HasSuffix(f, ".css") {
			cssFiles = append(cssFiles, f)
		}
	}

	if len(tsFiles) == 0 && len(jsFiles) == 0 {
		return language.GenerateResult{}
	}

	deps := make(map[string]bool)

	// Process imports in all files
	for _, file := range append(tsFiles, jsFiles...) {
		filePath := filepath.Join(args.Dir, file)
		l.processImports(filePath, deps, args)
	}

	dirName := filepath.Base(args.Dir)
	var ruleKind string
	var srcs []string

	// If we have any TypeScript files, use ts_* rules
	if len(tsFiles) > 0 {
		srcs = append(tsFiles, jsFiles...)
		if hasMainTs {
			ruleKind = "ts_binary"
		} else {
			ruleKind = "ts_library"
		}
	} else {
		// JavaScript only
		srcs = jsFiles
		if hasMainJs {
			ruleKind = "js_binary"
		} else {
			ruleKind = "js_library"
		}
	}

	r := rule.NewRule(ruleKind, dirName)
	r.SetAttr("srcs", srcs)

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
			// For scoped packages (e.g. @playwright/test), we need to keep the full name
			if strings.HasPrefix(importPath, "@") {
				parts := strings.SplitN(importPath, "/", 3)
				if len(parts) >= 2 {
					packageName := parts[0] + "/" + parts[1]
					dep := l.GetThirdPartyImport(args, packageName)
					if dep != "" {
						deps[dep] = true
						continue
					}
				}
			} else {
				// For regular packages, just take the first part
				packageName := strings.Split(importPath, "/")[0]

				// Check if it's a Node.js built-in module
				if nodeBuiltins[packageName] {
					// Only add @types/node as dependency
					if typesDep := l.GetThirdPartyImport(args, "@types/node"); typesDep != "" {
						deps[typesDep] = true
					}
					continue
				}

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
