#include<iostream>
#include <stdio.h>
#if defined(_WIN64)
#include <windows.h>
#define OS "windows"
#elif __APPLE__
#define OS "macos"
#elif __linux__
#include <features.h>
#define OS "linux"
#elif __wasi__
#include <features.h>
#define OS "wasi"
#else
#   error "Unknown compiler!"
#endif

int main() {
    if (__cplusplus == 202101L) std::cout << "C++23";
    else if (__cplusplus == 202002L) std::cout << "C++20";
    else if (__cplusplus == 201703L) std::cout << "C++17";
    else if (__cplusplus == 201402L) std::cout << "C++14";
    else if (__cplusplus == 201103L) std::cout << "C++11";
    else if (__cplusplus == 199711L) std::cout << "C++98";
    else std::cout << "pre-standard C++." << __cplusplus;
    std::cout << "\n";

#if defined(_WIN64)
    DWORD version = GetVersion();
    DWORD majorVersion = (DWORD)(LOBYTE(LOWORD(version)));
    DWORD minorVersion = (DWORD)(HIBYTE(LOWORD(version)));

    DWORD build = 0;
    if (version < 0x80000000) {
        build = (DWORD)(HIWORD(version));
    }

    printf("%s %lu.%lu (%lu).\n", OS, majorVersion, minorVersion, build);
#elif defined __GLIBC__
    printf("%s glibc_%d.%d\n", OS, __GLIBC__, __GLIBC_MINOR__);
#else
    printf("%s non-glibc\n", OS);
#endif
    return 0;
}
