# apt.py - Fonctions available for apt packages
import re


def extract_packages(dockerline):
    """Find and extract apt packages installed in Dockerfile"""

    # Extract apt-get install packages
    pacvers = {}
    apt_match = re.search(
        r"apt-get\s+(?:[a-zA-Z-_.\s]+\s+)*install\s+(?:[a-zA-Z-_.\s]+\s+)*(?P<packages>[a-zA-Z0-9].+=.+?)(?:&&|;|$)",
        dockerline)
    if apt_match:
        for pac in apt_match.group('packages').split():
            pac_match = re.search(
                r"(?P<name>[a-zA-Z0-9].+)=(?P<version>[a-zA-Z0-9].+)",
                pac)
            pacvers[pac_match.group('name')] = pac_match.group('version')
    else:
        pacvers = None

    return pacvers
