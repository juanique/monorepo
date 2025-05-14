package ts

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/bazelbuild/bazel-gazelle/language"
	"github.com/bazelbuild/bazel-gazelle/rule"
)

// nodeBuiltins is a map of Node.js built-in modules.
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

func Log(args ...interface{}) {
	// Change this to true to debug when running the tool.
	// Gazelle cannot produce any stdout or tests will fail.
	if false {
		fmt.Println(args...)
	}
}

// RuleKindBuilder is a builder for the rule kind.
// It accumulates files and determines the type of rule to build.
type RuleKindBuilder struct {
	language   string
	isMain     bool
	isReactApp bool
}

func NewRuleKindBuilder() *RuleKindBuilder {
	return &RuleKindBuilder{
		language: "javascript",
		isMain:   false,
	}
}

func (b *RuleKindBuilder) Combine(file *SourceFile) *RuleKindBuilder {
	Log("Combining", file.BaseName)
	if file.FileType.Name == "typescript" {
		b.language = "typescript"
	}

	if file.IsMainFile {
		b.isMain = true
	}

	if file.BaseName == "App.tsx" {
		b.isReactApp = true
	}

	return b
}

func (b *RuleKindBuilder) Build() string {
	if b.isReactApp {
		return "react_app"
	}

	if b.language == "typescript" {
		if b.isMain {
			return "ts_binary"
		}
		return "ts_library"
	}

	if b.language == "javascript" {
		if b.isMain {
			return "js_binary"
		}
		return "js_library"
	}

	panic("unknown language: " + b.language)
}

// FilePattern defines a pattern for matching files and how to generate rules for them
type FilePattern struct {
	// Name of the pattern for debugging
	Name string
	// Function to match files
	Matches func(filename string) bool
	// Function to get rule kind
	GetRuleKind func(isMainFile bool) string
	// Function to get rule name from file name
	GetRuleName func(filename string) string
	// Function to check if it's a main file
	IsMainFile func(filename string) bool
	// Extra attrs for the target
	ExtraAttrs func(filename string) map[string]interface{}
}

func IsComponentTest(filename string) bool {
	// We consider component tests files that have a component name that starts
	// with uppercase and end with ".spec.tsx" or ".test.tsx"
	parts := strings.Split(filename, ".")
	if len(parts) < 2 {
		return false
	}

	// Check for uppercase component name
	if !strings.EqualFold(parts[0], strings.ToUpper(parts[0])) {
		return false
	}

	IsComponentTest := strings.HasSuffix(filename, ".spec.tsx") || strings.HasSuffix(filename, ".test.tsx")

	if IsComponentTest {
		Log(filename, "is a component test")
	} else {
		Log(filename, "is not a component test")
	}

	return IsComponentTest
}

// Define patterns for different file types
var (
	// Order matters here - more specific patterns should come first
	playwrightPattern = FilePattern{
		Name: "playwright",
		Matches: func(f string) bool {
			return strings.HasSuffix(f, ".pw.spec.ts") || strings.HasSuffix(f, ".pw.spec.js")
		},
		GetRuleKind: func(bool) string { return "playwright_test" },
		GetRuleName: func(f string) string {
			base := filepath.Base(f)
			return strings.TrimSuffix(strings.TrimSuffix(base, ".pw.spec.js"), ".pw.spec.ts") + "_test"
		},
		IsMainFile: func(string) bool { return false },
		ExtraAttrs: func(f string) map[string]interface{} {
			return map[string]interface{}{}
		},
	}

	vitestPattern = FilePattern{
		Name: "vitest",
		Matches: func(f string) bool {
			if strings.HasSuffix(f, ".pw.spec.ts") || strings.HasSuffix(f, ".pw.spec.js") {
				return false
			}

			return strings.HasSuffix(f, ".spec.ts") ||
				strings.HasSuffix(f, ".test.ts") ||
				strings.HasSuffix(f, ".spec.js") ||
				strings.HasSuffix(f, ".test.js") ||
				strings.HasSuffix(f, ".spec.tsx") ||
				strings.HasSuffix(f, ".test.tsx")
		},
		GetRuleKind: func(bool) string { return "vitest_test" },
		GetRuleName: func(f string) string {
			base := filepath.Base(f)
			name := base
			for _, ext := range []string{".spec.ts", ".test.ts", ".spec.js", ".test.js"} {
				name = strings.TrimSuffix(name, ext)
			}
			return name + "_test"
		},
		IsMainFile: func(string) bool { return false },
		ExtraAttrs: func(f string) map[string]interface{} {
			if IsComponentTest(f) {
				Log(f, "is a component test")
				return map[string]interface{}{"dom": true}
			}
			return map[string]interface{}{}
		},
	}

	typescriptPattern = FilePattern{
		Name: "typescript",
		Matches: func(f string) bool {
			// TypeScript file that's not a test file
			return (strings.HasSuffix(f, ".ts") || strings.HasSuffix(f, ".tsx")) &&
				!strings.HasSuffix(f, ".spec.ts") && !strings.HasSuffix(f, ".test.ts") &&
				!strings.HasSuffix(f, ".pw.spec.ts")
		},
		GetRuleKind: func(isMain bool) string {
			if isMain {
				return "ts_binary"
			}
			return "ts_library"
		},
		GetRuleName: func(f string) string {
			return filepath.Base(filepath.Dir(f))
		},
		IsMainFile: func(f string) bool {
			base := filepath.Base(f)
			return base == "main.ts" || base == "main.tsx"
		},
		ExtraAttrs: func(f string) map[string]interface{} {
			return map[string]interface{}{}
		},
	}

	javascriptPattern = FilePattern{
		Name: "javascript",
		Matches: func(f string) bool {
			// JavaScript file that's not a test file
			return (strings.HasSuffix(f, ".js") || strings.HasSuffix(f, ".jsx")) &&
				!strings.HasSuffix(f, ".spec.js") && !strings.HasSuffix(f, ".test.js") &&
				!strings.HasSuffix(f, ".pw.spec.js")
		},
		GetRuleKind: func(isMain bool) string {
			if isMain {
				return "js_binary"
			}
			return "js_library"
		},
		GetRuleName: func(f string) string {
			return filepath.Base(filepath.Dir(f))
		},
		IsMainFile: func(f string) bool {
			base := filepath.Base(f)
			return base == "main.js" || base == "main.jsx"
		},
		ExtraAttrs: func(f string) map[string]interface{} {
			return map[string]interface{}{}
		},
	}

	cssPattern = FilePattern{
		Name: "css",
		Matches: func(f string) bool {
			return strings.HasSuffix(f, ".css")
		},
		GetRuleKind: func(bool) string { return "" }, // CSS files are included as data
		GetRuleName: func(string) string { return "" },
		IsMainFile:  func(string) bool { return false },
		ExtraAttrs: func(f string) map[string]interface{} {
			return map[string]interface{}{}
		},
	}
)

// SourceFile represents a source file with pre-computed relationships and paths
type SourceFile struct {
	// Basic file information
	Path         string // Full path to the file
	RelativePath string // Path relative to repo root
	BaseName     string // Base name of the file (filename.ext)
	Dir          string // Directory containing the file
	RelativeDir  string // Directory relative to repo root
	PackageName  string // Package name of the file

	// File type information
	FileType   *FilePattern // Type of file (TypeScript, JavaScript, etc.)
	IsMainFile bool         // Whether this is a main entry point
	IsTestFile bool         // Whether this is a test file

	// Import resolution helpers
	RepoRoot    string // Path to repository root
	PackagePath string // Bazel package path
}

// NewSourceFile creates a new SourceFile with pre-computed relationships
func NewSourceFile(path string, fileType *FilePattern, args language.GenerateArgs) *SourceFile {
	relativePath, _ := filepath.Rel(args.Config.RepoRoot, path)
	baseName := filepath.Base(path)
	dir := filepath.Dir(path)
	relativeDir, _ := filepath.Rel(args.Config.RepoRoot, dir)

	return &SourceFile{
		Path:         path,
		RelativePath: relativePath,
		BaseName:     baseName,
		Dir:          dir,
		RelativeDir:  relativeDir,
		FileType:     fileType,
		IsMainFile:   fileType.IsMainFile(baseName),
		IsTestFile:   fileType == &playwrightPattern || fileType == &vitestPattern,
		RepoRoot:     args.Config.RepoRoot,
		PackagePath:  args.Rel,
		PackageName:  filepath.Base(filepath.Dir(path)),
	}
}

func (l *tsLang) GenerateRules(args language.GenerateArgs) language.GenerateResult {
	nilImport := 0

	// Map to hold files by pattern
	filesByPattern := make(map[*FilePattern][]*SourceFile)

	// Initialize map with all patterns
	filesByPattern[&playwrightPattern] = []*SourceFile{}
	filesByPattern[&vitestPattern] = []*SourceFile{}
	filesByPattern[&typescriptPattern] = []*SourceFile{}
	filesByPattern[&javascriptPattern] = []*SourceFile{}
	filesByPattern[&cssPattern] = []*SourceFile{}

	// First pass - categorize files by pattern
	for _, f := range args.RegularFiles {
		path := filepath.Join(args.Dir, f)

		// Skip files that don't match any pattern
		if matched := l.categorizeFile(f, path, filesByPattern, args); !matched {
			continue
		}
	}

	var rules []*rule.Rule

	// Create a map of files to their containing library target
	// Important: Generate the library rule first so test rules can depend on it
	libraryRule := l.generateLibraryRule(args, filesByPattern)

	if libraryRule != nil {
		rules = append(rules, libraryRule)
	}

	// Now that we've generated the library rule, we can add test rules with proper dependencies
	libraryName := filepath.Base(args.Dir)

	// Generate a single rule for all Playwright tests
	if files, ok := filesByPattern[&playwrightPattern]; ok && len(files) > 0 {
		testRule := l.generateCombinedTestRule(args, files, &playwrightPattern, libraryRule != nil, libraryName)
		rules = append(rules, testRule)
	}

	// Generate a single rule for all Vitest tests
	if files, ok := filesByPattern[&vitestPattern]; ok && len(files) > 0 {
		testRule := l.generateCombinedTestRule(args, files, &vitestPattern, libraryRule != nil, libraryName)
		rules = append(rules, testRule)
	}

	imports := []interface{}{}
	for range rules {
		imports = append(imports, nilImport)
	}
	return language.GenerateResult{
		Gen:     rules,
		Imports: imports,
	}
}

// categorizeFile assigns a file to a pattern category
func (l *tsLang) categorizeFile(f string, path string, filesByPattern map[*FilePattern][]*SourceFile, args language.GenerateArgs) bool {
	// Check patterns in order - the order of patterns in the map is not guaranteed,
	// so we check them in a specific order
	patterns := []*FilePattern{
		&playwrightPattern, // Most specific tests first
		&vitestPattern,     // Then general tests
		&typescriptPattern, // Then source files
		&javascriptPattern,
		&cssPattern, // Finally CSS files
	}

	for _, pattern := range patterns {
		if pattern.Matches(f) {
			sourceFile := NewSourceFile(path, pattern, args)
			filesByPattern[pattern] = append(filesByPattern[pattern], sourceFile)
			return true
		}
	}
	return false
}

// generateLibraryRule creates a library or binary rule for source files
func (l *tsLang) generateLibraryRule(args language.GenerateArgs, filesByPattern map[*FilePattern][]*SourceFile) *rule.Rule {
	tsFiles := filesByPattern[&typescriptPattern]
	jsFiles := filesByPattern[&javascriptPattern]
	cssFiles := filesByPattern[&cssPattern]

	if len(tsFiles) == 0 && len(jsFiles) == 0 {
		return nil
	}

	srcs := []string{}
	ruleKind := NewRuleKindBuilder()
	for _, file := range append(tsFiles, jsFiles...) {
		srcs = append(srcs, file.BaseName)
		ruleKind.Combine(file)
	}

	dirName := filepath.Base(args.Dir)

	// Create deps map for source files - but only include external dependencies
	srcDeps := make(map[string]bool)
	for _, file := range append(tsFiles, jsFiles...) {
		l.processImports(file, srcDeps, args)
	}

	r := rule.NewRule(ruleKind.Build(), dirName)
	r.SetAttr("srcs", srcs)

	dataDeps := []string{}
	for _, file := range cssFiles {
		dataDeps = append(dataDeps, file.BaseName)
	}
	if len(dataDeps) > 0 {
		r.SetAttr("data", dataDeps)
	}

	if len(srcDeps) > 0 {
		depsList := make([]string, 0, len(srcDeps))
		for dep := range srcDeps {
			depsList = append(depsList, dep)
		}
		r.SetAttr("deps", depsList)
	}

	return r
}

// generateCombinedTestRule creates a single rule for all test files of the same type
func (l *tsLang) generateCombinedTestRule(args language.GenerateArgs, testFiles []*SourceFile, pattern *FilePattern, hasLibrary bool, libraryName string) *rule.Rule {
	// Create a name for the combined test rule
	dirName := filepath.Base(args.Dir)
	ruleName := dirName + "_test"

	// Create a separate deps map for all test files
	testDeps := make(map[string]bool)

	// Process imports for each test file and check if any imports from the library
	for _, testFile := range testFiles {
		l.processImports(testFile, testDeps, args)
	}

	r := rule.NewRule(pattern.GetRuleKind(false), ruleName)
	srcs := []string{}
	for _, file := range testFiles {
		srcs = append(srcs, file.BaseName)
	}
	r.SetAttr("srcs", srcs)

	extraAttrs := pattern.ExtraAttrs(testFiles[0].BaseName)
	for k, v := range extraAttrs {
		r.SetAttr(k, v)
	}

	if len(testDeps) > 0 {
		depsList := make([]string, 0, len(testDeps))
		for dep := range testDeps {
			depsList = append(depsList, dep)
		}
		r.SetAttr("deps", depsList)
	}

	return r
}

// processImports processes the imports in a file and adds dependencies to the deps map
func (l *tsLang) processImports(sourceFile *SourceFile, deps map[string]bool, args language.GenerateArgs) {
	file, err := os.Open(sourceFile.Path)
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

		importPath := parts[1]
		// Remove any inline comments
		importPath = strings.Split(importPath, "//")[0]
		importPath = strings.Trim(importPath, " \"';")

		// Handle imports based on path type
		if !strings.HasPrefix(importPath, ".") && !strings.HasPrefix(importPath, "/") {
			// Package import (npm or internal)
			if !l.handleNpmImport(importPath, args, deps) {
				l.handleInternalImport(sourceFile, importPath, args, deps)
			}
		} else if strings.HasPrefix(importPath, ".") {
			// Relative import
			l.handleRelativeImport(sourceFile, importPath, args, deps)
		}
	}
}

// Add helper functions to handle different import types
func (l *tsLang) handleNpmImport(importPath string, args language.GenerateArgs, deps map[string]bool) bool {
	// Handle scoped packages
	if strings.HasPrefix(importPath, "@") {
		parts := strings.SplitN(importPath, "/", 3)
		if len(parts) >= 2 {
			packageName := parts[0] + "/" + parts[1]
			dep := l.GetThirdPartyImport(args.Config, args.Rel, packageName)
			if dep != "" {
				Log("[NPM import scoped]Adding dependency on", dep)
				deps[dep] = true
				return true
			}
		}
		return false
	}

	// Handle regular packages
	packageName := strings.Split(importPath, "/")[0]

	// Check if it's a Node.js built-in module
	if nodeBuiltins[packageName] {
		// Only add @types/node as dependency
		if typesDep := l.GetThirdPartyImport(args.Config, args.Rel, "@types/node"); typesDep != "" {
			Log("[Node built-in]Adding dependency on", typesDep)
			deps[typesDep] = true
		}
		return true
	}

	dep := l.GetThirdPartyImport(args.Config, args.Rel, packageName)
	if dep != "" {
		Log("[NPM import]Adding dependency on", dep)
		deps[dep] = true
		// Check for @types package
		typesPackage := "@types/" + packageName
		if typesDep := l.GetThirdPartyImport(args.Config, args.Rel, typesPackage); typesDep != "" {
			Log("[NPM types import]Adding dependency on", typesDep)
			deps[typesDep] = true
		}
		return true
	}

	return false
}

func (l *tsLang) handleInternalImport(sourceFile *SourceFile, importPath string, args language.GenerateArgs, deps map[string]bool) bool {
	// Split the import path
	parts := strings.Split(importPath, "/")
	importDir := filepath.Dir(importPath)

	if importDir == sourceFile.RelativeDir && !sourceFile.IsTestFile {
		// Dependency on same library, noop
		return true
	}

	if importDir == sourceFile.RelativeDir && sourceFile.IsTestFile {
		// Dependency on same library, but test file, add as test_suite
		dep := ":" + sourceFile.PackageName
		Log("[Internal import, test file]Adding dependency on", dep)
		deps[dep] = true
		return true
	}

	// Get directory path without the file
	dirPath := strings.Join(parts[:len(parts)-1], "/")

	if dirPath == "" {
		panic(fmt.Sprintf("Error resolving '%s' in file '%s': not a valid NPM package or valid monorepo path.", importPath, sourceFile.Path))
	}
	dep := "//" + dirPath
	Log("[Internal import]Adding dependency on", dep, "for", importPath)
	deps[dep] = true

	return true
}

func (l *tsLang) handleRelativeImport(sourceFile *SourceFile, importPath string, args language.GenerateArgs, deps map[string]bool) {
	// Resolve the absolute path of the import
	importFile := filepath.Join(sourceFile.Dir, importPath)
	importDir := filepath.Dir(importFile)

	// If the import is outside the current package, add a dependency
	if importDir != args.Dir {
		relImportDir, _ := filepath.Rel(args.Config.RepoRoot, importDir)
		dep := "//" + relImportDir
		Log("[Relative import]Adding dependency on", dep)
		deps[dep] = true
	}

	if importDir == args.Dir && sourceFile.IsTestFile {
		dep := ":" + sourceFile.PackageName
		Log("[Relative import, test file]Adding dependency on", dep)
		deps[dep] = true
	}
}
