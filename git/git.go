package main

import (
	"fmt"
	"log"

	git "github.com/libgit2/git2go/v27"
)

func main() {
	// Open the local repository
	repo, err := git.OpenRepository(".")
	if err != nil {
		log.Fatalf("Could not open repository: %s", err)
	}

	// Get the status options
	opts := git.StatusOptions{}

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

		if entry.Status == git.StatusCurrent {
			continue
		}

		// Print the file status
		if (entry.Status&git.StatusIndexNew) != 0 || (entry.Status&git.StatusWtNew) != 0 {
			fmt.Printf("?? %s\n", entry.IndexToWorkdir.NewFile.Path)
		} else if (entry.Status & git.StatusWtModified) != 0 {
			fmt.Printf("M  %s\n", entry.IndexToWorkdir.NewFile.Path)
		} else if (entry.Status & git.StatusWtDeleted) != 0 {
			fmt.Printf("D  %s\n", entry.IndexToWorkdir.OldFile.Path)
		} // ... you can add other conditions for different statuses
	}
}
