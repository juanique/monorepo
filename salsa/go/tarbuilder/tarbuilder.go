package tarbuilder

import (
	"archive/tar"
	"fmt"
	"io"
	"os"
	"path/filepath"
)

// TarBuilder is a struct for building tar archives
type TarBuilder struct {
	tw      *tar.Writer
	tarFile *os.File
	baseDir string
}

// New creates a new TarBuilder and initializes the tar file
func New(baseDir, tarName string) (*TarBuilder, error) {
	tarFile, err := os.Create(tarName)
	if err != nil {
		return nil, err
	}

	return &TarBuilder{
		tw:      tar.NewWriter(tarFile),
		tarFile: tarFile,
		baseDir: baseDir,
	}, nil
}

// addFileOrDir adds a file or directory to the tar archive
func (tb *TarBuilder) addFileOrDir(path string) error {
	if !filepath.IsAbs(path) {
		path = filepath.Join(tb.baseDir, path)
	}
	fi, err := os.Stat(path)
	if err != nil {
		return err
	}

	if fi.IsDir() {
		return tb.addDirToTar(path)
	}

	return tb.addFileToTar(path)
}

// AddFile adds a single file to the tar archive
func (tb *TarBuilder) AddFile(path string) error {
	err := tb.addFileOrDir(path)
	if err != nil {
		return fmt.Errorf("failed to add file %s to tar archive: %w", path, err)
	}
	return nil
}

// AddDirectory adds a directory to the tar archive
func (tb *TarBuilder) AddDirectory(path string) error {
	err := tb.addFileOrDir(path)
	if err != nil {
		return fmt.Errorf("failed to add directory %s to tar archive: %w", path, err)
	}
	return nil
}

// Add adds multiple files and/or directories to the tar archive
func (tb *TarBuilder) Add(paths []string) error {
	for _, path := range paths {
		if err := tb.addFileOrDir(path); err != nil {
			return fmt.Errorf("failed to add %s to tar archive: %w", path, err)
		}
	}
	return nil
}

// addFileToTar adds a single file to the tar archive
func (tb *TarBuilder) addFileToTar(path string) error {
	file, err := os.Open(path)
	if err != nil {
		return err
	}
	defer file.Close()

	stat, err := file.Stat()
	if err != nil {
		return err
	}

	relPath, err := filepath.Rel(tb.baseDir, path)
	if err != nil {
		return err
	}

	header, err := tar.FileInfoHeader(stat, relPath)
	if err != nil {
		return err
	}
	header.Name = relPath

	if err := tb.tw.WriteHeader(header); err != nil {
		return err
	}

	if !stat.IsDir() {
		_, err = io.Copy(tb.tw, file)
	}

	return err
}

// addDirToTar adds a directory to the tar archive
func (tb *TarBuilder) addDirToTar(path string) error {
	return filepath.Walk(path, func(file string, fi os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if file == path {
			// Skip the root directory itself
			return nil
		}

		return tb.addFileToTar(file)
	})
}

// Write finalizes the tar archive and closes the file
func (tb *TarBuilder) Write() error {
	if err := tb.tw.Close(); err != nil {
		tb.tarFile.Close() // attempt to close the file even if tw.Close() fails
		return fmt.Errorf("failed to close tar writer: %w", err)
	}
	return tb.tarFile.Close()
}
