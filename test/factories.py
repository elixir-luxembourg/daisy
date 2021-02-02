# configure factories from https://factoryboy.readthedocs.io
import factory
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType

from core.constants import Groups as GroupConstants
from core.models import User, Dataset
from core.models.data_declaration import DeidentificationMethod, SubjectCategory, ShareCategory, ConsentStatus
from core.models.partner import GEO_CATEGORY
from notification.models import NotificationVerb


class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Group
        django_get_or_create = ('name',)

    name = factory.Iterator([g.value for g in GroupConstants])


class VIPGroup(GroupFactory):
    name = GroupConstants.VIP.value


class DataStewardGroup(GroupFactory):
    name = GroupConstants.DATA_STEWARD.value


class LegalGroup(GroupFactory):
    name = GroupConstants.LEGAL.value


class AuditorGroup(GroupFactory):
    name = GroupConstants.AUDITOR.value


class UserFactory(factory.django.DjangoModelFactory):
    """
    User factory
    """

    class Meta:
        model = 'core.User'
        django_get_or_create = ('username',)

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    last_name = factory.Faker('email')
    full_name = factory.LazyAttribute(lambda x: f'{x.first_name}.{x.last_name}'.lower())
    username = factory.LazyAttribute(lambda x: f'{x.first_name}.{x.last_name}@uni.lux'.lower())

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for group in extracted:
                self.groups.add(group)




class ProjectFactory(factory.django.DjangoModelFactory):
    """
    Project factory
    TODO: add members, custodians, contacts, publications
    """

    class Meta:
        model = 'core.Project'
        django_get_or_create = ('acronym',)

    acronym = factory.Faker('company')
    title = factory.Faker('company')
    description = factory.Faker('catch_phrase')
    has_cner = factory.Iterator([True, False])
    has_erp = factory.Iterator([True, False])
    cner_notes = factory.Iterator([True, False])

    @factory.post_generation
    def local_custodians(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of users were passed in, use them
            for user in extracted:
                self.local_custodians.add(user)


class DataDeclarationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'core.DataDeclaration'
        django_get_or_create = ('title',)

    title = factory.Faker('bs')
    has_special_subjects = factory.Iterator([True, False])
    submission_id = factory.Faker('ean13')
    deidentification_method = factory.Iterator(DeidentificationMethod)
    subjects_category = factory.Iterator(SubjectCategory)
    special_subjects_description = factory.Faker('text')
    share_category = factory.Iterator(ShareCategory)
    consent_status = factory.Iterator(ConsentStatus)


class CohortFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'core.Cohort'
        django_get_or_create = ('title',)

    owners = factory.Faker('city')
    comments = factory.Faker('text')


class DatasetFactory(factory.django.DjangoModelFactory):
    """
    Dataset factory
    #TODO: add data_files, local_custodians, use_restrictions, datatypes, contracts?
    """

    class Meta:
        model = 'core.Dataset'
        django_get_or_create = ('title',)

    title = factory.Faker('bs')
    other_external_id = factory.Faker('ean8')

    @factory.post_generation
    def local_custodians(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of users were passed in, use them
            for user in extracted:
                self.local_custodians.add(user)


class ContactTypeFactory(factory.DjangoModelFactory):
    """
    ContactType factory
    """

    class Meta:
        model = 'core.ContactType'
        django_get_or_create = ('name',)

    name = factory.Faker('job')


class ContactFactory(factory.DjangoModelFactory):
    """
    Contact factory
    """

    class Meta:
        model = 'core.Contact'
        django_get_or_create = ('email',)

    address = factory.Faker('address')
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    phone = factory.Sequence(lambda n: '123-555-%04d' % n)
    type = factory.SubFactory(ContactTypeFactory)


class PartnerFactory(factory.DjangoModelFactory):
    """
    Partner factory
    """

    class Meta:
        model = 'core.Partner'
        django_get_or_create = ('elu_accession',)

    acronym = factory.Faker('company_suffix')
    address = factory.Faker('address')
    elu_accession = factory.Faker('company_suffix')
    geo_category = factory.Iterator([GEO_CATEGORY.EU, GEO_CATEGORY.Non_EU])
    name = factory.Faker('company')


class GDPRRoleFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'core.GDPRRole'

    display_name = factory.Iterator(["Joint Controller", "Controller", "Processor"])
    name = factory.Iterator(["joint_controller", "controller", "processor"])


class ContractFactory(factory.DjangoModelFactory):
    """
    Collaboration factory
    """

    class Meta:
        model = 'core.Contract'

    company_roles = factory.SubFactory(GDPRRoleFactory)
    project = factory.SubFactory(ProjectFactory)

    @factory.post_generation
    def local_custodians(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of users were passed in, use them
            for user in extracted:
                self.local_custodians.add(user)

    @factory.post_generation
    def partners_roles(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of users were passed in, use them
            for partner_roles in extracted:
                self.partners_roles.add(partner_roles)

    @factory.post_generation
    def company_roles(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for company_role in extracted:
                self.company_roles.add(company_role)
                
## NOTIFICATIONS
class AbstractNotificationFactory(factory.django.DjangoModelFactory):
    """
    Abstract class for notification factories
    """

    class Meta:
        exclude = ['content_object']
        abstract = True

    actor = factory.Iterator(User.objects.all())
    verb = factory.Iterator(NotificationVerb)

    object_id = factory.SelfAttribute('content_object.id')
    content_type = factory.LazyAttribute(lambda o: ContentType.objects.get_for_model(o.content_object))

    time = factory.Faker('date_time_this_month', tzinfo=settings.TZINFO)


class DatasetNotificationFactory(AbstractNotificationFactory):
    """
    Add notification for Dataset
    """

    class Meta:
        model = 'notification.Notification'
        django_get_or_create = ('actor', 'verb', 'time',)

    # content_object = factory.SubFactory(DatasetFactory)
    content_object = factory.Iterator(Dataset.objects.all())


## Documents
class AbstractDocumentFactory(factory.django.DjangoModelFactory):
    """
    Abstract class for document factories
    """

    class Meta:
        exclude = ['content_object']
        abstract = True

    content = 'Some content'
    object_id = factory.SelfAttribute('content_object.id')
    content_type = factory.LazyAttribute(lambda o: ContentType.objects.get_for_model(o.content_object))


class DatasetDocumentFactory(AbstractDocumentFactory):
    """
    Add notification for Dataset
    """

    class Meta:
        model = 'core.Document'

    content_object = factory.SubFactory(DatasetFactory)


class ContractDocumentFactory(AbstractDocumentFactory):
    """
    Add notification for Dataset
    """

    class Meta:
        model = 'core.Document'

    content_object = factory.SubFactory(ContractFactory)
