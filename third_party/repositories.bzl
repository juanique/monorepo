load("//third_party/libgit2:repositories.bzl", "libgit2_repositories")
load("//third_party/libssh2:repositories.bzl", "libssh2_repositories")

def third_party_repositories():
    libssh2_repositories()
    libgit2_repositories()
