package must

// T is a type parameter that stands for any type.
func Must[T any](value T, err error) T {
	NoError(err)
	return value
}

// No error panics if the given err is not nil
func NoError(err error) {
	if err != nil {
		panic(err)
	}
}
