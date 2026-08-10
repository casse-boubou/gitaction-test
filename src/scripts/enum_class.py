# enum_class.py - Base Enum class with generic lookup helpers

from enum import Enum


class LookupEnum(Enum):
    """Parent class providing shared helper methods reused by every enum below."""
    @classmethod
    def as_dict(cls):
        """Returns a dictionary representation of the enum."""
        return {e.name: e.value for e in cls}

    @classmethod
    def listkeys(cls):
        """Returns a list of all the enum member names."""
        return cls._member_names_

    @classmethod
    def listvalues(cls):
        """Returns a list of all the enum member values."""
        return list(cls._value2member_map_.keys())

    @classmethod
    def name_for_value(cls, value):
        """Returns the member name matching the given value."""
        for i in cls:
            if i.value == value:
                return i.name
        return print(f"Sorry, no name key associated with value={value}")

    @classmethod
    def value_for_name(cls, name):
        """Returns the value of the member matching the given name."""
        for i in cls:
            if i.name == name.upper():
                return i.value
        return print(f"Sorry, no value associated with key name={name}")







class LatestDistribVersion(LookupEnum):
    """Version to use for each distribution when the Dockerfile requests the 'latest' tag."""
    ALPINE = 3.24
    UBUNTU = 26.04
    DEBIAN = 13


class SupportedDistribution(LookupEnum):
    """Distributions natively handled by this tool."""
    ALPINE = 1
    UBUNTU = 2
    DEBIAN = 3


class SupportedPackageManager(LookupEnum):
    """Package managers natively handled by this tool."""
    APK = 1
    APT = 2


class DockerCommand(LookupEnum):
    """Every Dockerfile instruction keyword recognized by the parser."""
    ADD = 1
    ARG = 2
    CMD = 3
    COPY = 4
    ENTRYPOINT = 5
    ENV = 6
    EXPOSE = 7
    FROM = 8
    HEALTHCHECK = 9
    LABEL = 10
    MAINTAINER = 11
    ONBUILD = 12
    RUN = 13
    SHELL = 14
    STOPSIGNAL = 15
    USER = 16
    VOLUME = 17
    WORKDIR = 18


class UbuntuCodename(LookupEnum):
    """Maps each Ubuntu release number to its codename (e.g. 24.04 -> NOBLE)."""
    BIONIC = 18.04
    COSMIC = 18.10
    DISCO = 19.04
    EOAN = 19.10
    FOCAL = 20.04
    GROOVY = 20.10
    HIRSUTE = 21.04
    IMPISH = 21.10
    JAMMY = 22.04
    KINETIC = 22.10
    LUNAR = 23.04
    MANTIC = 23.10
    NOBLE = 24.04
    ORACULAR = 24.10
    PLUCKY = 25.04
    QUESTING = 25.10
    RESOLUTE = 26.04
    STONKING = 26.10


class DebianCodename(LookupEnum):
    """Maps each Debian major version to its codename (e.g. 12 -> BOOKWORM)."""
    BULLSEYE = 11
    BOOKWORM = 12
    TRIXIE = 13
