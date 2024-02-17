package git

import (
	"fmt"
	"log"
	"os/user"
	"path/filepath"
	"strings"
	"time"

	libgit "github.com/libgit2/git2go/v33"
)

type Repo interface {
	// Equivalent to `git checkout -b <branchName>`
	CreateBranch(branchName string) error
	// Commit metadata of the current HEAD
	Head() (CommitMetadata, error)
	// Name of the current active branch
	ActiveBranch() (string, error)
	// Equivalent to `git commit -A -m <message>`
	Commit(message string) (string, error)
}

type repoImpl struct {
	RemotePath string
	LocalPath  string
	repo       *libgit.Repository
}

type CommitMetadata struct {
	Hash        string
	Description string
	Date        time.Time
}

func credentialsCallback(url string, usernameFromURL string, allowedTypes libgit.CredType) (*libgit.Cred, error) {
	// You might want to update the path according to your system's setup or obtain it from an environment variable.
	fmt.Println("This is the creds callback.")
	usr, err := user.Current()
	if err != nil {
		log.Fatalf("Failed to get current user: %v", err)
	}

	sshPublicKey := filepath.Join(usr.HomeDir, ".ssh", "id_ed25519.pub")
	sshPrivateKey := filepath.Join(usr.HomeDir, ".ssh", "id_ed25519")

	cred, err := libgit.NewCredentialSSHKey(usernameFromURL, sshPublicKey, sshPrivateKey, "")
	if err != nil {
		return nil, fmt.Errorf("Could not create ssh credentials: %w", err)
	}
	fmt.Println("sshPublicKey: ", sshPublicKey)
	fmt.Println("sshPrivateKey: ", sshPrivateKey)
	fmt.Println("cred:", cred)
	return cred, err
}

func certificateCheckCallback(cert *libgit.Certificate, valid bool, hostname string) error {
	return nil
}

func (repo *repoImpl) CreateBranch(branchName string) error {
	oid, err := repo.repo.RevparseSingle("HEAD")
	if err != nil {
		return fmt.Errorf("could not find HEAD %w", err)
	}
	commit, err := repo.repo.LookupCommit(oid.Id())
	if err != nil {
		return fmt.Errorf("Could not get HEAD commit %w", err)
	}

	branch, err := repo.repo.CreateBranch(branchName, commit, false /* force */)
	if err != nil {
		return fmt.Errorf("Could not create branch %w", err)
	}
	defer branch.Free()
	return nil
}

func (repo *repoImpl) Head() (CommitMetadata, error) {
	var commitMetadata CommitMetadata

	headRef, err := repo.repo.Head()
	if err != nil {
		return commitMetadata, fmt.Errorf("Failed to get HEAD reference: %s", err)
	}
	defer headRef.Free()

	commit, err := repo.repo.LookupCommit(headRef.Target())
	if err != nil {
		return commitMetadata, fmt.Errorf("Failed to lookup commit: %s", err)
	}
	defer commit.Free()

	commitMetadata.Hash = commit.Id().String()
	commitMetadata.Description = commit.Message()
	commitMetadata.Date = commit.Committer().When

	return commitMetadata, nil
}

func (repo *repoImpl) ActiveBranch() (string, error) {
	headRef, err := repo.repo.Head()
	if err != nil {
		return "", fmt.Errorf("Failed to get HEAD reference: %w", err)
	}

	branch, err := repo.repo.LookupBranch(headRef.Shorthand(), libgit.BranchLocal)
	if err != nil {
		return "", fmt.Errorf("Failed to lookup branch: %w", err)
	}
	defer branch.Free()

	branchName, err := branch.Name()
	if err != nil {
		return "", fmt.Errorf("Could not get branch name: %w", err)
	}

	return branchName, nil
}

func (repo *repoImpl) Commit(message string) (string, error) {
	// Load the index
	index, err := repo.repo.Index()
	if err != nil {
		return "", fmt.Errorf("failed to load repository index: %w", err)
	}

	// Add all changes to the index
	err = index.AddAll([]string{"."}, libgit.IndexAddDefault, nil)
	if err != nil {
		return "", fmt.Errorf("failed to stage changes: %w", err)
	}

	// Write the index to a tree
	treeId, err := index.WriteTree()
	if err != nil {
		return "", fmt.Errorf("failed to write tree: %w", err)
	}

	tree, err := repo.repo.LookupTree(treeId)
	if err != nil {
		return "", fmt.Errorf("failed to lookup tree: %w", err)
	}

	// Create the commit signature
	sig, err := repo.repo.DefaultSignature()
	if err != nil {
		return "", fmt.Errorf("failed to create signature: %w", err)
	}

	// Get HEAD as the parent commit
	parentCommit, err := repo.repo.Head()
	if err != nil {
		return "", fmt.Errorf("failed to get HEAD: %w", err)
	}
	parent, err := repo.repo.LookupCommit(parentCommit.Target())
	if err != nil {
		return "", fmt.Errorf("failed to lookup parent commit: %w", err)
	}

	// Commit
	commitId, err := repo.repo.CreateCommit("HEAD", sig, sig, message, tree, parent)
	if err != nil {
		return "", fmt.Errorf("failed to create commit: %w", err)
	}

	return commitId.String(), nil
}

func convertSSHUrl(url string) string {
	if strings.HasPrefix(url, "git@") {
		return strings.Replace(url, ":", "/", 1)
	}
	return url
}

func Clone(repoURL string, localPath string) (*repoImpl, error) {
	if libgit.Features()&libgit.FeatureSSH != 0 {
		fmt.Println("libgit2 has SSH support!")
	} else {
		fmt.Println("libgit2 does not have SSH support.")
	}

	fetchOptions := &libgit.FetchOptions{
		RemoteCallbacks: libgit.RemoteCallbacks{
			CredentialsCallback:      credentialsCallback,
			CertificateCheckCallback: certificateCheckCallback,
		},
	}

	repo, err := libgit.Clone(repoURL, localPath, &libgit.CloneOptions{
		FetchOptions:    *fetchOptions,
		CheckoutOptions: libgit.CheckoutOptions{Strategy: libgit.CheckoutForce},
	})
	if err != nil {
		return nil, fmt.Errorf("error cloning repository %s to %s: %w", repoURL, localPath, err)
	}

	return &repoImpl{RemotePath: repoURL, LocalPath: localPath, repo: repo}, nil
}

type InitOpts struct {
	ConfigFile string
}

func Init(localPath string, opts InitOpts) (*repoImpl, error) {
	repo, err := libgit.InitRepository(localPath, false /*isbare*/)
	if err != nil {
		return nil, fmt.Errorf("could not init git repo: %w", err)
	}

	if opts.ConfigFile != "" {
		c, err := libgit.NewConfig()
		if err != nil {
			return nil, fmt.Errorf("could not create config: %w", err)
		}

		// No idea what are good defaults for the arguments
		c.AddFile(opts.ConfigFile, libgit.ConfigLevelGlobal, true)
		if err = repo.SetConfig(c); err != nil {
			return nil, fmt.Errorf("could not set config: %w", err)
		}
	}

	// Create an empty tree
	treeBuilder, err := repo.TreeBuilder()
	if err != nil {
		return nil, fmt.Errorf("could not create repo tree: %w", err)
	}
	defer treeBuilder.Free()

	treeId, err := treeBuilder.Write()
	if err != nil {
		return nil, fmt.Errorf("could not build repo tree: %w", err)
	}

	tree, err := repo.LookupTree(treeId)
	if err != nil {
		return nil, fmt.Errorf("could not lookup repo tree: %w", err)
	}
	defer tree.Free()

	// Create the commit signature
	sig, err := repo.DefaultSignature()
	if err != nil {
		return nil, fmt.Errorf("failed to create signature: %w", err)
	}

	// Create an initial empty commit
	_, err = repo.CreateCommit("HEAD", sig, sig, "Initial commit", tree)
	if err != nil {
		log.Fatal(err)
	}

	newRepo := &repoImpl{LocalPath: localPath, repo: repo}

	return newRepo, nil
}

func Status() {
	// Open the local repository
	repo, err := libgit.OpenRepository(".")
	if err != nil {
		log.Fatalf("Could not open repository: %s", err)
	}

	// Get the status options
	opts := libgit.StatusOptions{}

	// Fetch the status list
	statusList, err := repo.StatusList(&opts)
	if err != nil {
		log.Fatalf("Could not get status: %s", err)
	}

	count, err := statusList.EntryCount()
	if err != nil {
		log.Fatalf("Failed to get status entry count: %s", err)
	}

	if count == 0 {
		fmt.Println("Working directory clean")
		return
	}

	for i := 0; i < count; i++ {
		entry, err := statusList.ByIndex(i)
		if err != nil {
			log.Fatalf("Error getting status entry: %s", err)
		}

		if entry.Status == libgit.StatusCurrent {
			continue
		}

		// Print the file status
		if (entry.Status&libgit.StatusIndexNew) != 0 || (entry.Status&libgit.StatusWtNew) != 0 {
			fmt.Printf("?? %s\n", entry.IndexToWorkdir.NewFile.Path)
		} else if (entry.Status & libgit.StatusWtModified) != 0 {
			fmt.Printf("M  %s\n", entry.IndexToWorkdir.NewFile.Path)
		} else if (entry.Status & libgit.StatusWtDeleted) != 0 {
			fmt.Printf("D  %s\n", entry.IndexToWorkdir.OldFile.Path)
		} // ... you can add other conditions for different statuses
	}
}
