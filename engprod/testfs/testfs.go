// package testfs makes it easy to manipulate the contents of a files in disk in the context of a test.
//
// It creates a tmp directory and provides functions to interact with the files on them. Example usage:
//
// fs := testfs.New()
// fs.SetFileContents("a.txt", "my contents")
// require.NoError(reverseFileContents(fs.AbsPath("a.txt")))
// require.True(fs.FileContentEquals("a.txt", "stnetnoc ym"))
package testfs

import (
	"os"
	"path/filepath"
	"strings"

	"github.com/juanique/monorepo/salsa/go/must"
)

type TestFS interface {
	// Sets the full contents of the given file in the test fs.
	SetFileContents(relPath string, contents string)
	// Reads the contents of the given file from the test fs.
	GetFileContents(relPath string) string
	// Returns true if the given file contains the given string
	FileContains(relPath string, contents string) bool
	// Returns true if the given file contains exactly the given string
	FileContentsEqual(relPath string, contents string) bool
	// Returns an absolute path of a file in the test fs given its relative path
	AbsPath(relPath string) string
}

// testFS is a concrete implementation of the TestFS interface
type testFS struct {
	basePath string
}

// New creates a new instance of testFS
func New() TestFS {
	tempDir, err := os.MkdirTemp("", "testfs")
	must.NoError(err)
	return &testFS{basePath: tempDir}
}

// SetFileContents sets the contents of a file in the test file system
func (t *testFS) SetFileContents(relPath string, contents string) {
	fullPath := filepath.Join(t.basePath, relPath)
	err := os.WriteFile(fullPath, []byte(contents), 0644)
	must.NoError(err)
}

// GetFileContents gets the contents of a file from the test file system
func (t *testFS) GetFileContents(relPath string) string {
	fullPath := filepath.Join(t.basePath, relPath)
	data := must.Must(os.ReadFile(fullPath))
	return string(data)
}

// FileContains checks if a file contains a given string
func (t *testFS) FileContains(relPath string, contents string) bool {
	fileContents := t.GetFileContents(relPath)
	return strings.Contains(fileContents, contents)
}

// FileContentsEqual checks if a file's contents exactly match a given string
func (t *testFS) FileContentsEqual(relPath string, contents string) bool {
	return t.GetFileContents(relPath) == contents
}

// AbsPath returns the absolute path of a file in the test file system
func (t *testFS) AbsPath(relPath string) string {
	return filepath.Join(t.basePath, relPath)
}
