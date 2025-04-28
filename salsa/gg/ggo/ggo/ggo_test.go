package ggo_test

import (
	"testing"

	"github.com/juanique/monorepo/engprod/testfs"
	"github.com/juanique/monorepo/git"
	"github.com/juanique/monorepo/salsa/gg/ggo/ggo"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestGgo(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "Ggo Suite")
}

var _ = Describe("Ggo", func() {
	Describe("Clone Test", func() {
		var (
			fs           testfs.TestFS
			repoPath     string
			repo         git.Repo
			fileContents string
			clonePath    string
		)

		BeforeEach(func() {
			fs = testfs.New()
			fs.SetFileContents("config", `
[user]
	name=Mr Git
	email=mrgit@example.com
	username=mrgit
`)

			repoPath = fs.AbsPath("repo")
			var err error
			repo, err = git.Init(repoPath, git.InitOpts{ConfigFile: fs.AbsPath("config")})
			require.NoError(GinkgoT(), err)

			fileContents = "Hello, Git world!"
			fs.SetFileContents("repo/testfile.txt", fileContents)

			_, err = repo.Commit("Add testfile")
			require.NoError(GinkgoT(), err)

			clonePath = fs.AbsPath("clone")
			opts := ggo.CloneOpts{
				GlobalConfig: ggo.GlobalConfig{ConfigRoot: fs.AbsPath("gg_configs")},
			}
			_, err = ggo.Clone(repoPath, clonePath, opts)
			require.NoError(GinkgoT(), err)
		})

		It("should clone the repository and verify file contents", func() {
			clonedFileContents := fs.GetFileContents("clone/testfile.txt")
			assert.Equal(GinkgoT(), fileContents, clonedFileContents)
		})

		It("should verify the active branch is master", func() {
			activeBranch, err := repo.ActiveBranch()
			require.NoError(GinkgoT(), err)
			assert.Equal(GinkgoT(), "master", activeBranch)
		})

		It("should verify the commit description", func() {
			commit, err := repo.Head()
			require.NoError(GinkgoT(), err)
			assert.Equal(GinkgoT(), "Add testfile", commit.Description)
		})
	})
})
