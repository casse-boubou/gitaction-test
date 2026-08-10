# THANKS to @nawazdhandala https://oneuptime.com/blog/post/2026-02-08-how-to-parse-and-analyze-dockerfiles-programmatically/view
# extract_datas.py - Extract some datas from parsed Dockerfiles
import importlib
import json
import re
import subprocess
import os

from scripts.enum_class import SupportedPackages, SupportedSource


def search_variable_version(parsedcommands, variable):
    """Search for plain text of version number if she is in variable"""
    for j in parsedcommands:
        if j.cmd != "ARG":
            continue
        regextotest = f"^ARG\\s+{variable}=\"?(?P<version>.+?)\"?$"
        variable_match = re.search(regextotest, j.instructions)
        if variable_match:
            return variable_match.group('version')
    return None


def dig_into_image(source, version):
    """Search for base source of image"""
    image = f"{source}:{version}"
    # github_act_path = os.environ["GITHUB_ACTION_PATH"]
    github_path = os.environ["GITHUB_PATH"]
    print(f"222222222222222 {github_path}")
    print(f"222222222222222 ${GITHUB_PATH}")
    print(f"222222222222222 ${GITHUB_PATH}")
    syft_cmd = ("/usr/local/bin/syft", "scan", f"{image}", "--output", "template", "--template", f"{github_path}/src/scripts/schema-latest.go")
    print(f"Wait, searching for the base image of {image} in progress...")
    scan = subprocess.run(syft_cmd, capture_output=True, check=True, text=True)
    syftdata = json.loads(scan.stdout)
    syftdataid = syftdata["distro"]["id"]
    syftdataversionid = syftdata["distro"]["versionID"]
    print(f"Base {syftdataid}:{syftdataversionid} found for {image}")
    return syftdataid, syftdataversionid


def extract_all_distro(parsedcommands, stage_id):
    """Extract distribution available for desired packages in Dockerfile."""

    # Find the line containing the FROM of the stage the packages come from
    for line in parsedcommands:
        if line.uid == stage_id:
            instructionline = line.instructions
        else:
            continue

    # Extract image
    image_match = re.search(
        r"^FROM\s+(?P<image>[a-zA-Z0-9].+?)(?:\s+AS\s+.*)?$",
        instructionline)
    if image_match:
        image = image_match.group('image')
        # print(f"{image}")
        # alpine:${ALPINE_BASE_IMAGE_VERSION}
    else:
        return None

    # Create group in regex for extract source and version(if exist)
    group_by_match = re.search(
        r"^(?P<source>[a-zA-Z0-9].+?)(:(?P<version>.+))?$",
        image)
    if not group_by_match:
        return None

    # Define version
    if group_by_match.group('version'):
        version = group_by_match.group('version')
        # Search if version is in plain text or variable with default
        # And if is variable, search it's reference and if not exist use deflaut
        version_in_variable_match = re.search(
            r"^\${(?P<variable>.+?)(:-(?P<default>.+))?}$",
            version)
        if version_in_variable_match:
            version = search_variable_version(
                parsedcommands,
                version_in_variable_match.group('variable')
                ) or version_in_variable_match.group('default')
        # Remove @sha TAG in version
        tag_match = re.search(
            r"^(?P<version>[a-zA-Z0-9].+?)(?:@.+?)$",
            version)
        if tag_match:
            version = tag_match.group('version')
    else:
        version = "latest"

    # Define source
    source = group_by_match.group('source')
    # Search if source is a native supported by this soft
    # If not, search it's origine
    if source.upper() not in SupportedSource.listkeys():
        image = dig_into_image(source, version)
        source = image[0]
        version = image[1]

    return source, version


def extract_all_packages(command_text):
    """Extract all supported packages type installed in Dockerfile."""
    for pkg in SupportedPackages.listkeys():
        extractfunct = importlib.import_module(f"packages.{pkg.lower()}")
        pk = extractfunct.extract_packages(command_text)
        if pk:
            return pkg.lower(), pk
    return None


def extract_data(parsedcommands):
    """Extract data for package and image in Dockerfile."""
    data = {}
    for package in SupportedPackages.listkeys():
        data[package.lower()] = []

    for step in parsedcommands:
        if step.cmd.upper() != "RUN":
            continue

        command_text = step.instructions
        # print(command_text)
        # RUN echo "Installing base packages"      && apk --update --no-cache add      cargo=1.96.1-r0      git=2.54.0-r0
        stage_id = step.stage["StageStartAtID"]

        # Extract Packages
        packages = extract_all_packages(command_text)
        # print(packages)
        # ('apk', {'cargo': '1.96.1-r0', 'git': '2.54.0-r0'})

        # Extract Distribution and version
        if packages:
            distribution = extract_all_distro(parsedcommands, stage_id)
            # print({distribution})
            # {('alpine', '3.24@sha256:28bd5fe8b56.....')}

            # # Save all this data in dict
            stage_infos = [distribution[0], distribution[1], packages[1], step.cmd, step.startline]
            # print(stage_infos)
            # ['alpine', '3.24', {'cargo': '1.96.1-r0', 'git': '2.54.0-r0'}, 'RUN', 6]
            data[packages[0]].append(stage_infos)

    return data
