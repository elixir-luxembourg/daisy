from django.urls import path

from web.views import access, api, contracts, data_declarations, datasets, \
                      documents, legalbasis, notifications, permissions, \
                      profile, projects, share, storage_locations
from web.views.access import AccessCreateView
from web.views.about import about
from web.views.cohorts import CohortCreateView, CohortEditView, \
                              CohortDelete, CohortDetailView, cohort_list, \
                              publish_cohort, unpublish_cohort
from web.views.contact import ContactCreateView, ContactDetailView, \
                              ContactEditView, ContactDelete, \
                              add_contact_to_project, contact_search_view, \
                              pick_contact_for_project, remove_contact_from_project
from web.views.contracts import ContractCreateView, ContractEditView, \
                                ContractDelete, ContractDetailView, contract_list
from web.views.dashboard import dashboard
from web.views.data_declarations import DatadeclarationDetailView, DatadeclarationEditView
from web.views.datasets import DatasetCreateView, DatasetDetailView, DatasetEditView, DatasetDelete, \
                               dataset_list, publish_dataset, unpublish_dataset
from web.views.export import cohorts_export, contacts_export, contracts_export, \
                             datasets_export, partners_export, projects_export
from web.views.issues import issues
from web.views.partner import PartnerCreateView, PartnerDelete, PartnerDetailView, \
                              PartnerEditView, partner_search_view, \
                              publish_partner, unpublish_partner
from web.views.projects import ProjectCreateView, ProjectEditView, ProjectDetailView, \
                               ProjectDelete, publish_project, unpublish_project, dsw_list_projects
from web.views.publication import PublicationCreateView, PublicationListView, \
                                  PublicationEditView, add_publication_to_project, \
                                  remove_publication_from_project, pick_publication_for_project
from web.views.reporting import email_reports, email_reports_preview, \
                                email_reports_disable_for_user
from web.views.user import change_password, UserCreateView, UserDetailView, \
                           UserDelete, UserEditView, UsersListView, UserPasswordChange 
from web.views.users import add_personnel_to_project, remove_personnel_from_project


web_urls = [
    # Single pages
    path('', dashboard, name='dashboard'),
    path('about', about, name='about'),
    path('issues', issues, name='issues'),
    path('profile', profile.ProfileEditView.as_view(), name='profile'),

    # API urls
    path('api/cohorts', api.cohorts, name="api_cohorts"),
    path('api/datasets', api.datasets, name="api_datasets"),
    path('api/contracts', api.contracts, name="api_contracts"),
    path('api/partners', api.partners, name="api_partners"),
    path('api/permissions/<str:user_oidc_id>', api.permissions, name='api_permissions'),
    path('api/projects', api.projects, name="api_projects"),
    path('api/rems', api.rems_endpoint, name='api_rems_endpoint'),
    path('api/termsearch/<slug:category>', api.termsearch, name="api_termsearch"),
    path('api/users', api.users, name="api_users"),
    path('api/keycloak/force', api.force_keycloak_synchronization, name='api_keycloak_force'),

    # Contracts and partner roles
    path('contracts/', contract_list, name="contracts"),
    path('contracts/add/', ContractCreateView.as_view(), name='contract_add'),
    path('contracts/export/', contracts_export, name='contracts_export'),
    path('contracts/<int:pk>/', ContractDetailView.as_view(), name="contract"),
    path('contracts/<int:pk>/add-partner-role', contracts.PartnerRoleCreateView.as_view(), name="add_partner_role_to_contract"),
    path('contracts/<int:pk>/delete', ContractDelete.as_view(), name="contract_delete"),
    path('contracts/<int:pk>/edit', ContractEditView.as_view(), name="contract_edit"),
    path('partner_role/<int:pk>/edit', contracts.PartnerRoleEditView.as_view(), name="edit_partner_role"),
    path('partner_role/<int:pk>/delete', contracts.partner_role_delete, name="delete_partner_role"),

    # Data declaration
    path('dataset/<int:pk>/add-data-declaration', data_declarations.data_declarations_add, name='data_declarations_add'),
    path('data_declaration/<int:pk>/', DatadeclarationDetailView.as_view(), name="data_declaration"),
    path('data_declaration/<int:pk>/duplicate', data_declarations.data_declarations_duplicate, name='data_declarations_duplicate'),
    path('data_declaration/<int:pk>/delete', data_declarations.data_declarations_delete, name='data_declarations_delete'),
    path('data_declaration/<int:pk>/edit', DatadeclarationEditView.as_view(), name="data_declaration_edit"),
    path('data-declaration-sub-form', data_declarations.data_declarations_add_sub_form, name='data_declarations_add_sub_form'),
    path('data-declarations-get-contracts', data_declarations.data_declarations_get_contracts, name="data_declarations_get_contracts"),
    # TODO: merge the two search views into one
    path('data-declarations-autocomplete', data_declarations.data_declarations_autocomplete, name="data_declarations_autocomplete"),
    path('data-dec-paginated-search', data_declarations.data_dec_paginated_search, name="data_dec_paginated_search"),

    # Datasets
    path('datasets/', dataset_list, name="datasets"),
    path('datasets/export', datasets_export, name="datasets_export"),
    path('dataset/add/', DatasetCreateView.as_view(), name='dataset_add'),
    path('dataset/<int:pk>/', DatasetDetailView.as_view(), name="dataset"),
    path('dataset/<int:pk>/delete', DatasetDelete.as_view(), name="dataset_delete"),
    path('dataset/<int:pk>/edit', DatasetEditView.as_view(), name="dataset_edit"),
    path('dataset/<int:pk>/publish', publish_dataset, name="dataset_publish"),
    path('dataset/<int:pk>/unpublish', unpublish_dataset, name="dataset_unpublish"),
    # Dataset's StorageLocation methods
    path('dataset/<int:dataset_pk>/storagelocation/add/', storage_locations.StorageLocationCreateView.as_view(), name='dataset_storagelocation_add'),
    path('dataset/<int:dataset_pk>/storagelocation/remove/<int:storagelocation_pk>/', storage_locations.remove_storagelocation, name='dataset_storagelocation_remove'),
    path('dataset/<int:dataset_pk>/storagelocation/<int:pk>/edit', storage_locations.edit_storagelocation, name="dataset_storagelocation_edit"),
    # Dataset's Access (Internal access, as opposed to "Shares")
    path('dataset/<int:dataset_pk>/access/add/', AccessCreateView.as_view(), name='dataset_access_add'),
    path('dataset/<int:dataset_pk>/access/remove/<int:access_pk>/', access.remove_access, name='dataset_access_remove'),
    path('dataset/<int:dataset_pk>/access/<int:pk>/edit', access.edit_access, name="dataset_access_edit"),
    # Dataset's LegalBasis
    path('dataset/<int:dataset_pk>/legalbasis/add/', legalbasis.LegalBasisCreateView.as_view(), name='dataset_legalbasis_add'),
    path('dataset/<int:dataset_pk>/legalbasis/remove/<int:legalbasis_pk>/', legalbasis.remove_legalbasis, name='dataset_legalbasis_remove'),
    path('dataset/<int:dataset_pk>/legalbasis/<int:pk>/edit', legalbasis.edit_legalbasis, name="dataset_legalbasis_edit"),
    # Dataset's Shares (External access, as opposed to "Access")
    path('dataset/<int:dataset_pk>/share/add/', share.ShareCreateView.as_view(), name='dataset_share_add'),
    path('dataset/<int:dataset_pk>/share/remove/<int:share_pk>/', share.remove_share, name='dataset_share_remove'),
    path('dataset/<int:dataset_pk>/share/<int:pk>/edit', share.edit_share, name="dataset_share_edit"),

    # Cohorts
    path('definitions/cohorts/', cohort_list, name="cohorts"),
    path('definitions/cohorts/add', CohortCreateView.as_view(), name='cohort_add'),
    path('definitions/cohorts/export', cohorts_export, name="cohorts_export"),
    path('definitions/cohorts/<int:pk>/', CohortDetailView.as_view(), name="cohort"),
    path('definitions/cohorts/<int:pk>/delete', CohortDelete.as_view(), name="cohort_delete"),
    path('definitions/cohorts/<int:pk>/edit', CohortEditView.as_view(), name="cohort_edit"),
    path('definitions/cohorts/<int:pk>/publish', publish_cohort, name="cohort_publish"),
    path('definitions/cohorts/<int:pk>/unpublish', unpublish_cohort, name="cohort_unpublish"),

    # Contacts
    path('definitions/contacts/', contact_search_view, name='contacts'),   # Formerly; ContactListView.as_view()
    path('definitions/contact/<int:pk>', ContactDetailView.as_view(), name='contact'),
    path('definitions/contact/<int:pk>/edit', ContactEditView.as_view(), name='contact_edit'),
    path('definitions/contacts/add/', ContactCreateView.as_view(), name='contact_add'),
    path('definitions/contacts/<int:pk>/delete', ContactDelete.as_view(), name="contact_delete"),
    path('definitions/contacts/export', contacts_export, name='contacts_export'),

    # Partners
    path('definitions/partners/', partner_search_view, name='partners'),
    path('definitions/partners/add/', PartnerCreateView.as_view(), name='partner_add'),
    path('definitions/partners/export', partners_export, name="partners_export"),
    path('definitions/partners/<int:pk>/', PartnerDetailView.as_view(), name="partner"),
    path('definitions/partners/<int:pk>/delete', PartnerDelete.as_view(), name="partner_delete"),
    path('definitions/partners/<int:pk>/edit', PartnerEditView.as_view(), name='partner_edit'),
    path('definitions/partners/<int:pk>/publish', publish_partner, name='partner_publish'),
    path('definitions/partners/<int:pk>/unpublish', unpublish_partner, name='partner_unpublish'),
    
    # User Management
    path('definitions/users', UsersListView.as_view(), name="users"),
    path('definitions/users/add', UserCreateView.as_view(), name="users_add"),
    path('definitions/users/change-password', change_password, name="users_change_password"),
    path('definitions/users/<int:pk>/', UserDetailView.as_view(), name="user"),
    path('definitions/users/<int:pk>/delete', UserDelete.as_view(), name="user_delete"),
    path('definitions/users/<int:pk>/edit', UserEditView.as_view(), name="user_edit"),

    # Documents
    path('documents/<int:object_id>/<int:content_type>/add', documents.upload_document,  name='document_add'),
    path('documents/<int:pk>/delete', documents.delete_document, name='document_delete'),
    path('documents/<int:pk>/download', documents.download_document, name='document_download'),
    path('documents/<int:pk>/edit/', documents.document_edit, name='document_edit'),

    # Email reports
    path('email_reports', email_reports, name='email_reports'),
    path('email_reports/<int:pk>/preview', email_reports_preview, name='email_reports_preview'),
    path('email_reports/<int:pk>/delete', email_reports_disable_for_user, name='email_reports_disable_for_user'),

    # Notifications
    path('notifications/', notifications.index, name="notifications"),
    path('notifications/admin', notifications.admin, name="notifications_admin"),
    path('notifications/admin/<int:pk>', notifications.admin, name="notifications_admin_for_user"),

    # Permissions
    path('permissions/', permissions.index, name="permissions"),
    path('permissions/project/<int:pk>/', permissions.index, {'selection': 'project'}, name="permission_project"),
    path('permissions/dataset/<int:pk>/', permissions.index, {'selection': 'dataset'}, name="permission_dataset"),

    # Projects
    path('projects/', projects.project_list, name="projects"),
    path('projects/export', projects_export, name="projects_export"),
    path('project/add/', ProjectCreateView.as_view(), name='project_add'),
    path('project/<int:pk>/', ProjectDetailView.as_view(), name="project"),
    path('project/<int:pk>/delete', ProjectDelete.as_view(), name="project_delete"),
    path('project/<int:pk>/edit', ProjectEditView.as_view(), name="project_edit"),
    path('project/<int:pk>/publish', publish_project, name="project_publish"),
    path('project/<int:pk>/unpublish', unpublish_project, name="project_unpublish"),
    path('project/<int:pk>/add-contact', add_contact_to_project, name="add_contact_to_project"),
    path('project/<int:pk>/add-dataset', datasets.DatasetCreateView.as_view(), name="datasets_add_to_project"),
    path('project/<int:pk>/add-personnel', add_personnel_to_project, name="add_personnel_to_project"),
    path('project/<int:pk>/add-publication', add_publication_to_project, name="add_publication_to_project"),
    path('project/<int:pk>/del-contact/<int:contact_id>', remove_contact_from_project, name="remove_contact_from_project"),
    path('project/<int:pk>/del-personnel/<int:user_id>', remove_personnel_from_project, name="remove_personnel_from_project"),
    path('project/<int:pk>/del-publication/<int:publication_id>', remove_publication_from_project, name="remove_publication_from_project"),
    path('project/<int:pk>/pick-contact', pick_contact_for_project, name="pick_contact_for_project"),
    path('project/<int:pk>/pick-publication', pick_publication_for_project, name="pick_publication_for_project"),
    # Project's contract
    path('project/<int:pk>/contract/create', projects.project_contract_create, name="project_contract_create"),
    path('project/<int:pk>/contract/remove/<int:cid>', projects.project_contract_remove, name="project_contract_remove"),
    # Project's dataset
    path('project/<int:pk>/dataset/add', projects.project_dataset_add, name="project_dataset_add"),
    path('project/<int:pk>/dataset/create', projects.project_dataset_choose_type, name="project_dataset_choose_type"),
    path('project/<int:pk>/dataset/<int:flag>/create', projects.project_dataset_create, name="project_dataset_create"),

    # Publications
    path('publications/', PublicationListView.as_view(), name="publications"),
    path('publications/add/', PublicationCreateView.as_view(), name='publication_add'),
    path('publications/<int:pk>/edit', PublicationEditView.as_view(), name='publication_edit'),
    
    # Integrations
    path('integrations/dsw/list-projects', dsw_list_projects, name="integrations_dsw_projects")
]
