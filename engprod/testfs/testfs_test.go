package testfs_test

import (
	"path/filepath"
	"testing"

	"github.com/juanique/monorepo/engprod/testfs"
	"github.com/stretchr/testify/suite"
)

type TestFSSuite struct {
	suite.Suite
	fs testfs.TestFS
}

func (suite *TestFSSuite) SetupTest() {
	suite.fs = testfs.New()
}

func (suite *TestFSSuite) TestSetAndGetFileContents() {
	fileName := "testfile.txt"
	content := "Hello, world!"

	suite.fs.SetFileContents(fileName, content)
	retrievedContent := suite.fs.GetFileContents(fileName)

	suite.Equal(content, retrievedContent)
}

func (suite *TestFSSuite) TestFileContains() {
	fileName := "testfile.txt"
	content := "Hello, world!"

	suite.fs.SetFileContents(fileName, content)
	suite.True(suite.fs.FileContains(fileName, "world"))
	suite.False(suite.fs.FileContains(fileName, "foobar"))
}

func (suite *TestFSSuite) TestFileContentsEqual() {
	fileName := "testfile.txt"
	content := "Hello, world!"

	suite.fs.SetFileContents(fileName, content)
	suite.True(suite.fs.FileContentsEqual(fileName, content))
	suite.False(suite.fs.FileContentsEqual(fileName, "Goodbye, world!"))
}

func (suite *TestFSSuite) TestAbsPath() {
	fileName := "testfile.txt"
	expectedPath := filepath.Join(suite.fs.AbsPath(""), fileName)

	suite.Equal(expectedPath, suite.fs.AbsPath(fileName))
}

func TestTestFSSuite(t *testing.T) {
	suite.Run(t, new(TestFSSuite))
}
