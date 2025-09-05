import logging
from django.conf import settings
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from core.models import Dataset, Project, User, Contract, DAC
from core.search_indexes import DatasetIndex, ProjectIndex, ContractIndex, DACIndex

logger = logging.getLogger("daisy.signals")


@receiver(
    m2m_changed,
    sender=Dataset.local_custodians.through,
    dispatch_uid="dataset_local_custodians_changed",
)
def dataset_local_custodians_changed(sender, instance, action, pk_set, **kwargs):
    """
    Dataset m2m changed
    * Change custodians permissions
    * Index dataset
    """
    if action == "post_add":
        added_custodians_ids = pk_set
        added_custodians = User.objects.filter(pk__in=added_custodians_ids)
        logger.debug(
            f'[dataset_local_custodians_changed] action: {action} on "{instance}". Adding custodians: {pk_set} .'
        )
        for custodian in added_custodians:
            custodian.assign_permissions_to_dataset(instance)
    elif action == "post_remove":
        removed_custodians_ids = pk_set
        removed_custodians = User.objects.filter(pk__in=removed_custodians_ids)
        logger.debug(
            f'[dataset_local_custodians_changed] action: {action} on "{instance}". Removing custodians: {pk_set} .'
        )
        for custodian in removed_custodians:
            custodian.remove_permissions_to_dataset(instance)
    DatasetIndex().update_object(instance)


@receiver(
    m2m_changed,
    sender=Contract.local_custodians.through,
    dispatch_uid="contract_local_custodians_changed",
)
def contract_local_custodians_changed(sender, instance, action, pk_set, **kwargs):
    """
    Dataset m2m changed
    * Change custodians permissions
    * Index dataset
    """
    if action == "post_add":
        added_custodians_ids = pk_set
        added_custodians = User.objects.filter(pk__in=added_custodians_ids)
        for custodian in added_custodians:
            custodian.assign_permissions_to_contract(instance)
    elif action == "post_remove":
        removed_custodians_ids = pk_set
        removed_custodians = User.objects.filter(pk__in=removed_custodians_ids)
        for custodian in removed_custodians:
            custodian.remove_permissions_to_contract(instance)
    ContractIndex().update_object(instance)


@receiver(
    m2m_changed,
    sender=Project.local_custodians.through,
    dispatch_uid="project_local_custodians_changed",
)
def project_local_custodians_changed(sender, **kwargs):
    """
    Project m2m changed
    * Change custodians permissions
    * Index project
    """
    instance = kwargs.get("instance")
    action = kwargs.get("action")
    pk_set = kwargs.get("pk_set")

    if action == "post_add":
        added_custodians_ids = pk_set
        added_custodians = User.objects.filter(pk__in=added_custodians_ids)
        for custodian in added_custodians:
            custodian.assign_permissions_to_project(instance)
    elif action == "post_remove":
        removed_custodians_ids = pk_set
        removed_custodians = User.objects.filter(pk__in=removed_custodians_ids)
        for custodian in removed_custodians:
            custodian.remove_permissions_to_project(instance)
    ProjectIndex().update_object(instance)


@receiver(
    m2m_changed,
    sender=DAC.local_custodians.through,
    dispatch_uid="dac_local_custodians_changed",
)
def dac_local_custodians_changed(sender, instance, action, pk_set, **kwargs):
    """
    DAC m2m changed
    * Change custodians permissions
    * Index DAC
    """
    if action == "post_add":
        added_custodians_ids = pk_set
        added_custodians = User.objects.filter(pk__in=added_custodians_ids)
        for custodian in added_custodians:
            custodian.assign_permissions_to_dac(instance)
    elif action == "post_remove":
        removed_custodians_ids = pk_set
        removed_custodians = User.objects.filter(pk__in=removed_custodians_ids)
        for custodian in removed_custodians:
            custodian.remove_permissions_to_dac(instance)
    DACIndex().update_object(instance)
