# enum_class.py - Define some Enum class here

from enum import Enum

class SuperEnum(Enum):
    """Parent class for define funct for other class"""
    @classmethod
    def to_dict(cls):
        """Returns a dictionary representation of the enum."""
        return {e.name: e.value for e in cls}

    @classmethod
    def listkeys(cls):
        """Returns a list of all the enum keys names."""
        return cls._member_names_

    @classmethod
    def listvalues(cls):
        """Returns a list of all the enum values."""
        return list(cls._value2member_map_.keys())

    @classmethod
    def search_key(cls, value):
        """Returns key name assigned to a value"""
        for i in cls:
            if i.value == value:
                return i.name
        return print(f"Sorry, no name key associated with value={value}")

    @classmethod
    def search_value(cls, name):
        """Returns value assigned to a key name"""
        for i in cls:
            if i.name == name.upper():
                return i.value
        return print(f"Sorry, no value associated with key name={name}")







class LatestSource(SuperEnum):
    """Class enumerat the image source supported by this soft"""
    ALPINE = 3.24
    UBUNTU = 26.04
    DEBIAN = 13


class SupportedSource(SuperEnum):
    """Class enumerat the image source supported by this soft"""
    ALPINE = 1
    UBUNTU = 2
    DEBIAN = 3


class SupportedPackages(SuperEnum):
    """Class enumerat the image source supported by this soft"""
    APK = 1
    APT = 2


class DockerCommand(SuperEnum):
    """Class representing the type of command in Dockerfile"""
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


class UbuntuRelease(SuperEnum):
    """Class associate name with version of Ubuntu"""
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


class DebianRelease(SuperEnum):
    """Class associate name with version of Debian"""
    BULLSEYE = 11
    BOOKWORM = 12
    TRIXIE = 13
