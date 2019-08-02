import datetime
from django.core.management import BaseCommand
from django.db.models import Q
from django.utils import timezone
from notification.models import Notification, NotificationVerb
from core.models import DataDeclaration, Document, Contract, Project


class Command(BaseCommand):

    help = 'generate periodic notifications'

    @staticmethod
    def data_storage_expiry_notifications():
        now = timezone.now()

        # the user will receive notifications on two consecutive days prior to storage end date
        window_2_start = now + datetime.timedelta(days=1)
        window_2_end = now + datetime.timedelta(days=2)

        # the user will receive notifications on two consecutive days, two months prior to storage end date
        window_60_start = now + datetime.timedelta(days=59)
        window_60_end = now + datetime.timedelta(days=60)

        data_declarations = DataDeclaration.objects.filter(Q(end_of_storage_duration__gte=window_60_start, end_of_storage_duration__lte=window_60_end) | Q(end_of_storage_duration__gte=window_2_start, end_of_storage_duration__lte=window_2_end)).order_by('end_of_storage_duration')

        for ddec in data_declarations:
            for custodian in ddec.dataset.local_custodians.all():
                Notification.objects.create(
                    actor=custodian,
                    verb=NotificationVerb.data_storage_expiry,
                    content_object=ddec,
                )

    @staticmethod
    def document_expiry_notifications():
        now = timezone.now()

        # the user will receive notifications on two consecutive days prior to storage end date
        window_2_start = now + datetime.timedelta(days=1)
        window_2_end = now + datetime.timedelta(days=2)

        # the user will receive notifications on two consecutive days, two months prior to storage end date
        window_60_start = now + datetime.timedelta(days=59)
        window_60_end = now + datetime.timedelta(days=60)

        documents = Document.objects.filter(Q(expiry_date__gte=window_60_start, expiry_date__lte=window_60_end) | Q(expiry_date__gte=window_2_start, expiry_date__lte=window_2_end)).order_by('expiry_date')

        for document in documents:
            print(document.content_type)
            if str(document.content_type) == 'project':
                obj = Project.objects.get(pk=document.object_id)
            if str(document.content_type) == 'contract':
                print('Contract found')
                obj = Contract.objects.get(pk=document.object_id)
            if obj:
                for custodian in obj.local_custodians.all():
                    Notification.objects.create(
                        actor=custodian,
                        verb=NotificationVerb.document_expiry,
                        content_object=obj,
                    )
    def handle(self, *args, **options):
        self.data_storage_expiry_notifications()
        self.document_expiry_notifications()
        print('notifications generated')