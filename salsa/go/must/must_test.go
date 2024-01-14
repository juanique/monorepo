package must_test

import (
	"errors"
	"testing"

	"github.com/juanique/monorepo/salsa/go/must"
	"github.com/stretchr/testify/suite"
)

// Define the suite struct
type MustTestSuite struct {
	suite.Suite
}

// All methods in this suite will run
func (suite *MustTestSuite) TestMustNoError() {
	f := func() (int, error) {
		return 42, nil
	}
	result := must.Must(f())
	suite.Equal(42, result)
}

func (suite *MustTestSuite) TestMustWithError() {
	val, err := 0, errors.New("some error")

	// We expect a panic here, so let's recover from it in the test
	defer func() {
		r := recover()
		suite.NotNil(r)
		suite.EqualError(r.(error), "some error")
	}()

	must.Must(val, err)
}

func (suite *MustTestSuite) TestNoErrorError() {
	err := errors.New("some error")

	// We expect a panic here, so let's recover from it in the test
	defer func() {
		r := recover()
		suite.NotNil(r)
		suite.EqualError(r.(error), "some error")
	}()

	must.NoError(err)
}

func TestRunMustTestSuite(t *testing.T) {
	suite.Run(t, new(MustTestSuite))
}
