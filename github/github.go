package github

import (
	"context"

	gh "github.com/google/go-github/v38/github"
	"golang.org/x/oauth2"
)

type GitHubClient struct {
	client *gh.Client
	owner  string
	repo   string
}

func NewClient(token, owner, repo string) (*GitHubClient, error) {
	if token == "" {
		return nil, &ErrMissingToken{}
	}

	ctx := context.Background()
	ts := oauth2.StaticTokenSource(
		&oauth2.Token{AccessToken: token},
	)
	tc := oauth2.NewClient(ctx, ts)

	return &GitHubClient{
		client: gh.NewClient(tc),
		owner:  owner,
		repo:   repo,
	}, nil
}

func (g *GitHubClient) CreatePullRequest(remoteBranchName, title, baseBranch string) (*gh.PullRequest, error) {
	ctx := context.Background()

	newPR := &gh.NewPullRequest{
		Title: &title,
		Head:  &remoteBranchName,
		Base:  &baseBranch,
		// Body can also be provided if you have a description or other fields you'd like to set.
	}

	pr, _, err := g.client.PullRequests.Create(ctx, g.owner, g.repo, newPR)
	if err != nil {
		return nil, err
	}

	return pr, nil
}

type ErrMissingToken struct{}

func (e *ErrMissingToken) Error() string {
	return "GitHub token is missing"
}
