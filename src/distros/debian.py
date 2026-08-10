# debian.py - Resolves the Debian codename, downloads the matching Packages
# indexes, and compares pinned package versions against them

import gzip
import json
import lzma
import os
import re
from pathlib import Path

import requests
from scripts.enum_class import DebianCodename, LatestDistribVersion
from tqdm import tqdm


def resolve_target_version(version):
    """Turn a Dockerfile version string ('latest', '12', '12.5'...) into the
    Debian codename used by the archive server (e.g. 'bookworm')."""
    if version == "latest":
        version = str(LatestDistribVersion.value_for_name("debian"))
    version_match = re.search(
        r"(?P<major>[0-9]+).?(?:.*)",
        version)
    if version_match:
        version = int(version_match.group('major'))
    return DebianCodename.name_for_value(version).lower()

def build_repo_paths(distribution=None, version=None, pocket=None, component=None, archive_extension=None):
    """Build the paths used to store and extract repository."""
    temp_dir_path = f"src/temp/{distribution}/{version}/{pocket}"
    archive_path = f"src/temp/{distribution}/{version}/{pocket}/{component}.{archive_extension}"
    extracted_json_path = f"src/temp/{distribution}/{version}/{pocket}/{component}"
    pocket_dir_path = f"src/temp/{distribution}/{version}/{pocket}"
    return temp_dir_path, archive_path, extracted_json_path, pocket_dir_path


def parse_packages_to_json(packages_stream, output_json_path):
    """Read an archive file and write a {package: version} JSON
    file built from its Package/Version fields."""
    package_versions = {}
    entry_buffer = {}
    for line in packages_stream:
        line = line.rstrip("\n")

        if ": " in line:
            key, value = line.split(": ", 1)
            if key in ('Package', 'Version'):
                entry_buffer[key] = value

        if not line:
            package_versions[entry_buffer["Package"]] = entry_buffer["Version"]
            entry_buffer = {}
            continue

    with open(output_json_path, "wt", encoding="utf-8") as destination:
        json.dump(package_versions, destination, indent=2)


def download_with_progress_bar(url, destination_path, resolved_version, pocket, component, chunk_size=1024):
    """Stream-download a file to disk while displaying a progress bar."""
    with requests.get(url, stream=True, timeout=20) as response:
        response.raise_for_status()
        total_size = int(response.headers.get("Content-Length", 0))

        # Initialize tqdm progress bar
        desc = f"Downloading debian {resolved_version} {pocket} {component}"
        desc = f"{desc:<50.50}"
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
    pockets_names = ["base", "updates", "security", "backports"]
    components_names = ["main", "contrib", "non-free", "non-free-firmware"]

    # Catch Debian codename
    resolved_version = resolve_target_version(version)

    # Create Directory for version/pocket
    for pocket in pockets_names:
        temp_dir_path = build_repo_paths(distribution=distribution, version=resolved_version, pocket=pocket)[0]
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


    archive_extension = "xz"
    # Create list of URL where download archives
    download_urls = {}
    for pocket in pockets_names:
        download_urls[pocket] = {}
        for component in components_names:
            if pocket == "base":
                url = f"http://deb.debian.org/debian/dists/{resolved_version}/{component}/binary-amd64/Packages.{archive_extension}"
                download_urls[pocket][component] = url
            elif pocket == "security":
                url = f"https://security.debian.org/debian-security/dists/{resolved_version}-{pocket}/{component}/binary-amd64/Packages.{archive_extension}"
                download_urls[pocket][component] = url
            else:
                url = f"http://deb.debian.org/debian/dists/{resolved_version}-{pocket}/{component}/binary-amd64/Packages.{archive_extension}"
                download_urls[pocket][component] = url

    # Download and extract archive if not exist
    for pocket, components in download_urls.items():
        for component, url in components.items():
            archive_path = build_repo_paths(distribution, resolved_version, pocket, component, archive_extension)[1]
            extracted_json_path = build_repo_paths(distribution, resolved_version, pocket, component)[2]
            archive_file = Path(archive_path)
            if not archive_file.exists():

                # Download archive
                download_with_progress_bar(url, archive_path, resolved_version, pocket, component)

                # Extract archive
                if archive_path.endswith(".gz"):
                    with gzip.open(archive_path, "rt", encoding="utf-8") as archive_stream:
                        parse_packages_to_json(archive_stream, extracted_json_path)
                elif archive_path.endswith(".xz"):
                    with lzma.open(archive_path, "rt", encoding="utf-8") as archive_stream:
                        parse_packages_to_json(archive_stream, extracted_json_path)


def find_outdated_packages(distribution, version, pinned_packages):
    """Compare the versions pinned in the Dockerfile against the versions
    found in the downloaded archive."""
    pockets_names = ["base", "updates", "security", "backports"]
    components_names = ["main", "restricted", "universe", "multiverse"]

    # Catch Debian codename
    resolved_version = resolve_target_version(version)

    outdated_versions_found = {}
    for pocket in pockets_names:
        for component in components_names:
            pocket_dir_path = build_repo_paths(distribution, resolved_version, pocket)[3]
            component_file_path = f"{pocket_dir_path}/{component}"
            component_file = Path(component_file_path)
            if component_file.exists():
                with open(component_file, "rt", encoding="utf-8") as archive:
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
