package main

import (
	"fmt"
	"os"

	"github.com/juanique/monorepo/genai/huggingface/hfapi"

	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "hfdownloader",
	Short: "Hugging Face Model Downloader",
	Long:  `Hugging Face Model Downloader is a CLI tool for downloading models and datasets from Hugging Face using an API token.`,
	Run: func(cmd *cobra.Command, args []string) {
		// Retrieve the flag values
		modelName, _ := cmd.Flags().GetString("model")
		apiToken, _ := cmd.Flags().GetString("token")

		if modelName == "" {
			fmt.Println("Model name is required.")
			return
		}

		urls, err := hfapi.FetchModelFilesList(modelName, apiToken, "", "")
		if err != nil {
			fmt.Printf("Error fetching file list for model %s: %v\n", modelName, err)
			return
		}

		for _, url := range urls {
			fmt.Println(url)
		}
	},
}

func init() {
	// Define flags for the root command
	rootCmd.PersistentFlags().String("model", "", "Name of the Hugging Face model to download")
	rootCmd.PersistentFlags().String("token", "", "API token for Hugging Face")
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
