package ggo

import (
	"fmt"
	"os"
	"regexp"
	"strings"
	"time"

	"github.com/juanique/monorepo/git"
	"github.com/juanique/monorepo/github"
)

type GudCommit struct {
	// Unique but also readable string that identifies the GudCommit, also corresponds
	// to the git branch name in which the user works.
	ID string

	// The hash of the underlying git commit
	Hash string

	// The commit description
	Description string

	// Whether the commit originates from the remote repo or not, for example for commits
	// from the master branch
	Remote bool

	// Whether the commit is up to date with the remote and does not need to be uploaded
	Uploaded bool

	// The parallel git branch that holds the history for this GudCommit
	HistoryBranch string

	// The remote branch to which changes are pushed on amends
	UpstreamBranch string

	// The date in which the commit was created, only populated for remote commits
	Date time.Time
}

// GlobalConfig stores config values that go beyond specific GitGud instances
type GlobalConfig struct {
	ConfigRoot string
}

// Pull request metadata from a remotely hosted repo
type GudPullRequest struct{}

// Interface to interact with a remotely hosted repo such as GitHub
type HostedRepo interface {
	CreatePullRequest(title string, remote_branch string, remote_base_branch string) (GudPullRequest, error)
}

// Optional settings for Clone()
type CloneOpts struct {
	// A hosted repo instance to pass to GitGud instead of infer it from the clone URL
	HostedRepo HostedRepo

	// Global config values to use
	GlobalConfig GlobalConfig
}

// Main point of interaction with the GitGud repo
type GitGud struct {
	// Handler to the underlying repo
	repo git.Repo

	// Persisted local state
	state RepoState

	// Interface with remote
	hostedRepo HostedRepo
}

// Options when creating a new instance of GitGud
type NewGitGudOpts struct {
	HostedRepo HostedRepo
}

// Creates a new instance of GitGud
func NewGitGud(repo git.Repo, state RepoState, opts NewGitGudOpts) (*GitGud, error) {
	return &GitGud{
		repo:       repo,
		state:      state,
		hostedRepo: opts.HostedRepo,
	}, nil
}

// The state of the GitGud repo. It is persisted on disk and loaded every time
// the binary is initialized.
type RepoState struct {
	// The local path where the GitGud repo is
	RepoDir string

	// The ID of the root GudCommit
	Root string

	// The ID of the GudCommit that is at HEAD
	Head string

	// Extra repository metadata
	RepoMetadata RepoMetadata

	// The map of available GudCommits, indexed by ID
	Commits map[string]GudCommit

	// Global config values
	GlobalConfig GlobalConfig
}

// Metadata about a GitHub repository.
type GitHubRepoMetadata struct {
	// Repository owner, the first part of the URL in a github repo.
	Owner string

	// Repository name, the second part of the URL in a github repo.
	Name string
}

// Union type for different types of remote repositories metadata
type RepoMetadata struct {
	// The type of repository, determines which of the other properties of the
	// struct is populated.
	Type string

	// GitHub metadata in the case this corresponds to a github repo.
	GitHub GitHubRepoMetadata
}

// Whether there's no metadata set for the struct.
func (md RepoMetadata) Empty() bool {
	return md.Type == ""
}

// Parses a github URL into a GithubRepoMetadata struct.
func ParseGithubRepoUrl(url string) (GitHubRepoMetadata, error) {
	var meta GitHubRepoMetadata

	// For HTTPS URLs
	if strings.HasPrefix(url, "https") {
		re := regexp.MustCompile(`https://github.com/(.*)/([^\.]*).*`)
		parts := re.FindStringSubmatch(url)
		if len(parts) >= 3 { // parts[0] is the full match, parts[1] and parts[2] are the submatches
			meta.Owner = parts[1]
			meta.Name = parts[2]
			return meta, nil
		}
	}

	// For SSH URLs
	if strings.HasPrefix(url, "git@") {
		re := regexp.MustCompile(`git@github.com:(.*)/([^\.]*).*`)
		parts := re.FindStringSubmatch(url)
		if len(parts) >= 3 {
			meta.Owner = parts[1]
			meta.Name = parts[2]
			return meta, nil
		}
	}

	return meta, fmt.Errorf("unable to parse the provided URL: %s", url)
}

func initRemoteCommit(repo git.Repo) (GudCommit, error) {
	var commit GudCommit

	remoteBranch, err := repo.ActiveBranch()
	if err != nil {
		return commit, fmt.Errorf("Could not get active branch: w", err)
	}

	head, err := repo.Head()
	if err != nil {
		return commit, fmt.Errorf("Could not get HEAD information: %w", err)
	}

	commit.ID = remoteBranch + "@" + head.Hash[:8]
	commit.Hash = head.Hash
	commit.Description = head.Description
	commit.Remote = true
	commit.Uploaded = true
	commit.HistoryBranch = commit.ID
	commit.UpstreamBranch = remoteBranch
	commit.Date = head.Date

	err = repo.CreateBranch(commit.ID)
	if err != nil {
		return commit, fmt.Errorf("Could not create branch: %w", err)
	}

	return commit, nil
}

type GitHubHostedRepo struct {
	metadata GitHubRepoMetadata
	client   *github.Client
}

func (gh *GitHubHostedRepo) CreatePullRequest(title string, remote_branch string, remote_base_branch string) (GudPullRequest, error) {
	panic("not implemented")
}

func MakeHostedRepo(repoMetadata RepoMetadata) (HostedRepo, error) {
	if repoMetadata.Type == "github" {
		token, exists := os.LookupEnv("GITHUB_GG_TOKEN")
		if !exists {
			return nil, fmt.Errorf("Missing env variable GITHUB_GG_TOKEN")
		}

		ghClient, err := github.NewClient(token, repoMetadata.GitHub.Owner, repoMetadata.GitHub.Name)
		if err != nil {
			return nil, fmt.Errorf("Could not create github client: %w", err)
		}
		return &GitHubHostedRepo{
			metadata: repoMetadata.GitHub,
			client:   ghClient,
		}, nil
	}

	return nil, fmt.Errorf("Unknown repo type: %s", repoMetadata.Type)
}

func Clone(remotePath string, localPath string, opts CloneOpts) (*GitGud, error) {
	if opts.GlobalConfig == (GlobalConfig{}) {
		opts.GlobalConfig.ConfigRoot = "~/.config/gg"
	}

	var repoState RepoState
	if strings.Contains(remotePath, "github") {
		githubMetadata, err := ParseGithubRepoUrl(remotePath)
		if err != nil {
			return nil, fmt.Errorf("Could not parse github path: %w", err)
		}
		repoState.RepoMetadata = RepoMetadata{Type: "github", GitHub: githubMetadata}
	}
	repo, err := git.Clone(remotePath, localPath)
	if err != nil {
		return nil, fmt.Errorf("Could not clone repo: %w", err)
	}

	root, err := initRemoteCommit(repo)
	if err != nil {
		return nil, fmt.Errorf("Could not init remote commit: %w", err)
	}

	repoState.RepoDir = localPath
	repoState.Root = root.ID
	repoState.Head = root.ID
	repoState.Commits[root.ID] = root
	repoState.GlobalConfig = opts.GlobalConfig

	newOpts := NewGitGudOpts{}
	if !repoState.RepoMetadata.Empty() {
		hostedRepo, err := MakeHostedRepo(repoState.RepoMetadata)
		if err != nil {
			return nil, fmt.Errorf("Could not init hosted repo: %w", err)
		}
		newOpts.HostedRepo = hostedRepo
	}

	gg, err := NewGitGud(repo, repoState, newOpts)
	if err != nil {
		return nil, fmt.Errorf("Could not create GitGud: %w", err)
	}

	return gg, nil
}
