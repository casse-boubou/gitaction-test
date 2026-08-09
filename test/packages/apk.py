# apk.py - Fonctions available for apk packages
import re


def extract_packages(dockerline):
    """Find and extract apk packages installed in Dockerfile"""

    # Extract apk add packages
    pacvers = {}
    apk_match = re.search(
        r"apk\s+(?:--[a-zA-Z-_.\s]+\s+)*add\s+(?:--[a-zA-Z-_.\s]+\s+)*(?P<packages>[a-zA-Z0-9].+=.+?)(?:&&|;|$)",
        dockerline)
    if apk_match:
        for pac in apk_match.group('packages').split():
            pac_match = re.search(
                r"(?P<name>[a-zA-Z0-9].+)=(?P<version>[a-zA-Z0-9].+)",
                pac)
            pacvers[pac_match.group('name')] = pac_match.group('version')
    else:
        pacvers = None

    return pacvers
