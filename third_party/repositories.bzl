load("//third_party/libgit2:repositories.bzl", "libgit2_repositories")
load("//third_party/libssh2:repositories.bzl", "libssh2_repositories")
load("//third_party/pcre:repositories.bzl", "pcre_repositories")
load("//third_party/openssl:repositories.bzl", "openssl_repositories")
load("//third_party/binaries:repositories.bzl", "binary_repositories")
load("//third_party/alsa:repositories.bzl", "alsa_repositories")

def third_party_repositories():
    libgit2_repositories()
    libssh2_repositories()
    pcre_repositories()
    openssl_repositories()
    binary_repositories()
    alsa_repositories()
