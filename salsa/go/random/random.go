package random

import (
	"math/rand"
	"time"
)

const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

// RandomString generates a random string of the specified length.
func RandomString(length int) string {
	// Seed the random number generator to ensure different output each time
	rand.Seed(time.Now().UnixNano())

	// Create a byte slice of the length specified by the input
	b := make([]byte, length)
	for i := range b {
		b[i] = charset[rand.Intn(len(charset))] // Pick a random character from the charset
	}
	return string(b) // Convert the byte slice to a string and return it
}
