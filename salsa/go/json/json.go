package json

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"os"
)

// ToFile writes a struct to a file in JSON format
func ToFile(filename string, v any) error {
	// Marshal the struct to JSON
	jsonData, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return err
	}

	// Write JSON data to a file
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	_, err = file.Write(jsonData)
	return err
}

// FromFile reads a JSON file from the specified path and unmarshals it into the provided struct
func FromFile(filename string, v any) error {
	// Open the file
	file, err := os.Open(filename)
	if err != nil {
		return fmt.Errorf("failed to open file: %w", err)
	}
	defer file.Close()

	// Read the file content
	byteValue, err := io.ReadAll(file)
	if err != nil {
		return fmt.Errorf("failed to read file: %w", err)
	}

	// Unmarshal the JSON data into the provided struct
	err = json.Unmarshal(byteValue, v)
	if err != nil {
		return fmt.Errorf("failed to unmarshal JSON: %w", err)
	}

	return nil
}

func MustToJSON(v any) string {
	jsonData, err := json.MarshalIndent(v, "", " ")
	if err != nil {
		log.Fatal(err)
	}
	return string(jsonData)
}

func FromJSON(jsonData string, v any) error {
	err := json.Unmarshal([]byte(jsonData), v)
	if err != nil {
		return err
	}
	return nil
}
