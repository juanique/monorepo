package git_test

import (
	"log"
	"testing"

	"github.com/juanique/monorepo/engprod/testfs"
	"github.com/juanique/monorepo/git"
	"github.com/juanique/monorepo/salsa/go/must"
	"github.com/stretchr/testify/suite"
)

var gitconfig = `
[user]
	name=Mr Git
	email=mrgit@example.com
	username=mrgit
`

type GitRepoSuite struct {
	suite.Suite
	fs testfs.TestFS
}

func (suite *GitRepoSuite) SetupTest() {
	suite.fs = testfs.New()
	suite.fs.SetFileContents("config", gitconfig)
	log.Println("TestFS path: ", suite.fs.BasePath())
}

func (suite *GitRepoSuite) TestInitAndCloneRepo() {
	// Initialize a new Git repository
	repoPath := suite.fs.AbsPath("repo")
	repo, err := git.Init(repoPath, git.InitOpts{ConfigFile: suite.fs.AbsPath("config")})
	suite.Require().NoError(err)

	// Simulate coding activity by creating and modifying files
	fileContents := "Hello, Git world!"
	suite.fs.SetFileContents("repo/testfile.txt", fileContents)

	// Commit the changes
	_, err = repo.Commit("Add testfile")
	suite.Require().NoError(err)

	// Clone the repository to a new location
	clonePath := suite.fs.AbsPath("clone")
	repo, err = git.Clone(repoPath, clonePath)
	suite.Require().NoError(err)

	// Read the file from the cloned repository using TestFS
	clonedFileContents := suite.fs.GetFileContents("clone/testfile.txt")

	// Assert that the file contents in the cloned repo match the original
	suite.Equal(fileContents, clonedFileContents)

	// Verify active branch is master
	activeBranch := must.Must(repo.ActiveBranch())
	suite.Equal(activeBranch, "master")

	// Verify commit
	commit := must.Must(repo.Head())
	suite.Equal(commit.Description, "Add testfile")
}

func TestGitRepoSuite(t *testing.T) {
	suite.Run(t, new(GitRepoSuite))
}
