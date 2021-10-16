## Monorepo

### Getting started

*Requirements*: `docker` must be installed.

```
# Clone the repository
git clone https://github.com/juanique/monorepo.git
cd monorepo

# Add build tools to path
export PATH=$PATH:`pwd`/bin

# Run a simple Python binary
bzl run //examples/python:version
```