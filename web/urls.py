from django.urls import path

from web.views import contracts, datasets, permissions, api, profile, documents, projects, storage_locations, \
    share, notifications, data_declarations, access, legalbasis
from web.views.access import AccessCreateView, AccessDetailView
from web.views.cohorts import CohortCreateView, CohortEditView, \
    CohortDetailView, cohort_list
from web.views.contact import ContactCreateView, ContactDetailView, add_contact_to_project, \
    remove_contact_from_project, ContactEditView, pick_contact_for_project, contact_search_view
from web.views.contracts import ContractCreateView, ContractEditView, \
    ContractDetailView, contract_list
from web.views.dashboard import dashboard
from web.views.data_declarations import DatadeclarationDetailView, DatadeclarationEditView
from web.views.datasets import DatasetDetailView, DatasetEditView, dataset_list, \
    DatasetCreateView
from web.views.partner import PartnerCreateView, partner_search_view, PartnerDetailView, PartnerEditView, publish_partner
from web.views.projects import ProjectCreateView, ProjectEditView, ProjectDetailView
from web.views.publication import PublicationCreateView, PublicationListView, PublicationEditView, \
    add_publication_to_project, remove_publication_from_project, pick_publication_for_project
from web.views.storage_locations import StorageLocationListView, StorageLocationEditView, \
    StorageLocationDetailView, StorageLocationCreateView, remove_storage_location_from_dataset, \
    pick_storage_location_for_dataset, add_storage_location_to_dataset
from web.views.users import add_personnel_to_project, remove_personnel_from_project

# Use include() to add paths from the catalog application


web_urls = [
    path('', dashboard, name='dashboard'),

    path('profile', profile.ProfileEditView.as_view(), name='profile'),

    path('definitions/cohorts/', cohort_list, name="cohorts"),
    path('definitions/cohorts/add', CohortCreateView.as_view(), name='cohort_add'),
    path('definitions/cohorts/<int:pk>/edit', CohortEditView.as_view(), name="cohort_edit"),
    path('definitions/cohorts/<int:pk>/', CohortDetailView.as_view(), name="cohort"),

    path('contracts/', contract_list, name="contracts"),

    path('contracts/add/', ContractCreateView.as_view(), name='contract_add'),
    path('contracts/<int:pk>/edit', ContractEditView.as_view(), name="contract_edit"),
    path('contracts/<int:pk>/', ContractDetailView.as_view(), name="contract"),
    path('contracts/<int:pk>/add-partner-role', contracts.PartnerRoleCreateView.as_view(), name="add_partner_role_to_contract"),
    path('partner_role/<int:pk>/delete', contracts.partner_role_delete, name="delete_partner_role"),



    # path('definitions/contacts', ContactListView.as_view(), name='contacts'),
    path('definitions/contact/<int:pk>', ContactDetailView.as_view(), name='contact'),
    path('definitions/contact/<int:pk>/edit', ContactEditView.as_view(), name='contact_edit'),
    path('definitions/contacts/add/', ContactCreateView.as_view(), name='contact_add'),
    path('definitions/contacts', contact_search_view, name='contacts'),


    path('storage_locations', StorageLocationListView.as_view(), name='storage_locations'),
    path('storage_location/<int:pk>', StorageLocationDetailView.as_view(), name='storage_location'),
    path('storage_location/<int:pk>/edit', StorageLocationEditView.as_view(), name='storage_location_edit'),
    path('storage_location/add/', StorageLocationCreateView.as_view(), name='storage_location_add'),

    path('dataset/<int:pk>/add-data-declaration', data_declarations.data_declarations_add,
         name='data_declarations_add'),
    path('data_declaration/<int:pk>/duplicate', data_declarations.data_declarations_duplicate,
         name='data_declarations_duplicate'),
    path('data_declaration/<int:pk>/delete', data_declarations.data_declarations_delete,
         name='data_declarations_delete'),
    path('data_declaration/<int:pk>/', DatadeclarationDetailView.as_view(), name="data_declaration"),
    path('data_declaration/<int:pk>/edit', DatadeclarationEditView.as_view(), name="data_declaration_edit"),
    path('data-declaration-sub-form', data_declarations.data_declarations_add_sub_form,
         name='data_declarations_add_sub_form'),
    path('data-declarations-get-contracts', data_declarations.data_declarations_get_contracts,
         name="data_declarations_get_contracts"),


    #TODO merge the two search views into one
    path('data-declarations-autocomplete', data_declarations.data_declarations_autocomplete,
         name="data_declarations_autocomplete"),
    path('data-dec-paginated-search', data_declarations.data_dec_paginated_search,
         name="data_dec_paginated_search"),

    path('datasets/add/', DatasetCreateView.as_view(), name='dataset_add'),
    path('datasets/', dataset_list, name="datasets"),
    path('dataset/<int:pk>/', DatasetDetailView.as_view(), name="dataset"),
    path('dataset/<int:pk>/edit', DatasetEditView.as_view(), name="dataset_edit"),
    path('dataset/<int:pk>/add-datafile', add_storage_location_to_dataset, name="add_storage_location_to_dataset"),
    path('dataset/<int:pk>/pick-datafile', pick_storage_location_for_dataset, name="pick_storage_location_for_dataset"),
    path('dataset/<int:pk>/del-datafile/<int:storage_location_id>', remove_storage_location_from_dataset,
         name="remove_storage_location_from_dataset"),


    # dataset's data location methods
    path('datalocation/<int:pk>', storage_locations.DataLocationDetailView.as_view(), name='datalocation'),
    path('dataset/<int:pk>/datalocation/add/', storage_locations.DataLocationCreateView.as_view(),
         name='datalocation_add'),
    path('dataset/<int:dataset_pk>/data/remove/<int:data_pk>/', storage_locations.datalocation_remove,
         name='datalocation_remove'),

    # (INTERNAL) ACCESSES
    path('access/<int:pk>', AccessDetailView.as_view(), name='access'),
    path('dataset/<int:dataset_pk>/access/add/', AccessCreateView.as_view(), name='access_add'),
    path('dataset/<int:dataset_pk>/access/remove/<int:access_pk>/', access.remove_access, name='access_remove'),


    # LEGAL BASIS
    path('dataset/<int:dataset_pk>/legalbasis/add/', legalbasis.LegalBasisCreateView.as_view(), name='dataset_legalbasis_add'),
    path('dataset/<int:dataset_pk>/legalbasis/remove/<int:legalbasis_pk>/', legalbasis.remove_legalbasis, name='dataset_legalbasis_remove'),
    path('dataset/<int:dataset_pk>/legalbasis/<int:pk>/edit', legalbasis.edit_legalbasis, name="dataset_legalbasis_edit"),


    # (EXTERNAL) SHARES
    path('dataset/<int:dataset_pk>/share/add/', share.ShareCreateView.as_view(), name='dataset_share_add'),
    path('dataset/<int:dataset_pk>/share/remove/<int:share_pk>/', share.remove_share, name='dataset_share_remove'),
    path('dataset/<int:dataset_pk>/share/<int:pk>/edit', share.edit_share, name="dataset_share_edit"),



    path('documents/<int:object_id>/<int:content_type>/add', documents.upload_document,  name='document_add'),
    path('documents/<int:pk>/edit/', documents.document_edit, name='document_edit'),
    path('documents/<int:pk>/download', documents.download_document, name='document_download'),
    path('documents/<int:pk>/delete', documents.delete_document, name='document_delete'),


    path('definitions/partners/<int:pk>/edit/', PartnerEditView.as_view(), name='partner_edit'),
    path('definitions/partners/<int:pk>/', PartnerDetailView.as_view(), name="partner"),
    path('definitions/partners', partner_search_view, name='partners'),
    path('definitions/partners/add/', PartnerCreateView.as_view(), name='partner_add'),
    path('definitions/partners/<int:pk>/publish_partner/', publish_partner, name='publish_partner'),

    path('permissions/', permissions.index, name="permissions"),
    path('permissions/project/<int:pk>/', permissions.index, {'selection': 'project'}, name="permission_project"),
    path('permissions/dataset/<int:pk>/', permissions.index, {'selection': 'dataset'}, name="permission_dataset"),

    path('notifications/', notifications.index, name="notifications"),
    path('notifications/admin', notifications.admin, name="notifications_admin"),
    path('notifications/admin/<int:pk>', notifications.admin, name="notifications_admin_for_user"),

    path('projects/', projects.project_list, name="projects"),
    path('projects/add/', ProjectCreateView.as_view(), name='project_add'),
    path('project/<int:pk>/edit', ProjectEditView.as_view(), name="project_edit"),
    path('project/<int:pk>/', ProjectDetailView.as_view(), name="project"),
    path('project/<int:pk>/add-personnel', add_personnel_to_project, name="add_personnel_to_project"),
    path('project/<int:pk>/add-dataset', datasets.DatasetCreateView.as_view(), name="datasets_add_to_project"),
    path('project/<int:pk>/del-personnel/<int:user_id>', remove_personnel_from_project,
         name="remove_personnel_from_project"),
    path('project/<int:pk>/del-contact/<int:contact_id>', remove_contact_from_project,
         name="remove_contact_from_project"),
    path('project/<int:pk>/add-contact', add_contact_to_project, name="add_contact_to_project"),
    path('project/<int:pk>/pick-contact', pick_contact_for_project, name="pick_contact_for_project"),
    path('project/<int:pk>/add-publication', add_publication_to_project, name="add_publication_to_project"),
    path('project/<int:pk>/pick-publication', pick_publication_for_project, name="pick_publication_for_project"),
    path('project/<int:pk>/del-publication/<int:publication_id>', remove_publication_from_project,
         name="remove_publication_from_project"),

    # project's dataset methods
    path('project/<int:pk>/dataset/create', projects.project_dataset_choose_type, name="project_dataset_choose_type"),
    path('project/<int:pk>/dataset/<int:flag>/create', projects.project_dataset_create, name="project_dataset_create"),
    path('project/<int:pk>/dataset/add', projects.project_dataset_add, name="project_dataset_add"),

    # project's contract methods
    path('project/<int:pk>/contract/create', projects.project_contract_create,
         name="project_contract_create"),
    path('project/<int:pk>/contract/remove/<int:cid>', projects.project_contract_remove,
         name="project_contract_remove"),

    # publications methods
    path('publications/', PublicationListView.as_view(), name="publications"),
    path('publications/add/', PublicationCreateView.as_view(), name='publication_add'),
    path('publications/<int:pk>/edit', PublicationEditView.as_view(), name='publication_edit'),

    # api urls
    path('api/users', api.users, name="api_users"),
    path('api/cohorts', api.cohorts, name="api_cohorts"),
    path('api/partners', api.partners, name="api_partners"),
    path('api/termsearch/<slug:category>', api.termsearch, name="api_termsearch")
]
