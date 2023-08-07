import os
import unicodedata

from django.http import JsonResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import urlquote
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType

from core.constants import Permissions
from core.forms import DocumentForm
from core.models import Document
from core.permissions import permission_required, permission_required_from_content_type
from core.utils import DaisyLogger
from web.views.utils import is_ajax_request


log = DaisyLogger(__name__)


def rfc5987_content_disposition(file_name):
    ascii_name = unicodedata.normalize('NFKD', file_name).encode('ascii', 'ignore').decode()
    header = f'attachment; filename="{ascii_name}"'
    if ascii_name != file_name:
        quoted_name = urlquote(file_name)
        header += f'; filename*=UTF-8\'\'{quoted_name}'
    return header


@permission_required_from_content_type(Permissions.PROTECTED, content_type_attr='content_type', object_id_attr='object_id')
@permission_required_from_content_type(Permissions.EDIT, content_type_attr='content_type', object_id_attr='object_id')
def upload_document(request, object_id, content_type):
    log.debug('uploading document', post=request.POST, files=request.FILES)
    content_type_object = ContentType.objects.get(pk=content_type)
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if not form.is_valid():
            if not request.FILES:
                log.error('Upload failed: no document found.')
            else:
                log.error([str(e) for e in form.errors])
            return JsonResponse(form.errors, status=400) if is_ajax_request(request) else redirect(to=content_type_object.name, pk=object_id)

        else:
            document = form.save()
            messages.add_message(request, messages.SUCCESS, "Document added")
            redirecturl = document.content_type.name
            if is_ajax_request(request):
                return JsonResponse({"status_code": 200})
            else:
                return redirect(to=redirecturl, pk=document.object_id)

    else:
        form = DocumentForm(initial={'content_type':content_type, 'object_id': object_id})
    log.debug(submit_url=request.get_full_path())
    return render(request, 'modal_form.html', {'form': form, 'submit_url': request.get_full_path()})


@permission_required(Permissions.EDIT, 'document', (Document, 'pk', 'pk'))
@permission_required(Permissions.PROTECTED, 'document', (Document, 'pk', 'pk'))
def document_edit(request, pk):
    log.debug('editing document', post=request.POST)
    document = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        form = DocumentForm(request.POST,  request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, "Document updated")
            if is_ajax_request(request):
                return JsonResponse({
                    'success': {},
                })
            else:
                redirecturl = document.content_type.name
                return redirect(to=redirecturl, pk=document.object_id)
        else:
            return JsonResponse({
                'error': {
                    'type': 'Edit error',
                    'messages': form.errors,
                },
            }, status=405) if is_ajax_request(request) else redirect(to=document.content_type.name, pk=document.object_id)
    else:
        form = DocumentForm(instance=document)

    log.debug(submit_url=request.get_full_path())
    return render(request, 'modal_form.html', {'form': form, 'submit_url': request.get_full_path() })


@require_http_methods(["GET"])
@permission_required(Permissions.PROTECTED, 'document', (Document, 'pk', 'pk'))
def download_document(request, pk):
    document = get_object_or_404(Document, pk=pk)

    file_path = document.content.path
    if not os.path.exists(file_path):
        log.error(request, 'Document path not found.', path=document.content.path)
        raise Http404("Document path not found on the server.")

    with open(file_path, 'rb') as fh:
        response = HttpResponse(fh.read(), content_type="application/octet-stream")
        content_disposition = rfc5987_content_disposition(document.shortname)
        response['Content-Disposition'] = content_disposition
        return response


@require_http_methods(["DELETE"])
@permission_required(Permissions.PROTECTED, 'document', (Document, 'pk', 'pk'))
@permission_required(Permissions.EDIT, 'document', (Document, 'pk', 'pk'))
def delete_document(request, pk):
    document = get_object_or_404(Document, pk=pk)
    # perm = PERMISSION_MAPPING[document.content_type.name].DELETE.value
    # if not request.user.has_perm(perm, document.content_object):
    #     raise PermissionDenied
    try:
        document.delete()
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=403)
    return JsonResponse({'message': 'document deleted'})


