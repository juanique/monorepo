#include <git2.h>
#include <stdio.h>

int main() {
    git_repository *repo = NULL;
    int error;

    // Initialize the library
    git_libgit2_init();

    // Clone the repository
    error = git_clone(&repo, "https://github.com/libgit2/libgit2.git", "/tmp/libgit2", NULL);
    if (error < 0) {
        const git_error *e = git_error_last();
        printf("Error %d/%d: %s\n", error, e->klass, e->message);
        return error;
    }

    // Clean up
    git_repository_free(repo);
    git_libgit2_shutdown();

    return 0;
}
