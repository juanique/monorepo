package ts

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/bazelbuild/bazel-gazelle/config"
	"github.com/bazelbuild/bazel-gazelle/language"
	"github.com/google/go-cmp/cmp"
)

func TestGenerateRules(t *testing.T) {
	tests := []struct {
		name         string
		files        []string
		wantRuleKind string
	}{
		{
			name:         "library with no main",
			files:        []string{"foo.ts", "bar.ts"},
			wantRuleKind: "ts_library",
		},
		{
			name:         "binary with main.ts",
			files:        []string{"main.ts", "utils.ts"},
			wantRuleKind: "ts_binary",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create a temporary directory for the test
			tmpDir, err := os.MkdirTemp("", "ts_test")
			if err != nil {
				t.Fatal(err)
			}
			defer os.RemoveAll(tmpDir)

			// Create test files
			for _, f := range tt.files {
				path := filepath.Join(tmpDir, f)
				if err := os.WriteFile(path, []byte(""), 0o644); err != nil {
					t.Fatal(err)
				}
			}

			// Create test arguments
			args := language.GenerateArgs{
				Config:       &config.Config{},
				Dir:          tmpDir,
				RegularFiles: tt.files,
			}

			// Generate rules
			lang := NewLanguage()
			result := lang.GenerateRules(args)

			// Check results
			if len(result.Gen) != 1 {
				t.Fatalf("got %d rules; want 1", len(result.Gen))
			}

			if got := result.Gen[0].Kind(); got != tt.wantRuleKind {
				t.Errorf("got rule kind %q; want %q", got, tt.wantRuleKind)
			}

			// Verify srcs attribute contains all files
			srcs := result.Gen[0].AttrStrings("srcs")
			if diff := cmp.Diff(tt.files, srcs); diff != "" {
				t.Errorf("srcs attribute mismatch (-want +got):\n%s", diff)
			}
		})
	}
}
