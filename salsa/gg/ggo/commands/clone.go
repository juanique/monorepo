package commands

import (
	"fmt"

	"github.com/spf13/cobra"
)

var cloneCmd = &cobra.Command{
	Use:   "clone",
	Short: "Clone a git repository",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("Clone is not implemented")
	},
}

func init() {
	rootCmd.AddCommand(cloneCmd)
}
