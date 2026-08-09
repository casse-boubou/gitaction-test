# download_depo.py - Download an updated depot from source

import importlib


def download_all_depot(data):
    """Download a fresh version of multiple depot"""
    # Separate each stage of Dockerfile
    for value in data.values():
        if value:
            # print(value)
            # [['alpine', '3.24', {'cargo': '1.96.1-r0', 'git': '2.54.0-r0'}], ['alpine', '3.23', {'phase': '1.96.1-r0', 'seconde': '2.54.0-r0'}]]
            # Process for each stage
            for stage in value:
                # print(stage)
                # ['alpine', '3.24', {'cargo': '1.96.1-r0', 'git': '2.54.0-r0'}]
                distroname = stage[0]
                versionname = stage[1]

                # Download the depot
                extractfunct = importlib.import_module(f"distros.{distroname}")
                extractfunct.download_fresh_depot(distroname, versionname)


def compare_all_packages(data):
    """Compare the version of package between Dockerfile and archive"""
    # Separate each stage of Dockerfile

    all_outdated_packages = {}
    for value in data.values():
        for stage in value:
            distroname = stage[0]
            versionname = stage[1]
            packagespack = stage[2]
            extractfunct = importlib.import_module(f"distros.{distroname}")
            outdated_packages = extractfunct.compare(distroname, versionname, packagespack)
            all_outdated_packages[stage[4]] = outdated_packages
    return all_outdated_packages
