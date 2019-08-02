import datetime
from django.core.management import BaseCommand
from django.db.models import Q
from django.utils import timezone
from notification.models import Notification, NotificationVerb
from core.models import DataDeclaration


class Command(BaseCommand):

    help = 'generate periodic notifications'

    @staticmethod
    def data_storage_expiry_notifications():
        now = timezone.now()

        # the user will receive notifications on two consecutive days prior to storage end date
        window_7_start = now + datetime.timedelta(days=1)
        window_7_end = now + datetime.timedelta(days=2)

        # the user will receive notifications on two consecutive days, two months prior to storage end date
        window_30_start = now + datetime.timedelta(days=59)
        window_30_end = now + datetime.timedelta(days=60)

        data_declarations = DataDeclaration.objects.filter(Q(end_of_storage_duration__gte=window_30_start, end_of_storage_duration__lte=window_30_end) | Q(end_of_storage_duration__gte=window_7_start, end_of_storage_duration__lte=window_7_end)).order_by('end_of_storage_duration')

        for ddec in data_declarations:
            for custodian in ddec.dataset.local_custodians.all():
                Notification.objects.create(
                    actor=custodian,
                    verb=NotificationVerb.data_storage_expiry,
                    content_object=ddec,
                )

    def handle(self, *args, **options):
        self.data_storage_expiry_notifications()
        print('notifications generated')