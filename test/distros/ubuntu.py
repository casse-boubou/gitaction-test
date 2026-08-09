# ubuntu.py - Fonctions available for an ubuntu docker image
import gzip
import json
import lzma
import os
import re
from pathlib import Path

import requests
from scripts.enum_class import LatestSource, UbuntuRelease
from tqdm import tqdm


def catch_version(version):
    """Download the name of the version like it is in archive server"""
    if version == "latest":
        version = str(LatestSource.search_value("ubuntu"))
    version_match = re.search(
        r"(?P<major>[0-9]+.[0-9]+).?(?:.*)",
        version)
    if version_match:
        version = float(version_match.group('major'))
    return UbuntuRelease.search_key(version).lower()

def define_path(distribution=None , version=None, repository=None, component=None, packages_extention=None):
    """Determine many folderpath in one place"""
    directory_name = f"src/temp/{distribution}/{version}/{repository}"
    srcfilepath = f"src/temp/{distribution}/{version}/{repository}/{component}.{packages_extention}"
    destfilepath = f"src/temp/{distribution}/{version}/{repository}/{component}"
    archivespath = f"src/temp/{distribution}/{version}/{repository}"
    return directory_name, srcfilepath, destfilepath, archivespath


def extract_archive(source, destination_file):
    """Extract an archive and save they packages and version content"""
    packages = {}
    pkg_bloc = {}
    for line in source:
        line = line.rstrip("\n")

        if ": " in line:
            key, value = line.split(": ", 1)
            if key in ('Package', 'Version'):
                pkg_bloc[key] = value

        if not line:
            packages[pkg_bloc["Package"]] = pkg_bloc["Version"]
            pkg_bloc = {}
            continue

    with open(destination_file, "wt", encoding="utf-8") as destination:
        json.dump(packages, destination, indent=2)


def download_file_with_progress(url, save_path, ubuntu_version, pocket, component, chunk_size=1024):
    """Download a file and print a progress bar"""
    with requests.get(url, stream=True, timeout=20) as response:
        response.raise_for_status()
        total_size = int(response.headers.get("Content-Length", 0))

        # Initialize tqdm progress bar
        desc = f"Downloading ubuntu {ubuntu_version} {pocket} {component}"
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

        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    file.write(chunk)
                    # Update progress bar by chunk size
                    progress_bar.update(len(chunk))

        progress_bar.close()


def download_fresh_depot(distribution, version):
    """Download a fresh version of ubuntu depot"""
    pockets = ["base", "updates", "security", "backports"]
    components = ["main", "restricted", "universe", "multiverse"]

    # Catch ubuntu version
    ubuntu_version = catch_version(version)

    # Create Directory for version/pocket
    for pocket in pockets:
        directory_name = define_path(distribution=distribution, version=ubuntu_version, repository=pocket)[0]
        try:
            os.makedirs(directory_name)
            # print(f"Directory '{directory_name}' created successfully.")
        except FileExistsError:
            # print(f"Directory '{directory_name}' already exists.")
            pass
        except PermissionError:
            # print(f"Permission denied: Unable to create '{directory_name}'.")
            pass
        except Exception as e:
            print(f"An error occurred: {e}")


    packages_ext = "xz"
    # Create list of URL where download archives
    urls = {}
    for pocket in pockets:
        urls[pocket] = {}
        for component in components:
            if pocket == "base":
                url = f"http://archive.ubuntu.com/ubuntu/dists/{ubuntu_version}/{component}/binary-amd64/Packages.{packages_ext}"
                urls[pocket][component] = url
            else:
                url = f"http://archive.ubuntu.com/ubuntu/dists/{ubuntu_version}-{pocket}/{component}/binary-amd64/Packages.{packages_ext}"
                urls[pocket][component] = url

    # Download and extract archive if not exist
    for pocket, components in urls.items():
        for component, url in components.items():
            srcfilepath = define_path(distribution, ubuntu_version, pocket, component, packages_ext)[1]
            destfilepath = define_path(distribution, ubuntu_version, pocket, component)[2]
            fiile = Path(srcfilepath)
            if not fiile.exists():

                # Download archive
                download_file_with_progress(url, srcfilepath, ubuntu_version, pocket, component)

                # Extract archive
                if srcfilepath.endswith(".gz"):
                    with gzip.open(srcfilepath, "rt", encoding="utf-8") as source:
                        extract_archive(source, destfilepath)
                elif srcfilepath.endswith(".xz"):
                    with lzma.open(srcfilepath, "rt", encoding="utf-8") as source:
                        extract_archive(source, destfilepath)


def compare(distribution, version, packages):
    """Compare the version of package between Dockerfile and archive"""
    pockets = ["base", "updates", "security", "backports"]
    components = ["main", "restricted", "universe", "multiverse"]

    # Catch alpine version
    ubuntu_version = catch_version(version)

    outdated_packages = {}
    for pocket in pockets:
        for component in components:
            filefolder = define_path(distribution, ubuntu_version, pocket)[3]
            filepath = f"{filefolder}/{component}"
            file = Path(filepath)
            if file.exists():
                with open(file, "rt", encoding="utf-8") as archive:
                    for line in archive:
                        for package, value in packages.items():
                            if f"\"{package}\"" in line:
                                version_match = re.search(
                                    r"(?:.*):\s\"(?P<version>.*)\",",
                                    line)
                                if version_match:
                                    repo_version = version_match.group('version')
                                    if repo_version != value:
                                        outdated_packages[package] = [value, repo_version]
                                continue
    return outdated_packages
