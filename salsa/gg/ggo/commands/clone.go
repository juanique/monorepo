package commands

import (
	"fmt"
	"os"
	"path"
	"strings"

	"github.com/juanique/monorepo/salsa/gg/ggo/ggo"
	"github.com/spf13/cobra"
)

var cloneCmd = &cobra.Command{
	Use:   "clone",
	Short: "Clone a git repository",
	Run: func(cmd *cobra.Command, args []string) {
		parts := strings.Split(args[0], "/")
		lastPart := parts[len(parts)-1]
		subParts := strings.Split(lastPart, ".")

		var resultPath string

		if len(subParts) > 1 {
			subdir := subParts[len(subParts)-2]

			// Get the current working directory
			cwd, err := os.Getwd()
			if err != nil {
				fmt.Println("Error:", err)
				return
			}

			// Join the current working directory with subdir
			resultPath = path.Join(cwd, subdir)
		} else {
			fmt.Println("No '.' found in last part of the path")
			os.Exit(1)
		}

		fmt.Println("Clonning... ", args[0])
		_, err := ggo.Clone(args[0], resultPath, ggo.CloneOpts{})
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}
	},
}

func init() {
	rootCmd.AddCommand(cloneCmd)
}
