package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "cli_example",
	Short: "A simple CLI application built with Cobra",
	Long:  `This is an example CLI application that demonstrates using third-party Go dependencies with Bazel and bzlmod.`,
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("Hello from the CLI example!")
		fmt.Println("This application uses the popular Cobra CLI library.")
	},
}

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Print the version number",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("cli_example v1.0.0")
	},
}

var greetCmd = &cobra.Command{
	Use:   "greet [name]",
	Short: "Greet someone by name",
	Args:  cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		name := args[0]
		fmt.Printf("Hello, %s! Nice to meet you.\n", name)
	},
}

func init() {
	rootCmd.AddCommand(versionCmd)
	rootCmd.AddCommand(greetCmd)
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}