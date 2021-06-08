import urllib

from typing import Dict, Optional

from django.conf import settings

from core.models.cohort import Cohort
from core.models.dataset import Dataset
from core.models.partner import Partner
from core.models.project import Project
from core.models.utils import CoreTrackedModel


def _http_post(url: str, data: Dict):
    request = urllib.request.Request(url, data)
    response = urllib.request.urlopen(request).read().decode('utf-8')
    return response

def _call_idservice(entity_type: str, name: Optional[str]=None):
    url = getattr(settings, 'IDSERVICE_ENDPOINT')
    data = {
        "entity": entity_type,
    }
    if name is not None:
        data['name'] = name
    return _http_post(url, data)

def generate_identifier(obj: CoreTrackedModel, save=True):
    klass = type(obj).__name__
    if not isinstance(obj, (Dataset, Project, Cohort, Partner)):
        msg = f'Unrecognized entity! (Only Project, Dataset, Cohort and Partner are recognized; got - {klass})'
        raise ValueError(msg)
    
    if hasattr(obj, 'title'):
        title = obj.title
    elif hasattr(obj, 'name'):
        title = obj.name
    else:
        msg = f'Cannot find the object''s name! (The object of class {klass} does not have title nor name attribute!'
        raise KeyError(msg)

    the_id = _call_idservice(klass.lower(), title)
    obj.elu_accession = the_id
    
    if save:
        obj.save()

    return obj
