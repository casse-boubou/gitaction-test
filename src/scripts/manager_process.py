# manager_process.py - Orchestrates, for every stage found in the Dockerfile,
# downloading the matching distribution package index and comparing pinned package
# versions against it.

import importlib


def download_all_package_indexes(dataset):
    """Download a fresh package index for every distrib/version referenced by
    any stage in the dataset."""
    # Separate each stage of Dockerfile
    for stage_entries in dataset.values():
        if stage_entries:
            # Process for each stage
            for stage_entry in stage_entries:
                distrib_name = stage_entry[0]
                distrib_version = stage_entry[1]

                # Download the depot
                distrib_module = importlib.import_module(f"distros.{distrib_name}")
                distrib_module.download_package_index(distrib_name, distrib_version)


def find_all_outdated_packages(dataset):
    """Compare the pinned package versions of every stage against the
    downloaded archive."""
    # Separate each stage of Dockerfile

    all_outdated_packages = {}
    for stage_entries in dataset.values():
        for stage_entry in stage_entries:
            distrib_name = stage_entry[0]
            distrib_version = stage_entry[1]
            pinned_packages = stage_entry[2]
            distrib_module = importlib.import_module(f"distros.{distrib_name}")
            outdated_for_stage = distrib_module.find_outdated_packages(distrib_name, distrib_version, pinned_packages)
            all_outdated_packages[stage_entry[4]] = outdated_for_stage
    return all_outdated_packages
