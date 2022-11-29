from django.db import models
from django.conf import settings

from .utils import CoreTrackedModel, TextFieldWithInputWidget


class Cohort(CoreTrackedModel):
    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']


    class AppMeta:
        help_text = "Cohorts are studies that collect data and/or biosamples from a group of participants. " \
                    "Longitudinal, case-control, family studies are typical examples of cohorts."


    ethics_confirmation =  models.BooleanField(default=True, blank=False, null=False,
                                               verbose_name='Confirmation of Ethics Approval?',
                                   help_text='Is the existence of the study\'s ethics approval confirmed by the cohort owner.')

    ethics_notes = models.TextField(verbose_name='Ethics Approval notes',
                                 default='',
                                 help_text='Provide notes on ethics approval. If it does not exist, please state justifications here.',
                                 blank=True,
                                 null=True)

    cohort_web_page = models.URLField(verbose_name='Cohort''s URL page',
                                       help_text='If the cohort has a webpage, please provide its URL link here.',
                                       blank=True)

    comments = models.TextField(verbose_name='Comments', blank=True, null=True,
                                help_text='Any additional remarks on this cohort.')

    owners = models.ManyToManyField('core.Contact',
                                       verbose_name='Cohort owner(s)',
                                       help_text='Cohort owners are typically clinicians that supervise the recruitment of subjects. They have access to subjects\' identities and deal with subject\'s requests.',
                                       blank=False)

    title = TextFieldWithInputWidget(blank=False, null=False,
                                     max_length=255,
                                     verbose_name='Title',
                                     help_text='The name with which this cohort is commonly known.',
                                     unique=True)

    institutes = models.ManyToManyField('core.Partner',
                                        verbose_name='Institutes',
                                        help_text='The partner institutes involved in the running of this cohort study.',
                                        blank=True)

    def __str__(self):
        return self.title

    def to_dict(self):
        owners_dicts = []
        for owner in self.owners.all():
            owners_dicts.append(owner.to_dict())
                
        base_dict = {
            "source": settings.SERVER_URL,
            "id_at_source": self.id.__str__(),
            "external_id": self.elu_accession,
            'name': self.title,
            'description': self.comments,
            'url': self.cohort_web_page,
            'contacts': owners_dicts,
            'institutes': [i.id for i in self.institutes.all()],
            'has_ethics_approval': self.ethics_confirmation,
            'ethics_approval_notes': self.ethics_notes,
            "metadata": self.scientific_metadata
        }
        return base_dict

    def serialize_to_export(self):
        import functools

        d = self.to_dict()

        owners = map(lambda v: f"[{v['first_name']} {v['last_name']}, {v['email']}]", d['owners'])
        d['owners'] = ','.join(owners)

        institutes = map(lambda v: f"[{v.to_dict()['name']}]", self.institutes.all())
        d['institutes'] = ','.join(institutes)

        return d
