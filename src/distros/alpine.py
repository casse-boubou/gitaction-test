# alpine.py - Resolves the Alpine version, downloads the matching APKINDEX
# archives, and compares pinned package versions against them

import json
import os
import re
import tarfile
from pathlib import Path

import requests
from scripts.enum_class import LatestDistribVersion
from tqdm import tqdm


def resolve_target_version(version):
    """Turn a Dockerfile version string ('latest', '3.24.1'...) into the
    'major.minor' form used by the Alpine archive server (e.g. '3.24')."""
    if version == "latest":
        version = str(LatestDistribVersion.value_for_name("alpine"))
    alpine_match = re.search(
        r"^(?P<minor>[0-9]+.[0-9]*)(.[0-9]*)?$",
        version)
    if alpine_match:
        version = alpine_match.group('minor')
    return version

def build_repo_paths(distribution=None, version=None, repo_name=None, archive_extension=None):
    """Build the paths used to store and extract repository."""
    temp_dir_path = f"src/temp/{distribution}/{version}"
    archive_path = f"src/temp/{distribution}/{version}/{repo_name}.{archive_extension}"
    extracted_json_path = f"src/temp/{distribution}/{version}/{repo_name}"
    return temp_dir_path, archive_path, extracted_json_path


def parse_packages_to_json(packages_stream, output_json_path):
    """Read an archive file and write a {package: version} JSON
    file built from its Package/Version fields."""
    package_versions = {}
    entry_buffer = {}
    for line in packages_stream:
        line = line.rstrip("\n")

        if ":" in line:
            key, value = line.split(":", 1)
            if key in ('P', 'V'):
                entry_buffer[key] = value

        if not line:
            package_versions[entry_buffer["P"]] = entry_buffer["V"]
            entry_buffer = {}
            continue

    with open(output_json_path, "wt", encoding="utf-8") as destination:
        json.dump(package_versions, destination, indent=2)


def download_with_progress_bar(url, destination_path, resolved_version, repo_name, chunk_size=1024):
    """Stream-download a file to disk while displaying a progress bar."""
    with requests.get(url, stream=True, timeout=20) as response:
        response.raise_for_status()
        total_size = int(response.headers.get("Content-Length", 0))

        # Initialize tqdm progress bar
        desc = f"Downloading alpine {resolved_version} {repo_name}"
        desc = f"{desc:<40.40}"
        progress_bar = tqdm(
            desc=desc,
            total=total_size,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
            ncols=120,
            ascii=True,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
        )

        with open(destination_path, "wb") as output_file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    output_file.write(chunk)
                    # Update progress bar by chunk size
                    progress_bar.update(len(chunk))

        progress_bar.close()


def download_package_index(distribution, version):
    """Download and extract the archive of every repository
    skipping files already on disk."""
    repo_names = ["main", "community"]

    # Catch alpine version
    resolved_version = resolve_target_version(version)

    # Create Directory for version
    temp_dir_path = build_repo_paths(distribution=distribution, version=resolved_version)[0]
    try:
        os.makedirs(temp_dir_path)
        # print(f"Directory '{temp_dir_path}' created successfully.")
    except FileExistsError:
        # print(f"Directory '{temp_dir_path}' already exists.")
        pass
    except PermissionError:
        # print(f"Permission denied: Unable to create '{temp_dir_path}'.")
        pass
    except Exception as e:
        print(f"An error occurred: {e}")


    archive_extension = "tar.gz"
    # Create list of URL where download archives
    download_urls = {}
    for repo in repo_names:
        url = f"https://dl-cdn.alpinelinux.org/alpine/v{resolved_version}/{repo}/x86_64/APKINDEX.tar.gz"
        download_urls[repo] = url

    # Download and extract archive if not exist
    for repo, url in download_urls.items():
        archive_path = build_repo_paths(distribution, resolved_version, repo, archive_extension)[1]
        extracted_json_path = build_repo_paths(distribution, resolved_version, repo)[2]
        archive_file = Path(archive_path)
        if not archive_file.exists():

            # Download archive
            download_with_progress_bar(url, archive_path, resolved_version, repo)

            # Extract archive
            with tarfile.open(archive_path) as archive_stream:
                archive_stream.extract("APKINDEX", f"{extracted_json_path}/APKINDEX_temp")
                archive_stream.close()
            with open(f"{extracted_json_path}/APKINDEX_temp/APKINDEX", "rt", encoding="utf-8") as extracted_index:
                parse_packages_to_json(extracted_index, f"{extracted_json_path}/APKINDEX")


def find_outdated_packages(distribution, version, pinned_packages):
    """Compare the versions pinned in the Dockerfile against the versions
    found in the downloaded archive."""
    repo_names = ["main", "community"]

    # Catch alpine version
    resolved_version = resolve_target_version(version)

    outdated_versions_found = {}
    for repo_name in repo_names:
        repo_dir_path = build_repo_paths(distribution, resolved_version, repo_name)[2]
        index_file_path = f"{repo_dir_path}/APKINDEX"
        index_file = Path(index_file_path)
        if index_file.exists():
            with open(index_file, "rt", encoding="utf-8") as archive:
                for line in archive:
                    for package_name, pinned_version in pinned_packages.items():
                        if f"\"{package_name}\"" in line:
                            version_match = re.search(
                                r"(?:.*):\s\"(?P<version>.*)\",",
                                line)
                            if version_match:
                                repository_version = version_match.group('version')
                                if repository_version != pinned_version:
                                    outdated_versions_found[package_name] = [pinned_version, repository_version]
                            continue
    return outdated_versions_found
