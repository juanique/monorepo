package hfapi

import (
	"encoding/json"
	"fmt"
	"net/http"
)

const (
	JsonModelsFileTreeURL = "https://huggingface.co/api/models/%s/tree/%s/%s"
	RawModelFileURL       = "https://huggingface.co/%s/raw/%s/%s"
)

type HFModel struct {
	Type string `json:"type"`
	Path string `json:"path"`
}

// FetchModelFilesList takes a model name, an API token, and optionally a branch and folder name,
// and returns a list of URLs for the files in the model's tree.
func FetchModelFilesList(modelName, token, branch, folderName string) ([]string, error) {
	if branch == "" {
		branch = "main" // default to main branch if not specified
	}

	jsonFileListURL := fmt.Sprintf(JsonModelsFileTreeURL, modelName, branch, folderName)

	// Create a new HTTP request
	req, err := http.NewRequest("GET", jsonFileListURL, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// If a token is provided, add it to the request's Authorization header
	if token != "" {
		req.Header.Add("Authorization", fmt.Sprintf("Bearer %s", token))
	}

	// Execute the HTTP request
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to fetch model file list, status code: %d", resp.StatusCode)
	}

	var filesList []HFModel
	if err := json.NewDecoder(resp.Body).Decode(&filesList); err != nil {
		return nil, fmt.Errorf("failed to decode file list JSON: %w", err)
	}

	var urls []string
	for _, file := range filesList {
		if file.Type != "directory" { // Skip directories
			fileURL := fmt.Sprintf(RawModelFileURL, modelName, branch, file.Path)
			urls = append(urls, fileURL)
		}
	}

	return urls, nil
}
