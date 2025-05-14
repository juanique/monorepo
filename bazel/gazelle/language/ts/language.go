package ts

import (
	"github.com/bazelbuild/bazel-gazelle/language"
)

const (
	languageName = "typescript"
)

// tsLang satisfies the language.Language interface. It is the Gazelle extension
// for TypeScript rules.
type tsLang struct {
	packageJSON *packageJSON
}

func (l *tsLang) Name() string { return languageName }

// NewLanguage initializes a new tsLang that satisfies the language.Language
// interface. This is the entrypoint for the extension initialization.
func NewLanguage() language.Language {
	return &tsLang{}
}
