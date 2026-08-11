# THANKS to @nawazdhandala https://oneuptime.com/blog/post/2026-02-08-how-to-parse-and-analyze-dockerfiles-programmatically/view
# extract_datas.py - Walks the parsed Dockerfile instructions to find, for
# each RUN step that pins package versions, which distribution/version the
# stage is built from and which packages/versions it pins.

import importlib
import json
import os
import re
import subprocess

from scripts.enum_class import SupportedDistribution, SupportedPackageManager


def resolve_arg_variable_version(instructionsliste, variable_name):
    """Search the parsed instructions for an `ARG variable_name="..."` line
    and return its plain-text default value, if any."""
    for entry in instructionsliste:
        if entry.command != "ARG":
            continue
        arg_pattern = f"^ARG\\s+{variable_name}=\"?(?P<version>.+?)\"?$"
        value_match = re.search(arg_pattern, entry.instruction_text)
        if value_match:
            return value_match.group('version')
    return None


def inspect_unknown_base_image(image_name, image_tag):
    """Use syft to scan a base image that isn't natively recognized, and
    return the (distrib_id, version_id) syft detects for it."""
    image_ref = f"{image_name}:{image_tag}"
    github_action_path = (os.environ["GITHUB_ACTION_PATH"]+"/") if os.environ.get("GITHUB_ACTION_PATH", "") else ""
    syft_location = "/usr/local/bin/syft" if os.environ.get("RUNNER_OS") else "/usr/local/Cellar/syft/1.51.0/bin/syft"
    syft_cmd = (syft_location, "scan", f"{image_ref}", "--output", "template", "--template", f"{github_action_path}src/scripts/schema-latest.go")
    print(f"Wait, searching for the base image of {image_ref} in progress...")
    syft_process = subprocess.run(syft_cmd, capture_output=True, check=True, text=True)
    syft_output = json.loads(syft_process.stdout)
    detected_distrib_id = syft_output["distro"]["id"]
    detected_version_id = syft_output["distro"]["versionID"]
    print(f"Base {detected_distrib_id}:{detected_version_id} found for {image_ref}")
    return detected_distrib_id, detected_version_id


def extract_base_image(instructionsliste, stage_id):
    """Find the FROM instruction that starts the given stage and return the
    (distribution, version) it is built from"""

    # Find the line containing the FROM of the stage the packages come from
    for entry in instructionsliste:
        if entry.instruction_id == stage_id:
            instruction_entry = entry.instruction_text
        else:
            continue

    # Extract image
    image_match = re.search(
        r"^FROM\s+(?P<image>[a-zA-Z0-9].+?)(?:\s+AS\s+.*)?$",
        instruction_entry)
    if image_match:
        image_ref = image_match.group('image')
    else:
        return None

    # Create group in regex for extract source and version(if exist)
    group_source_version_match = re.search(
        r"^(?P<source>[a-zA-Z0-9].+?)(:(?P<version>.+))?$",
        image_ref)
    if not group_source_version_match:
        return None

    # Define version
    if group_source_version_match.group('version'):
        base_image_version = group_source_version_match.group('version')
        # Search if version is in plain text or variable with default
        # And if is variable, search it's reference and if not exist use deflaut
        arg_reference_match = re.search(
            r"^\${(?P<variable>.+?)(:-(?P<default>.+))?}$",
            base_image_version)
        if arg_reference_match:
            base_image_version = resolve_arg_variable_version(
                instructionsliste,
                arg_reference_match.group('variable')
                ) or arg_reference_match.group('default')
        # Remove @sha TAG in version
        digest_suffix_match = re.search(
            r"^(?P<version>[a-zA-Z0-9].+?)(?:@.+?)$",
            base_image_version)
        if digest_suffix_match:
            base_image_version = digest_suffix_match.group('version')
    else:
        base_image_version = "latest"

    # Define source
    base_image_name = group_source_version_match.group('source')
    # Search if source is a native supported by this soft
    # If not, search it's origine
    if base_image_name.upper() not in SupportedDistribution.listkeys():
        detected = inspect_unknown_base_image(base_image_name, base_image_version)
        base_image_name = detected[0]
        base_image_version = detected[1]

    return base_image_name, base_image_version


def extract_package_manager_and_packages(instruction_text):
    """Try each supported package manager's extractor against this instruction."""
    for pkg_manager_name in SupportedPackageManager.listkeys():
        package_module = importlib.import_module(f"packages.{pkg_manager_name.lower()}")
        found_packages = package_module.extract_pinned_packages(instruction_text)
        if found_packages:
            return pkg_manager_name.lower(), found_packages
    return None


def extract_dataset(instructionsliste):
    """Extract dataset for package and image in Dockerfile."""
    dataset = {}
    for package_manager in SupportedPackageManager.listkeys():
        dataset[package_manager.lower()] = []

    for entry in instructionsliste:
        if entry.command.upper() != "RUN":
            continue

        instruction_text = entry.instruction_text
        stage_id = entry.stage_infos["StageStartAtID"]

        # Extract Packages
        detected_packages = extract_package_manager_and_packages(instruction_text)

        # Extract Distribution and version
        if detected_packages:
            base_image_info = extract_base_image(instructionsliste, stage_id)

            # # Save all this data in dict
            stage_entry_infos = [base_image_info[0], base_image_info[1], detected_packages[1], entry.command, entry.start_line]
            dataset[detected_packages[0]].append(stage_entry_infos)

    return dataset
