# apt.py - Extracts pinned APT package versions (name=version) from an
# `apt-get install ...` instruction found in a Dockerfile RUN line

import re


def extract_pinned_packages(instruction_text):
    """Return a {package_name: pinned_version} dict or None if no package found."""

    # Extract apt-get install packages
    pinned_versions = {}
    install_match = re.search(
        r"apt-get\s+(?:[a-zA-Z-_.\s]+\s+)*install\s+(?:[a-zA-Z-_.\s]+\s+)*(?P<packages>[a-zA-Z0-9].+=.+?)(?:&&|;|$)",
        instruction_text)
    if install_match:
        for pkg_token in install_match.group('packages').split():
            name_version_match = re.search(
                r"(?P<name>[a-zA-Z0-9].+)=(?P<version>[a-zA-Z0-9].+)",
                pkg_token)
            pinned_versions[name_version_match.group('name')] = name_version_match.group('version')
    else:
        pinned_versions = None

    return pinned_versions
