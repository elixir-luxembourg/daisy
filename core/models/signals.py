from django.conf import settings
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from core.models import Dataset, Project, User, Contract
from core.search_indexes import DatasetIndex, ProjectIndex, ContractIndex
from notification.models import Notification, NotificationVerb, NotificationStyle


@receiver(post_save, sender=Dataset, dispatch_uid='dataset_change')
def dataset_changed(sender, instance, created, **kwargs):
    """
    Dataset changed
    * create a notification
    """
    from notification import tasks
    # log an activity for each custodians
    for custodian in instance.local_custodians.all():
        Notification.objects.create(
            actor=custodian,
            verb=created and NotificationVerb.new_dataset or NotificationVerb.update_dataset,
            content_object=instance,
        )
        # send an email if notif setting is every time
        if not settings.NOTIFICATIONS_DISABLED and (not hasattr(custodian,
                                                                'notification_setting') or custodian.notification_setting == NotificationStyle.every_time):
            tasks.send_dataset_notification_for_user.delay(custodian.pk, instance.pk, created)


@receiver(m2m_changed, sender=Dataset.local_custodians.through, dispatch_uid='dataset_local_custodians_changed')
def dataset_local_custodians_changed(sender, instance, action, pk_set, **kwargs):
    """
    Dataset m2m changed
    * Change custodians permissions
    * Index dataset
    """
    if action == 'post_add':
        added_custodians_ids = pk_set
        added_custodians = User.objects.filter(pk__in=added_custodians_ids)
        for custodian in added_custodians:
            custodian.assign_permissions_to_dataset(instance)
    elif action == 'post_remove':
        removed_custodians_ids = pk_set
        removed_custodians = User.objects.filter(pk__in=removed_custodians_ids)
        for custodian in removed_custodians:
            custodian.remove_permissions_to_dataset(instance)
    DatasetIndex().update_object(instance)


@receiver(m2m_changed, sender=Contract.local_custodians.through,
          dispatch_uid='contract_local_custodians_changed')
def contract_local_custodians_changed(sender, instance, action, pk_set, **kwargs):
    """
    Dataset m2m changed
    * Change custodians permissions
    * Index dataset
    """
    if action == 'post_add':
        added_custodians_ids = pk_set
        added_custodians = User.objects.filter(pk__in=added_custodians_ids)
        for custodian in added_custodians:
            custodian.assign_permissions_to_contract(instance)
    elif action == 'post_remove':
        removed_custodians_ids = pk_set
        removed_custodians = User.objects.filter(pk__in=removed_custodians_ids)
        for custodian in removed_custodians:
            custodian.remove_permissions_to_contract(instance)
    ContractIndex().update_object(instance)


@receiver(m2m_changed, sender=Project.local_custodians.through, dispatch_uid='project_local_custodians_changed')
def project_local_custodians_changed(sender, **kwargs):
    """
    Project m2m changed
    * Change custodians permissions
    * Index project
    """
    instance = kwargs.get('instance')
    action = kwargs.get('action')
    pk_set = kwargs.get('pk_set')

    if action == 'post_add':
        added_custodians_ids = pk_set
        added_custodians = User.objects.filter(pk__in=added_custodians_ids)
        for custodian in added_custodians:
            custodian.assign_permissions_to_project(instance)
    elif action == 'post_remove':
        removed_custodians_ids = pk_set
        removed_custodians = User.objects.filter(pk__in=removed_custodians_ids)
        for custodian in removed_custodians:
            custodian.remove_permissions_to_project(instance)
    ProjectIndex().update_object(instance)

# @receiver(post_save, sender=Project, dispatch_uid='project_saved')
# def project_saved(sender, instance, created, **kwargs):
#     print('project saved')
#     if created:
#         for user in instance.local_custodians.all():
#             user.assign_permissions_to_project(instance)
