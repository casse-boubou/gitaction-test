# Docker Check - Entry point: parses a Dockerfile, downloads the reference
# package archives for its base images, and reports any pinned package
# version that is out of date.

import sys

from scripts.exit_status import determine_exit_code
from scripts.extract_datas import extract_dataset
from scripts.manager_process import (
    download_all_package_indexes,
    find_all_outdated_packages,
)
from scripts.parser import parse_dockerfile

if __name__ == "__main__":

    dockerfile_path = sys.argv[1] if len(sys.argv) > 1 else "Dockerfile"

    # Parse the Dockerfile into a flat list of instructions
    instructions = parse_dockerfile(dockerfile_path).instruction_list

    # Build the dataset of every stage that pins at least one package
    dataset = extract_dataset(instructions)

    # Download a fresh package index for each distribution/version referenced
    download_all_package_indexes(dataset)

    # Compare each pinned version against the downloaded package index
    outdated_by_line = find_all_outdated_packages(dataset)
    show_warning = True
    for start_line, outdated_packages_by_distro in outdated_by_line.items():
        if outdated_packages_by_distro[2] and show_warning:
            print("***** WARNING !! some packages appear to be out of date. This could block the build of docker image")
            print("***** Check the corresponding versions for the following packages:")
            show_warning = False
        if outdated_packages_by_distro[2]:
            for package_name, versions in outdated_packages_by_distro[2].items():
                print(f"***** {package_name}: {versions[0]} -> {versions[1]} for {outdated_packages_by_distro[0]}:{outdated_packages_by_distro[1]} base image claim at line {start_line}")
                # continue

    # Determine and apply the final exit code
    determine_exit_code(outdated_by_line)
