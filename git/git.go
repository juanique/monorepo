package git

import (
	"fmt"
	"log"
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

func Clone(remotePath string, localPath string) (*Repo, error) {
	cloneOpts := &libgit.CloneOptions{}
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
