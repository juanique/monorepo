import os
from github import Github


if __name__ == "__main__":
    token = os.environ["GITHUB_GG_TOKEN"]
    g = Github(token)
    for repo in g.get_user().get_repos():
        print(repo.name)
