package files

import (
	"os"
	"path/filepath"
)

func FileExists(filename string) bool {
	info, err := os.Stat(filename)
	if os.IsNotExist(err) {
		return false
	}
	return !info.IsDir()
}

// CreateSymLink creates a symbolic link from src to dest.
func CreateSymLink(src string, dest string) error {
	// Convert src to an absolute path
	src, err := filepath.Abs(src)
	if err != nil {
		return err // Return the error if any
	}

	// Convert dest to an absolute path
	dest, err = filepath.Abs(dest)
	if err != nil {
		return err // Return the error if any
	}

	// Create a symbolic link 'dest' that points to 'src'
	if err = os.Symlink(src, dest); err != nil {
		return err // Return the error if any
	}
	return nil // No error occurred
}
