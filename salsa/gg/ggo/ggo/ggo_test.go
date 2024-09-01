package ggo_test

import (
	"testing"

	"github.com/juanique/monorepo/engprod/testfs"
	"github.com/juanique/monorepo/git"
	"github.com/juanique/monorepo/salsa/gg/ggo/ggo"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestExample(t *testing.T) {
	// Use assert for non-fatal checks
	assert.Equal(t, 1, 1, "they should be equal")

	// Use require for fatal checks
	require.Equal(t, 1, 1, "they should be equal")
}

func TestClone(t *testing.T) {
	fs := testfs.New()
	fs.SetFileContents("config", `
[user]
	name=Mr Git
	email=mrgit@example.com
	username=mrgit
`)

	// Initialize a new Git repository
	repoPath := fs.AbsPath("repo")
	repo, err := git.Init(repoPath, git.InitOpts{ConfigFile: fs.AbsPath("config")})
	require.NoError(t, err)

	// Simulate coding activity by creating and modifying files
	fileContents := "Hello, Git world!"
	fs.SetFileContents("repo/testfile.txt", fileContents)

	// Commit the changes
	_, err = repo.Commit("Add testfile")
	require.NoError(t, err)

	// Clone the repository to a new location
	clonePath := fs.AbsPath("clone")
	opts := ggo.CloneOpts{
		GlobalConfig: ggo.GlobalConfig{ConfigRoot: fs.AbsPath("gg_configs")},
	}
	_, err = ggo.Clone(repoPath, clonePath, opts)
	require.NoError(t, err)

	// Read the file from the cloned repository using TestFS
	clonedFileContents := fs.GetFileContents("clone/testfile.txt")

	// Assert that the file contents in the cloned repo match the original
	assert.Equal(t, fileContents, clonedFileContents)

	// Verify active branch is master
	activeBranch, err := repo.ActiveBranch()
	require.NoError(t, err)
	assert.Equal(t, "master", activeBranch)

	// Verify commit
	commit, err := repo.Head()
	require.NoError(t, err)
	assert.Equal(t, "Add testfile", commit.Description)
}
