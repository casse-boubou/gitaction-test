# Docker Pinned Package Checker

<ins>[Français](README.fr.md)</ins>
<ins>[English](README.en.md)</ins>

## About

A GitHub action that verifies that the versions of packages **pinned** (`apt-get install pkg=version`, `apk add pkg=version`, ...) in a `Dockerfile` are still up to date relative to the official repository of the base image's distribution.

The purpose of this check is to prevent a Docker image build from failing due to packages that are no longer available in the distribution’s package index used by the image, and to avoid starting the build until those packages are updated. This saves time that would otherwise be wasted waiting for the image to build only to have it fail at the `RUN` step (`RUN apt-get install pkg=version`, `RUN apk add pkg=version`).

## Detailed Description

For each provided `Dockerfile`, the action:

1. **Parses the Dockerfile** line by line (merging instructions split by `\`) and identifies each build step (`FROM ... AS ...`) along with its `RUN` instructions.
2. **Identifies pinned packages** in `RUN` instructions containing `apt-get install` or `apk add` using the `package=version` syntax.
3. **Determines the distribution and version of the base image** for the relevant step:
   - resolves tags based on an `ARG` variable (`FROM debian:${VERSION}`);
   - resolves tags based on a digest (`@sha256:...`);
   - if the base image is not natively recognized (Alpine / Ubuntu / Debian), the action uses [`syft`](https://github.com/anchore/syft) to scan the image and deduce its actual distribution and version.
4. **Downloads the official package index** corresponding to the detected distribution/version
5. **Compares** each version pinned in the `Dockerfile` to the version currently available in the official repository.
6. **Reports the result**:
   - `***** WARNING !!...` message is displayed in the logs for each obsolete package, along with the relevant line in the `Dockerfile` and the old/new version;
   - the job **fails** (non-zero exit code) if at least one pinned package is obsolete, and **succeeds** otherwise.

### Distributions and Package Managers Currently Supported

| Distribution | Package Manager | Direct Detection |
|---|---|---|
| Debian       | `apt`                   | ✅ |
| Ubuntu       | `apt`                   | ✅ |
| Alpine       | `apk`                   | ✅ |
| Other       | `apt` or `apk`          | ✅ via `syft` scan of the image |

## Prerequisites

- The repository must be checked out **before** this action (via [`actions/checkout`](https://github.com/actions/checkout)), because the action reads the `Dockerfile` from `$GITHUB_WORKSPACE`.
- A Linux runner with `bash` and `sudo` available (e.g., `ubuntu-latest`), as the action installs `syft` via a shell script.
- Outbound network access to: `pypi.org` (Python dependencies), `get.anchore.io` (installation of `syft`), as well as `deb.debian.org`, `security.debian.org`, `archive.ubuntu.com`, and `dl-cdn.alpinelinux.org` (downloading package indexes).

## Inputs

### Required

| Name | Description |
|---|---|
| `dockerfile` | Path, relative to the repository root (`$GITHUB_WORKSPACE`), to the `Dockerfile` to be analyzed. |

## Secrets Used

No secrets are required by the action.

> ⚠️ If the `Dockerfile` references a base image hosted on a private registry, the runner must already be authenticated (for example, via [`docker/login-action`](https://github.com/docker/login-action)) **before** this action runs, as this action does not handle registry authentication itself.

## Environment Variables Used

| Variable | Source | Role |
|---|---|---|
| `GITHUB_WORKSPACE` | Automatically provided by the GitHub Actions runner | Used to construct the absolute path to the `Dockerfile` from the `dockerfile` input. |
| `GITHUB_ACTION_PATH` | Automatically provided by the GitHub Actions runner | Used to locate the action’s internal files (`requirements.txt`, `main.py`, the `schema-latest.go` template used by `syft`). |
| `RUNNER_OS` | Automatically provided by the GitHub Actions runner | Used to determine the location of the `syft` binary on the runner. |
| `DOCKERFILE` | Defined by the action based on the `dockerfile` input | Exposed in the `Run the check` step; however, the actual path used by the script is constructed and passed as a command-line argument. |

## Example usage

```yaml
name: Check pinned Docker packages

on:
  pull_request:
    paths:
      - "**/Dockerfile"

jobs:
  docker-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Check pinned package versions
        uses: <owner>/<repo>@v1
        with:
          dockerfile: Dockerfile
```

> Remplacez `<owner>/<repo>@v1` par le chemin et la version réels de cette action une fois publiée.

### Exemple multi-Dockerfile

```yaml
jobs:
  docker-check:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        dockerfile:
          - Dockerfile
          - docker/worker/Dockerfile
    steps:
      - uses: actions/checkout@v7

      - name: Check pinned package versions (${{ matrix.dockerfile }})
        uses: <owner>/<repo>@v1
        with:
          dockerfile: ${{ matrix.dockerfile }}
```
