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

func Clone(repoURL string, localPath string) (*Repo, error) {
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
	defer repo.Free()

	return &Repo{RemotePath: repoURL, LocalPath: localPath, repo: repo}, nil
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
