"""
Module containing constants for the project.
"""

from enum import Enum


class Permissions(Enum):
    ADMIN = "admin"
    EDIT = "change"
    DELETE = "delete"
    PROTECTED = "protected"


class Groups(Enum):
    DATA_STEWARD = "daisy-data-steward"
    VIP = "daisy-vip"
    AUDITOR = "daisy-auditors"
    LEGAL = "daisy-legal"


class IdentityProvider(Enum):
    UL = ("ul", "University of Luxembourg")
    LIH = ("lih", "Luxembourg Institute of Health")
    LUMS = ("lums", "LCSB User Management System")
    LS = ("ls", "LifeScience Login (academic federation)")
    ORCID = ("orcid", "ORCID")

    def __init__(self, username_suffix, display_name):
        self.username_suffix = username_suffix
        self.display_name = display_name

    @classmethod
    def from_username_suffix(cls, username_suffix):
        for provider in cls:
            if provider.username_suffix == username_suffix.lower():
                return provider
        return None
