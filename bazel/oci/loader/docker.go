// Docker implementation of the image loader.
package main

import (
	"context"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"strings"
	"time"

	"github.com/docker/docker/api/types"
	"github.com/docker/docker/client"
	"github.com/juanique/monorepo/salsa/go/json"
)

// DockerLoadAction contains information of the action that was actually
// performed when requesting to load the image.  Since the image may have
// already been loaded, or may some of the tags were already set, this struct
// summarizes what needed to be done.
type DockerLoadAction struct {
	Digest             string   `json:"digest"`
	AlreadyLoaded      bool     `json:"alreadyLoaded"`
	TagsAdded          []string `json:"tagsAdded"`
	TagsAlreadyPresent []string `json:"tagsAlreadyPresent"`
	LoadTime           string   `json:"loadTime"`
}

// JSON returns the JSON representation of the DockerLoadAction
func (d DockerLoadAction) JSON() string {
	return json.MustToJSON(d)
}

// DockerLoader holds a Docker client and provides methods to interact with Docker.
type DockerLoader struct {
	cli *client.Client
}

// NewDockerLoader creates a new DockerLoader using sensible defaults.
func NewDockerLoader() (*DockerLoader, error) {
	cli, err := client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())
	if err != nil {
		return nil, fmt.Errorf("error creating Docker client: %w", err)
	}
	return &DockerLoader{cli: cli}, nil
}

// TagImage tags a Docker image with a new tag
func (d *DockerLoader) TagImage(ctx context.Context, imageID, tag string) error {
	err := d.cli.ImageTag(ctx, imageID, tag)
	if err != nil {
		return fmt.Errorf("error tagging image: %w", err)
	}
	return nil
}

// checkForExistingImage checks if an image with the specified ID exists in
// Docker.  If it does, it checks if all the tags are present.  If not, it tags
// the image with the missing tags.
func (d *DockerLoader) checkForExistingImage(ctx context.Context, imageID string, tags []string) (DockerLoadAction, error) {
	action := DockerLoadAction{}

	images, err := d.cli.ImageList(ctx, types.ImageListOptions{})
	if err != nil {
		return action, fmt.Errorf("error listing Docker images: %w", err)
	}

	tagsPresent := map[string]bool{}
	for _, tag := range tags {
		tagsPresent[tag] = false
	}

	var existingImage types.ImageSummary
	for _, image := range images {
		if image.ID == imageID {
			existingImage = image
			action.AlreadyLoaded = true
			break
		}
	}

	if !action.AlreadyLoaded {
		// We'll add all tags during the load itself
		action.TagsAdded = tags
		return action, nil
	}

	// The image was already there, we need to check if any extra tags are needed
	for _, tag := range existingImage.RepoTags {
		_, expected := tagsPresent[tag]
		if expected {
			tagsPresent[tag] = true
		}
	}

	for tag, alreadyPresent := range tagsPresent {
		if alreadyPresent {
			action.TagsAlreadyPresent = append(action.TagsAlreadyPresent, tag)
			continue
		}

		// Tag not there, we need to tag the image
		d.TagImage(ctx, imageID, tag)
		action.TagsAdded = append(action.TagsAlreadyPresent, tag)
	}

	action.Digest = imageID

	return action, nil
}

type LoadError struct {
	ErrorDetail struct {
		Message string `json:"message"`
	} `json:"errorDetail"`
}

func (d *DockerLoader) GetImageLayerDigests(ctx context.Context, label string) ([]string, error) {
	image, _, err := d.cli.ImageInspectWithRaw(ctx, label)
	if err != nil {
		if strings.Contains(err.Error(), "No such image") {
			return nil, nil
		}
		return nil, fmt.Errorf("error inspecting image: %w", err)
	}

	for labelKey, labelValue := range image.Config.Labels {
		if labelKey == "oci_layers" {
			return strings.Split(labelValue, ","), nil
		}
	}

	return nil, nil
}

// LoadTarIntoDocker ensures that the given tar is loaded and tagged with the given tags.
func (d *DockerLoader) LoadTarIntoDocker(ctx context.Context, tarPath, imageID string, repoTags []string) (DockerLoadAction, error) {
	start := time.Now()
	// Check if the image already exists
	action, err := d.checkForExistingImage(ctx, imageID, repoTags)
	if err != nil {
		return action, err
	}
	if action.AlreadyLoaded {
		action.LoadTime = time.Since(start).String()
		return action, nil
	}

	// Open the tar file
	tar, err := os.Open(tarPath)
	if err != nil {
		return action, fmt.Errorf("error opening tar file (%s): %w", tarPath, err)
	}
	defer tar.Close()

	// Load the tar file into Docker
	response, err := d.cli.ImageLoad(ctx, tar, true)
	if err != nil {
		return action, fmt.Errorf("error loading tar file into Docker: %w", err)
	}
	defer response.Body.Close()

	// Read all data from readCloser
	data, err := ioutil.ReadAll(response.Body)
	if err != nil {
		return action, fmt.Errorf("Error reading data: %W", err)
	}

	// Convert data to a string
	loadErr := LoadError{}
	json.FromJSON(string(data), &loadErr)
	if loadErr.ErrorDetail.Message != "" {
		log.Println("Load error:", loadErr.ErrorDetail.Message)
		return action, fmt.Errorf("Error loading tar file into Docker: %s", loadErr.ErrorDetail.Message)
	}

	action.Digest = imageID
	action.LoadTime = time.Since(start).String()
	return action, nil
}
