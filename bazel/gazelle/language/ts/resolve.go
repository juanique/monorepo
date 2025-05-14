package ts

import (
	"github.com/bazelbuild/bazel-gazelle/config"
	"github.com/bazelbuild/bazel-gazelle/label"
	"github.com/bazelbuild/bazel-gazelle/repo"
	"github.com/bazelbuild/bazel-gazelle/resolve"
	"github.com/bazelbuild/bazel-gazelle/rule"
)

func (l *tsLang) Imports(c *config.Config, r *rule.Rule, f *rule.File) []resolve.ImportSpec {
	return nil
}

func (l *tsLang) Embeds(r *rule.Rule, from label.Label) []label.Label {
	return nil
}

func (l *tsLang) Fix(c *config.Config, f *rule.File) {}

func (l *tsLang) Resolve(c *config.Config, ix *resolve.RuleIndex, rc *repo.RemoteCache, r *rule.Rule, imports interface{}, from label.Label) {
}

func (l *tsLang) GetThirdPartyImport(c *config.Config, rel string, packageName string) string {
	// Get config for current directory
	cfgs := c.Exts[languageName].(TsConfigs)
	cfg := cfgs[rel]

	if cfg == nil {
		return ""
	}

	packageJSON := cfg.GetPackageJSON()
	if packageJSON == nil {
		return ""
	}

	// if it exists on the map:
	if _, ok := packageJSON.Dependencies[packageName]; ok {
		return "//:node_modules/" + packageName
	}

	// if it exists on the devDependencies map:
	if _, ok := packageJSON.DevDependencies[packageName]; ok {
		return "//:node_modules/" + packageName
	}

	return ""
}
