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

    # Parse Dockerfile for extract data
    instructionsliste = parse_dockerfile(dockerfile_path).instruction_list

    # Check and extract if pinned package is present in Dockerfile
    dataset = extract_dataset(instructionsliste)

    # Download a fresh version of depot for each version of distribution
    download_all_package_indexes(dataset)

    # Compare version for each packages
    all_outdated_packages = find_all_outdated_packages(dataset)
    show_warning = True
    for start_line, outdated_packages in all_outdated_packages.items():
        if outdated_packages and show_warning:
            print("***** WARNING !! some packages appear to be out of date. This could block the build of docker image")
            print("***** Check the corresponding versions for the following packages:")
            show_warning = False
        if outdated_packages:
            for package_name, versions in outdated_packages.items():
                print(f"***** Stage start at line {start_line}, {package_name}: {versions[0]} -> {versions[1]}")
                # continue

    # Determine exit status code
    determine_exit_code(dataset)
