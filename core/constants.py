"""
Module containing constants for the project.
"""
from enum import Enum


class Permissions(Enum):
    ADMIN = 'admin'
    CREATE = 'add'
    EDIT = 'change'
    DELETE = 'delete'
    VIEW = 'view'
    PROTECTED = 'protected'


class Groups(Enum):
    DATA_STEWARD = 'daisy-data-steward'
    VIP = 'daisy-vip'
    AUDITOR = 'daisy-auditors'
    LEGAL = 'daisy-legal'
