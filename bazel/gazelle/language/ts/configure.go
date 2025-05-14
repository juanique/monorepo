package ts

import (
	"encoding/json"
	"flag"
	"log"
	"os"
	"path/filepath"

	"github.com/bazelbuild/bazel-gazelle/config"
	"github.com/bazelbuild/bazel-gazelle/rule"
	"golang.verkada.com/vcorecommand/go/files"
)

// packageJSON represents the structure of a package.json file.
type packageJSON struct {
	Dependencies    map[string]string `json:"dependencies"`
	DevDependencies map[string]string `json:"devDependencies"`
}

// TsConfig stores TypeScript-specific configuration for a directory.
type TsConfig struct {
	parent      *TsConfig
	packageJSON *packageJSON
	directives  map[string][]string
	repoRoot    string
}

// TsConfigs maps directory paths to their configurations.
type TsConfigs map[string]*TsConfig

// ParentForPackage returns the configuration for the parent directory
// of the given package.
func (cfgs *TsConfigs) ParentForPackage(pkg string) *TsConfig {
	dir := filepath.Dir(pkg)
	if dir == "." {
		dir = ""
	}
	parent := (map[string]*TsConfig)(*cfgs)[dir]
	return parent
}

// NewTsConfig creates a new TypeScript configuration for a directory.
func NewTsConfig(repoRoot string) *TsConfig {
	cfg := &TsConfig{
		repoRoot:   repoRoot,
		directives: make(map[string][]string),
	}

	// Load package.json during initialization
	packageJSON, err := readPackageJSON(repoRoot)
	if err != nil {
		log.Printf("Warning: Failed to read package.json: %v", err)
	} else {
		cfg.packageJSON = packageJSON
	}

	return cfg
}

// NewChild creates a child configuration inheriting from this configuration.
func (cfg *TsConfig) NewChild() *TsConfig {
	return &TsConfig{
		parent:      cfg,
		packageJSON: cfg.packageJSON,
		directives:  cfg.directives,
		repoRoot:    cfg.repoRoot,
	}
}

// AddDirective adds a directive to this configuration.
func (cfg *TsConfig) AddDirective(key string, value string) {
	cfg.directives[key] = append(cfg.directives[key], value)
}

// GetPackageJSON returns the parsed package.json data.
func (cfg *TsConfig) GetPackageJSON() *packageJSON {
	return cfg.packageJSON
}

func (l *tsLang) RegisterFlags(fs *flag.FlagSet, cmd string, c *config.Config) {}

func (l *tsLang) CheckFlags(fs *flag.FlagSet, c *config.Config) error {
	return nil
}

func (l *tsLang) KnownDirectives() []string {
	return []string{}
}

func (l *tsLang) Configure(c *config.Config, rel string, f *rule.File) {
	// Create the root config if it doesn't exist
	if _, exists := c.Exts[languageName]; !exists {
		rootConfig := NewTsConfig(c.RepoRoot)
		c.Exts[languageName] = TsConfigs{"": rootConfig}
	}

	configs := c.Exts[languageName].(TsConfigs)

	config, exists := configs[rel]
	if !exists {
		parent := configs.ParentForPackage(rel)
		config = parent.NewChild()
		configs[rel] = config
	}

	if f == nil {
		return
	}

	for _, directive := range f.Directives {
		config.AddDirective(directive.Key, directive.Value)
	}
}

// Utility functions for reading and parsing package.json can be added here
func readPackageJSON(repoRoot string) (*packageJSON, error) {
	filePath := filepath.Join(repoRoot, "package.json")
	packageJsonExists, err := files.Exists(filePath)
	if err != nil {
		return nil, err
	}

	packageJSON := &packageJSON{}
	if packageJsonExists {
		data, err := os.ReadFile(filePath)
		if err != nil {
			return nil, err
		}

		if err := json.Unmarshal(data, packageJSON); err != nil {
			return nil, err
		}
	}
	return packageJSON, nil
}
