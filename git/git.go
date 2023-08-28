package git

import (
	"fmt"
	"log"
	"os"
	"os/user"
	"path/filepath"
	"strings"
	"time"

	libgit "github.com/libgit2/git2go/v27"
)

type Repo struct {
	RemotePath string
	LocalPath  string
	repo       *libgit.Repository
}

type CommitMetadata struct {
	Hash        string
	Description string
	Date        time.Time
}

func credentialsCallback(url string, usernameFromURL string, allowedTypes libgit.CredType) (libgit.ErrorCode, *libgit.Cred) {
	// You might want to update the path according to your system's setup or obtain it from an environment variable.
	usr, err := user.Current()
	if err != nil {
		log.Fatalf("Failed to get current user: %v", err)
	}

	sshPublicKey := filepath.Join(usr.HomeDir, ".ssh", "id_rsa.pub")
	sshPrivateKey := filepath.Join(usr.HomeDir, ".ssh", "id_rsa")

	retVal, cred := libgit.NewCredSshKey(usernameFromURL, sshPublicKey, sshPrivateKey, "")
	if retVal != 0 {
		return libgit.ErrorCode(retVal), nil
	}
	return libgit.ErrorCode(retVal), &cred
}

func certificateCheckCallback(cert *libgit.Certificate, valid bool, hostname string) libgit.ErrorCode {
	return libgit.ErrOk
}

func (repo *Repo) CreateBranch(branchName string) error {
	oid, err := repo.repo.RevparseSingle("HEAD")
	if err != nil {
		return fmt.Errorf("Could not find HEAD %w", err)
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

func (repo *Repo) Head() (CommitMetadata, error) {
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

func (repo *Repo) ActiveBranch() (string, error) {
	headRef, err := repo.repo.Head()
	if err != nil {
		return "", fmt.Errorf("Failed to get HEAD reference: %w", err)
	}

	// Ensure the reference is a branch
	if headRef.Type() != libgit.ReferenceSymbolic {
		return "", fmt.Errorf("HEAD is not a symbolic reference")
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

func convertSSHUrl(url string) string {
	if strings.HasPrefix(url, "git@") {
		return strings.Replace(url, ":", "/", 1)
	}
	return url
}

func LongClone(repoURL string, localPath, branch string) (*Repo, error) {
	if libgit.Features()&libgit.FeatureSSH != 0 {
		fmt.Println("libgit2 has SSH support!")
	} else {
		fmt.Println("libgit2 does not have SSH support.")
	}

	if strings.HasPrefix(repoURL, "git@github") {
		repoURL = convertSSHUrl(repoURL)
	}
	// 1. Create the directory
	if err := os.MkdirAll(localPath, 0755); err != nil {
		return nil, fmt.Errorf("error creating directory: %w", err)
	}

	// 2. Initialize it as a git repository
	repo, err := libgit.InitRepository(localPath, false)
	if err != nil {
		return nil, fmt.Errorf("error initializing repository: %w", err)
	}
	defer repo.Free()

	// 3. Add the repository URL as a remote
	remote, err := repo.Remotes.Create("origin", repoURL)
	if err != nil {
		return nil, fmt.Errorf("error adding remote: %w", err)
	}

	// Set up fetch options with a callback for credentials if needed.
	// Here's a simple example without authentication. Modify as required.
	fetchOptions := &libgit.FetchOptions{
		RemoteCallbacks: libgit.RemoteCallbacks{
			CredentialsCallback:      credentialsCallback,
			CertificateCheckCallback: certificateCheckCallback,
		},
	}

	// 4. Fetch the remote branch
	if err := remote.Fetch([]string{branch}, fetchOptions, ""); err != nil {
		return nil, fmt.Errorf("error fetching remote branch: %w", err)
	}

	// 5. Checkout the fetched branch
	fetchedBranch, err := repo.LookupBranch("origin/"+branch, libgit.BranchRemote)
	if err != nil {
		return nil, fmt.Errorf("error looking up fetched branch: %w", err)
	}
	defer fetchedBranch.Free()

	commit, err := repo.LookupCommit(fetchedBranch.Target())
	if err != nil {
		return nil, fmt.Errorf("error looking up commit from fetched branch: %w", err)
	}

	localBranch, err := repo.CreateBranch(branch, commit, false)
	if err != nil {
		return nil, fmt.Errorf("error creating local branch: %w", err)
	}
	defer localBranch.Free()

	tree, err := repo.LookupTree(localBranch.Target())
	if err != nil {
		return nil, fmt.Errorf("error looking up tree for local branch: %w", err)
	}

	if err := repo.CheckoutTree(tree, &libgit.CheckoutOpts{
		Strategy: libgit.CheckoutSafe | libgit.CheckoutRecreateMissing,
	}); err != nil {
		return nil, fmt.Errorf("error checking out tree: %w", err)
	}

	// Point HEAD to the new branch
	if err := repo.SetHead("refs/heads/" + branch); err != nil {
		return nil, fmt.Errorf("error setting HEAD to new branch: %w", err)
	}

	return &Repo{RemotePath: repoURL, LocalPath: localPath, repo: repo}, nil
}

func Clone(remotePath string, localPath string) (*Repo, error) {
	log.Println("Clonning", remotePath, "to", localPath)
	panic("wtf")
	cloneOpts := &libgit.CloneOptions{
		FetchOptions: &libgit.FetchOptions{
			RemoteCallbacks: libgit.RemoteCallbacks{
				CredentialsCallback:      credentialsCallback,
				CertificateCheckCallback: certificateCheckCallback,
			},
		},
	}
	repo, err := libgit.Clone(remotePath, localPath, cloneOpts)
	if err != nil {
		return nil, fmt.Errorf("Failed to clone repo: %w", err)
	}

	return &Repo{RemotePath: remotePath, LocalPath: localPath, repo: repo}, nil
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
