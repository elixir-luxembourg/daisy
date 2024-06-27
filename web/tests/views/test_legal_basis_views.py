import pytest
from typing import Union
from django.shortcuts import reverse

from test.factories import (
    VIPGroup,
    DataStewardGroup,
    LegalGroup,
    AuditorGroup,
    LegalBasisFactory,
    DatasetFactory,
    UserFactory,
)
from core.models.legal_basis import LegalBasis
from core.models.user import User
from core.models.dataset import Dataset
from core.constants import Permissions
from .utils import check_response_status


def check_legal_basis_views_permissions(
    url: str, user: User, obj: Union[Dataset, LegalBasis], method: str = "GET"
):
    if user.is_part_of(DataStewardGroup()):
        assert user.has_permission_on_object(
            f"core.{Permissions.EDIT.value}_dataset", obj
        )
    else:
        assert not user.has_permission_on_object(
            f"core.{Permissions.EDIT.value}_dataset", obj
        )

    check_response_status(
        url, user, [f"core.{Permissions.EDIT.value}_dataset"], obj, method
    )
    if user.is_part_of(VIPGroup()):
        parent_dataset = obj if isinstance(obj, Dataset) else obj.dataset
        parent_dataset.local_custodians.set([user])
        assert user.has_permission_on_object(
            f"core.{Permissions.EDIT.value}_dataset", obj
        )
        check_response_status(
            url, user, [f"core.{Permissions.EDIT.value}_dataset"], obj, method
        )


@pytest.mark.parametrize(
    "group", [VIPGroup, DataStewardGroup, LegalGroup, AuditorGroup]
)
@pytest.mark.parametrize(
    "url_name",
    ["dataset_legalbasis_add", "dataset_legalbasis_remove", "dataset_legalbasis_edit"],
)
def test_legal_basis_views_permissions(permissions, group, url_name):
    """
    Tests whether users from different groups can access urls associated with LegalBasis instances
    """
    legal_basis = None
    dataset = DatasetFactory()
    dataset.save()
    if url_name == "dataset_legalbasis_add":
        url = reverse(url_name, kwargs={"dataset_pk": dataset.pk})
    else:
        legal_basis = LegalBasisFactory(dataset=dataset)
        legal_basis.save()
        # Url placeholder for legal_basis pk has a different name for dataset_legal_basis_remove view
        key_name = "legalbasis_pk" if url_name == "dataset_legalbasis_remove" else "pk"
        url = reverse(
            url_name, kwargs={"dataset_pk": dataset.pk, key_name: legal_basis.pk}
        )

    assert url is not None
    user = UserFactory(groups=[group()])
    check_legal_basis_views_permissions(
        url,
        user,
        legal_basis if legal_basis is not None else dataset,
        method="DELETE" if url_name == "dataset_legalbasis_remove" else "GET",
    )
