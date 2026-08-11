# Docker Pinned Package Checker

<ins>[Français](README.md)</ins>
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
   - the job **fails** (non-zero exit code) if at least one pinned package is obsolete, and **succeeds** otherwise except for the distributions/versions listed in the optional [`allow_outdated_for`](#allowing-certain-distributionsversions-allow_outdated_for) input, which only produce a warning.

### Distributions and Package Managers Currently Supported

| Distribution | Package Manager | Direct Detection |
| --- | --- | --- |
| Debian | `apt` | ✅ |
| Ubuntu | `apt` | ✅ |
| Alpine | `apk` | ✅ |
| Other | `apt` or `apk` | ✅ via `syft` scan of the image |

### Allowing certain distributions/versions (`allow_outdated_for`)

By default, the action fails as soon as any pinned package is outdated, regardless of the base image's distribution or version. The optional `allow_outdated_for` input disables that failure for a chosen list of distribution/version pairs: outdated packages detected there only produce a warning in the logs, without failing the job — useful, for example, for a distribution you know you'll update later, or a version that's about to be deprecated.

The expected format is a string representing a Python dictionary, mapping each distribution name to the list of versions it covers:

```yaml
allow_outdated_for: "{'debian': ['12'], 'alpine': ['3.20', '3.22']}"
```

## Prerequisites

- The repository must be checked out **before** this action (via [`actions/checkout`](https://github.com/actions/checkout)), because the action reads the `Dockerfile` from `$GITHUB_WORKSPACE`.
- A Linux runner with `bash` and `sudo` available (e.g., `ubuntu-latest`), as the action installs `syft` via a shell script.
- Outbound network access to: `pypi.org` (Python dependencies), `get.anchore.io` (installation of `syft`), as well as `deb.debian.org`, `security.debian.org`, `archive.ubuntu.com`, and `dl-cdn.alpinelinux.org` (downloading package indexes).

## Inputs

### Required

| Name | Description |
| --- | --- |
| `dockerfile` | Path, relative to the repository root (`$GITHUB_WORKSPACE`), to the `Dockerfile` to be analyzed. |

### Optional

| Name | Description | Default |
| --- | --- | --- |
| `allow_outdated_for` | Whitelist of distributions/versions whose outdated packages don't fail the job (see [Allowing certain distributions/versions](#allowing-certain-distributionsversions-allow_outdated_for)). Python dict-literal string, e.g. `{'debian': ['12'], 'alpine': ['3.20', '3.22']}`. | `""` (no distribution covered) |

## Secrets Used

No secrets are required by the action.

> ⚠️ If the `Dockerfile` references a base image hosted on a private registry, the runner must already be authenticated (for example, via [`docker/login-action`](https://github.com/docker/login-action)) **before** this action runs, as this action does not handle registry authentication itself.

## Environment Variables Used

| Variable | Source | Role |
| --- | --- | --- |
| `GITHUB_WORKSPACE` | Automatically provided by the GitHub Actions runner | Used to construct the absolute path to the `Dockerfile` from the `dockerfile` input. |
| `GITHUB_ACTION_PATH` | Automatically provided by the GitHub Actions runner | Used to locate the action’s internal files (`requirements.txt`, `main.py`, the `schema-latest.go` template used by `syft`). |
| `RUNNER_OS` | Automatically provided by the GitHub Actions runner | Used to determine the location of the `syft` binary on the runner. |
| `DOCKERFILE` | Defined by the action based on the `dockerfile` input | Exposed in the `Run the check` step; however, the actual path used by the script is constructed and passed as a command-line argument. |
| `ALLOW_OUTDATED_FOR` | Defined by the action based on the `allow_outdated_for` input | Read by `scripts/exit_status.py` to determine which distributions/versions are exempt from failing the job. |

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
          allow_outdated_for: "{'debian': ['12'], 'alpine': ['3.20', '3.22']}" # OPTIONAL
```

> Replace `<owner>/<repo>@v1` with the actual path and version of this action once published.

### Multi-Dockerfile example

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
