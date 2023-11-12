#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <errno.h>
#include <stdbool.h>

bool fileOrDirExists(const char *path) {
    struct stat statbuf;

    if (lstat(path, &statbuf) == -1) {
        if (errno == ENOENT) {
            // File or directory does not exist
            return false;
        } else {
            // An error other than ENOENT occurred, crash the program
            perror("Unexpected error occurred in lstat");
            exit(EXIT_FAILURE);
        }
    }

    // File or directory exists
    return true;
}

int main() {
    const char *path = "/tmp/pepito";  // Replace with your path

    if (fileOrDirExists(path)) {
        printf("The path '%s' exists.\n", path);
    } else {
        printf("The path '%s' does not exist.\n", path);
    }

    return 0;
}
