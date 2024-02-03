package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/juanique/monorepo/salsa/go/must"
	"github.com/spf13/cobra"
)

type Options struct {
	Output         string
	OnlyGetImageID bool
	LogToFile      string
	NoRun          bool // backwards compatibilty with rules_dockerk
}

var opts = Options{}

var rootCmd = &cobra.Command{
	Use:   "loader",
	Short: "loader is a tool that loads images into docker incrementally",
	Run: func(cmd *cobra.Command, args []string) {
		imagePath := args[0]
		repoTags := args[1:]

		image := must.Must(NewImage(imagePath))
		must.NoError(buildAndLoadImage(image, repoTags))
	},
}

func buildAndLoadImage(i Image, repoTags []string) error {
	ctx := context.Background()
	originalImage := i

	dockerImageId := i.Manifest.Config.Digest
	builder := NewImageBuilder(dockerImageId, repoTags)
	if err := builder.Prepare(&i); err != nil {
		log.Println("Could not prepare image:", err)

		// Undo any attempts to modify the image
		i = originalImage
	}

	if opts.OnlyGetImageID {
		fmt.Println(i.Manifest.Config.Digest)
		return nil
	}

	loader, err := NewDockerLoader()
	if err != nil {
		return err
	}

	if len(repoTags) == 0 {
		return fmt.Errorf("No repo tags specified")
	}

	firstTag := repoTags[0]
	existingLayers, err := loader.GetImageLayerDigests(ctx, firstTag)
	log.Println("Found existing layers:", existingLayers)
	if err != nil {
		return err
	}

	tarPath, err := builder.Build(i, BuildOpts{SkipLayers: existingLayers})
	if err != nil {
		return err
	}

	action := must.Must(loader.LoadTarIntoDocker(context.Background(), tarPath, i.Manifest.Config.Digest, repoTags))

	if opts.Output == "json" {
		fmt.Println(action.JSON())
		log.Println(action.JSON())
	}

	if action.AlreadyLoaded {
		log.Println("Image ID", dockerImageId, "was already loaded.")
		fmt.Println("Image ID", dockerImageId, "was already loaded.")
	}

	for _, tag := range action.TagsAlreadyPresent {
		log.Println("Image was already tagged with", tag)
		fmt.Println("Image was already tagged with", tag)
	}

	for _, tag := range action.TagsAdded {
		log.Println("Tagged image with", tag)
		fmt.Println("Tagged image with", tag)
	}

	return nil
}

func main() {
	startTime := time.Now()
	rootCmd.Flags().StringVar(&opts.Output, "output", "", "Format for the output")
	rootCmd.Flags().BoolVar(&opts.OnlyGetImageID, "only-get-image-id", false, "Only print the image ID, not build it")
	rootCmd.Flags().BoolVar(&opts.NoRun, "norun", false, "unused - only here for backwards compatibility with rules_docker")
	rootCmd.Flags().StringVar(&opts.LogToFile, "log-to-file", "", "whether to print logs to a file")

	if err := rootCmd.Execute(); err != nil {
		os.Exit(1)
	}
	log.Println("Total time:", time.Since(startTime))
}
