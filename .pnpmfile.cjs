// Parses a platform-specific package name.
const supportedRegexp =
    /\b(darwin|linux|aix|android|freebsd|netbsd|openbsd|sunos|win32)-(arm64|x64|arm|ia32|loong64|mips64el|powerpc64|ppc64|riscv64|s390x)(?:-(gnu|eabi|musl|msvc|gnueabihf)\b)?(@[0-9.]+)?/;

const supportedPlatforms = new Set(['darwin-arm64', 'linux-x64', 'linux-arm64']);
const supportedABIs = new Set(['gnu']);

/**
 * Returns true if the package is supported. Useful to omit unneeded packages
 * since Bazel downloads optional dependencies.
 * @param {string} pkg
 * @returns {boolean}
 */
const isSupportedPackage = (pkg) => {
    const matches = supportedRegexp.exec(pkg);
    if (matches === null) {
        return true; // not a platform-specific package
    }
    const [, os, arch, abi] = matches;

    const isSupportedPlatform = supportedPlatforms.has(`${os}-${arch}`);
    const isSupportedABI = abi === undefined || supportedABIs.has(abi);
    return isSupportedPlatform && isSupportedABI;
};

/**
 * @typedef Lockfile
 * @property {Record<string, Package>} packages
 *
 * @typedef Package
 * @property {Record<string, string>} dependencies
 * @property {Record<string, string>} optionalDependencies
 */

/**
 * PNPM hook to modify the lockfile after all dependencies have been resolved.
 * @see https://pnpm.io/pnpmfile
 *
 * @param {Lockfile} lockfile
 * @param _context
 * @returns {Lockfile}
 */
const afterAllResolved = (lockfile, _context) => {
    for (const [name, pkgDef] of Object.entries(lockfile.packages)) {
        // Delete unsupported top-level packages.
        if (!isSupportedPackage(name)) {
            delete lockfile.packages[name];
            continue;
        }

        // Delete unsupported dependencies.
        for (const dep of Object.keys(pkgDef.dependencies || {})) {
            if (!isSupportedPackage(dep)) {
                delete pkgDef.dependencies[dep];
            }
        }

        // Delete unsupported optional dependencies.
        for (const dep of Object.keys(pkgDef.optionalDependencies || {})) {
            if (!isSupportedPackage(dep)) {
                delete pkgDef.optionalDependencies[dep];
            }
        }
    }
    return lockfile;
};

module.exports = {
    hooks: { afterAllResolved },
};
