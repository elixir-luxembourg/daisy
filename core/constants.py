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
