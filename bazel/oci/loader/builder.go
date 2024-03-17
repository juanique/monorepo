// Utilities for taking the output of an OCI image directory and building a
// combined image .tar
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"

	encodingjson "encoding/json"

	"github.com/juanique/monorepo/salsa/go/files"
	"github.com/juanique/monorepo/salsa/go/json"
	"github.com/juanique/monorepo/salsa/go/random"
	"github.com/juanique/monorepo/salsa/go/tarbuilder"
)

// OCI images have different types. This builder can only handle these.
var acceptedMediaTypes = map[string]bool{
	"application/vnd.oci.image.manifest.v1+json":           true,
	"application/vnd.docker.distribution.manifest.v2+json": true,
}

func WriteToBlob(content any, destDir string) (Descriptor, error) {
	// Marshal the JSON object
	jsonBytes, err := encodingjson.Marshal(content)
	if err != nil {
		return Descriptor{}, err
	}

	// Compute SHA256 hash
	hasher := sha256.New()
	_, err = hasher.Write(jsonBytes)
	if err != nil {
		return Descriptor{}, err
	}
	sha256Hash := hex.EncodeToString(hasher.Sum(nil))

	// Create file with hash as its name
	dest := filepath.Join(destDir, sha256Hash)
	file, err := os.Create(dest)
	if err != nil {
		return Descriptor{}, err
	}
	defer file.Close()

	// Write JSON to the file
	_, err = file.Write(jsonBytes)
	if err != nil {
		return Descriptor{}, err
	}

	return Descriptor{
		Digest: "sha256:" + sha256Hash,
		Size:   len(jsonBytes),
	}, nil
}

// Descriptor of an image artifact indexed by digest.
type Descriptor struct {
	MediaType string `json:"mediaType"`
	Size      int    `json:"size"`
	Digest    string `json:"digest"`
}

// A layer manifest for an OCI image.
type Manifest struct {
	MediaType string       `json:"mediaType"`
	Size      int          `json:"size"`
	Digest    string       `json:"digest"`
	Config    Descriptor   `json:"config"`
	Layers    []Descriptor `json:"layers"`
}

// This is the main index of the OCI directory layout.
type ImageIndex struct {
	SchemaVersion int        `json:"schemaVersion"`
	MediaType     string     `json:"mediaType"`
	Manifests     []Manifest `json:"manifests"`
}

// An abstract representation of an OCI image directory.
type Image struct {
	Path string `json:"path"`

	// Dynamically loaded
	Index    ImageIndex `json:"index"`
	Manifest Manifest   `json:"manifest"`
}

// BlobPath returns the directory where the blobs are stored in the OCI image directory.
func (i Image) BlobPath(digest string) string {
	return filepath.Join(i.Path, "blobs", strings.Replace(digest, ":", "/", -1))
}

// IndexPath returns the path to the index.json file in the OCI image directory.
func (i Image) IndexPath() string {
	return filepath.Join(i.Path, "index.json")
}

// ConfigBlobPath returns the path to the config blob in the OCI image directory.
func (i Image) ConfigBlobPath() string {
	return i.BlobPath(i.Manifest.Config.Digest)
}

// ManifestBlobPath returns the path to the manifest blob in the OCI image directory.
func (i Image) ManifestBlobPath() string {
	return i.BlobPath(i.Index.Manifests[0].Digest)
}

func (i *Image) AddLayersAsLabels(blobsDir string) error {
	var configData map[string]interface{}
	err := json.FromFile(i.ConfigBlobPath(), &configData)
	if err != nil {
		return err
	}

	nestedConfig, ok := configData["config"]
	if !ok {
		return fmt.Errorf("config json missing config key")
	}

	labels, ok := nestedConfig.(map[string]interface{})["Labels"]
	if !ok {
		nestedConfig.(map[string]interface{})["Labels"] = map[string]interface{}{}
		labels = nestedConfig.(map[string]interface{})["Labels"]
	}
	labelsMap, ok := labels.(map[string]interface{})
	if !ok {
		return fmt.Errorf("config json labels key is not a map")
	}

	blobDigests := []string{}
	for _, blobPath := range i.GetLayerBlobPaths() {
		blobDigests = append(blobDigests, filepath.Base(blobPath))
	}
	labelsMap["oci_layers"] = strings.Join(blobDigests, ",")
	configData["config"].(map[string]interface{})["Labels"] = labelsMap

	newConfig, err := WriteToBlob(configData, blobsDir)
	if err != nil {
		return err
	}

	newConfig.MediaType = "application/vnd.oci.image.config.v1+json"
	i.Manifest.Config = newConfig
	return nil
}

// GetLayerBlobPaths returns the paths to the image layer blobs in the OCI image directory.
func (i Image) GetLayerBlobPaths() []string {
	output := []string{}
	for _, layer := range i.Manifest.Layers {
		output = append(output, i.BlobPath(layer.Digest))
	}

	return output
}

// LoadManifest loads the manifest blob JSON file from the OCI image directory.
func (i *Image) LoadManifest() error {
	return json.FromFile(i.ManifestBlobPath(), &i.Manifest)
}

// LoadIndex loads the index.json file from the OCI image directory.
func (i *Image) LoadIndex() error {
	return json.FromFile(i.IndexPath(), &i.Index)
}

// NewImage creates a new Image from an OCI image directory.
func NewImage(path string) (Image, error) {
	image := Image{Path: path}
	if err := image.LoadIndex(); err != nil {
		return Image{}, err
	}
	if err := image.LoadManifest(); err != nil {
		return Image{}, err
	}

	return image, nil
}

// Outpufile represents a file that will be copied into the output tar.
type OutputFile struct {
	src string
	dst string
	rel string
}

// OutputManifest is the manifest.json file that will be written to the output tar.
type OutputManifest struct {
	Config   string   `json:"Config"`
	RepoTags []string `json:"RepoTags"`
	Layers   []string `json:"Layers"`
}

// ImageBuilder is a builder for creating an OCI image tar from an OCI image directory.
type ImageBuilder struct {
	stagingDir     string
	blobsDir       string
	outputManifest OutputManifest
	repoTags       []string

	// Stateful
	filesToCopy []OutputFile
	configPath  string
}

func (b *ImageBuilder) Prepare(i *Image) error {
	err := os.MkdirAll(b.blobsDir, 0o755)

	// By default we use the original config blob path
	b.configPath = i.ConfigBlobPath()

	if err != nil {
		return fmt.Errorf("Failed to create output dir: %w", err)
	}

	if !acceptedMediaTypes[i.Index.Manifests[0].MediaType] {
		return fmt.Errorf("Unsupported media type: %s", i.Index.Manifests[0].MediaType)
	}

	if err := i.AddLayersAsLabels(b.blobsDir); err != nil {
		return fmt.Errorf("Error adding layers as labels: %v", err)
	}

	b.outputManifest.RepoTags = b.repoTags

	b.configPath = filepath.Join(b.blobsDir, strings.Replace(i.Manifest.Config.Digest, "sha256:", "", -1))

	return nil
}

type BuildOpts struct {
	SkipLayers []string
}

// Build creates an OCI image tar from an OCI image directory.
func (b *ImageBuilder) Build(i Image, opts BuildOpts) (string, error) {
	configOutput := b.AddBlob(b.configPath)
	b.outputManifest.Config = configOutput.rel
	layersToSkip := []string{}

	for _, layerPath := range i.GetLayerBlobPaths() {
		skipped := false
		for _, skipLayer := range opts.SkipLayers {
			if filepath.Base(layerPath) == skipLayer {
				skipped = true
				layersToSkip = append(layersToSkip, skipLayer)
			}
		}

		if !skipped {
			// Once we need a layer, we need every other layer on top.
			break
		}
	}

	for _, layer := range i.GetLayerBlobPaths() {
		output := b.AddLayerBlob(layer, layersToSkip)
		b.outputManifest.Layers = append(b.outputManifest.Layers, output.rel)
	}

	tarInputs := []string{}
	for _, file := range b.filesToCopy {
		if file.src != file.dst {
			if files.FileExists(file.dst) {
				// TOOD(juan.munoz): Why does this happen sometimes? how should we handle it?
				continue
			}
			if err := files.CreateSymLink(file.src, file.dst); err != nil && file.src != file.dst {
				return "", err
			}
		}
		tarInputs = append(tarInputs, file.rel)
	}

	outputManifest := []OutputManifest{b.outputManifest}
	err := json.ToFile(b.GetOutputPath("manifest.json"), outputManifest)
	if err != nil {
		return "", err
	}
	tarInputs = append(tarInputs, "manifest.json")

	tarb, err := tarbuilder.New(b.stagingDir, b.GetOutputPath("image.tar"))
	if err != nil {
		return "", fmt.Errorf("failed to create tar builder: %w", err)
	}
	if err := tarb.Add(tarInputs); err != nil {
		return "", fmt.Errorf("failed to add files to tar: %w", err)
	}

	if err := tarb.Write(); err != nil {
		return "", fmt.Errorf("failed to write tar: %w", err)
	}
	return b.GetOutputPath("image.tar"), nil
}

// GetOutputPath returns the for a file in the staging dir that will be packaged into the tar.
func (b ImageBuilder) GetOutputPath(relPath string) string {
	return filepath.Join(b.stagingDir, relPath)
}

// AddBlob adds a blob to the list of files that will be copied into the tar.
func (b *ImageBuilder) AddBlob(blobPath string) OutputFile {
	f := OutputFile{
		src: blobPath,
		dst: filepath.Join(b.blobsDir, filepath.Base(blobPath)),
	}
	f.rel, _ = filepath.Rel(b.stagingDir, f.dst)
	b.filesToCopy = append(b.filesToCopy, f)
	return f
}

// AddLayerBlob adds a gzipped blob to the list of files that will be copied into the tar.
func (b *ImageBuilder) AddLayerBlob(blobPath string, skipLayers []string) OutputFile {
	f := OutputFile{
		src: blobPath,
		dst: filepath.Join(b.blobsDir, filepath.Base(blobPath)+".tar.gz"),
	}
	f.rel, _ = filepath.Rel(b.stagingDir, f.dst)

	skip := false
	for _, skipLayer := range skipLayers {
		if filepath.Base(blobPath) == skipLayer {
			skip = true
			log.Println("Skipping layer", skipLayer)
			break
		}
	}

	if !skip {
		b.filesToCopy = append(b.filesToCopy, f)
	}
	return f
}

// NewImageBuilder creates a new ImageBuilder.
func NewImageBuilder(imageSha string, repoTags []string) ImageBuilder {
	builder := ImageBuilder{
		stagingDir: "/tmp/" + random.String(10) + "_" + strings.Replace(imageSha, "sha256:", "", -1),
		repoTags:   repoTags,
	}
	log.Println("Staging dir is ", builder.stagingDir)
	builder.blobsDir = filepath.Join(builder.stagingDir, "blobs", "sha256")
	return builder
}
