# alpine.py - Fonctions available for an alpine docker image
import json
import os
import re
import tarfile
from pathlib import Path

import requests
from scripts.enum_class import LatestSource
from tqdm import tqdm


def catch_version(version):
    """Download the name of the version like it is in archive server"""
    if version == "latest":
        version = str(LatestSource.search_value("alpine"))
    alpine_match = re.search(
        r"^(?P<minor>[0-9]+.[0-9]*)(.[0-9]*)?$",
        version)
    if alpine_match:
        version = alpine_match.group('minor')
    return version

def define_path(distribution=None , version=None, repository=None, packages_extention=None):
    """Determine many folderpath in one place"""
    directory_name = f"src/temp/{distribution}/{version}"
    srcfilepath = f"src/temp/{distribution}/{version}/{repository}.{packages_extention}"
    destfilepath = f"src/temp/{distribution}/{version}/{repository}"
    return directory_name, srcfilepath, destfilepath


def extract_archive(source, destination_file):
    """Extract an archive and save they packages and version content"""
    packages = {}
    pkg_bloc = {}
    for line in source:
        line = line.rstrip("\n")

        if ":" in line:
            key, value = line.split(":", 1)
            if key in ('P', 'V'):
                pkg_bloc[key] = value

        if not line:
            packages[pkg_bloc["P"]] = pkg_bloc["V"]
            pkg_bloc = {}
            continue

    with open(destination_file, "wt", encoding="utf-8") as destination:
        json.dump(packages, destination, indent=2)


def download_file_with_progress(url, save_path, alpine_version, repository, chunk_size=1024):
    """Download a file and print a progress bar"""
    with requests.get(url, stream=True, timeout=20) as response:
        response.raise_for_status()
        total_size = int(response.headers.get("Content-Length", 0))

        # Initialize tqdm progress bar
        desc = f"Downloading alpine {alpine_version} {repository}"
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

        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    file.write(chunk)
                    # Update progress bar by chunk size
                    progress_bar.update(len(chunk))

        progress_bar.close()


def download_fresh_depot(distribution, version):
    """Download a fresh version of alpine depot"""
    repo = ["main", "community"]

    # Catch alpine version
    alpine_version = catch_version(version)

    # Create Directory for version
    directory_name = define_path(distribution=distribution, version=alpine_version)[0]
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


    packages_ext = "tar.gz"
    # Create list of URL where download archives
    urls = {}
    for rep in repo:
        url = f"https://dl-cdn.alpinelinux.org/alpine/v{alpine_version}/{rep}/x86_64/APKINDEX.tar.gz"
        urls[rep] = url

    # Download and extract archive if not exist
    for rep, url in urls.items():
        srcfilepath = define_path(distribution, alpine_version, rep, packages_ext)[1]
        destfilepath = define_path(distribution, alpine_version, rep)[2]
        fiile = Path(srcfilepath)
        if not fiile.exists():

            # Download archive
            download_file_with_progress(url, srcfilepath, alpine_version, rep)

            # Extract archive
            with tarfile.open(srcfilepath) as source:
                source.extract("APKINDEX", f"{destfilepath}/APKINDEX_temp")
                source.close()
            with open(f"{destfilepath}/APKINDEX_temp/APKINDEX", "rt", encoding="utf-8") as extracted:
                extract_archive(extracted, f"{destfilepath}/APKINDEX")


def compare(distribution, version, packages):
    """Compare the version of package between Dockerfile and archive"""
    repo = ["main", "community"]

    # Catch alpine version
    alpine_version = catch_version(version)

    outdated_packages = {}
    for rep in repo:
        filefolder = define_path(distribution, alpine_version, rep)[2]
        filepath = f"{filefolder}/APKINDEX"
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
