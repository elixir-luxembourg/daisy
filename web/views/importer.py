from django.contrib.auth.decorators import login_required, user_passes_test
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from core.forms.importer import ImportForm
from django.core.management import call_command
from django.conf import settings
import os
import logging
from io import StringIO
from django.http import JsonResponse, HttpResponseForbidden
from web.views.utils import is_ajax_request, is_data_steward


@login_required
@require_http_methods(["GET", "POST"])
@user_passes_test(is_data_steward)
def import_data(request, model_type):
    """
    Handle the importation of data based on the provided model type.

    This function first checks if the user has the required permissions and if the request is an AJAX request.
    Depending on the HTTP method (GET/POST), it either presents the import form or processes the uploaded data.

    Args:
        request (HttpRequest): The request object.
        model_type (str): The type of the model for which data is being imported.

    Returns:
        JsonResponse: A JSON response containing the rendered HTML form or errors.
    """
    if not is_ajax_request(request):
        return HttpResponseForbidden()
    if request.method == "GET":
        form = ImportForm(initial={"model_type": model_type})
        return render_form_to_json(form, model_type)
    if request.method == "POST":
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data["file"]
            file_path = save_uploaded_file(uploaded_file, model_type)
            output = process_uploaded_file(file_path, model_type)
            os.remove(file_path)
            return render_form_to_json(None, model_type, output)
        else:
            return render_form_to_json(form, model_type)


def render_form_to_json(form, model_type, output=None):
    """
    Render the import form to a JSON response.

    Args:
        form (Form): The import form instance.
        model_type (str): The type of the model for which data is being imported.
        output (dict, optional): Any output data or messages to be included in the rendered HTML.

    Returns:
        JsonResponse: A JSON response containing the rendered HTML form.
    """
    form_html = render_to_string(
        "importer/import_form.html",
        {
            "form": form,
            "model_type": model_type,
            "output": output,
        },
    )
    return JsonResponse({"form_html": form_html})


def save_uploaded_file(uploaded_file, model_type):
    """
    Save the uploaded file to a temporary location.

    Args:
        uploaded_file (UploadedFile): The uploaded file object.
        model_type (str): The type of the model for which data is being imported.

    Returns:
        str: The path to the saved file.
    """
    file_path = os.path.join(settings.MEDIA_ROOT, f"temp_{model_type}.json")
    with open(file_path, "wb+") as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
    return file_path


def process_uploaded_file(file_path, model_type):
    """
    Process the uploaded file based on the provided model type.

    This function leverages Django's call_command to run the appropriate management command for processing.

    Args:
        file_path (str): The path to the uploaded file.
        model_type (str): The type of the model for which data is being imported.

    Returns:
        dict: A dictionary containing processing results, logs, and any errors.
    """
    cmd_args = [
        f"import_{model_type}",
        "--file",
        file_path,
        "--exit-on-error",
        "--skip-on-exist",
    ]

    stdout_buffer = StringIO()
    stderr_buffer = StringIO()

    log_buffer = StringIO()
    log_handler = logging.StreamHandler(log_buffer)
    LOGGING_FORMAT = "%(levelname)s: %(message)s"
    log_formatter = logging.Formatter(LOGGING_FORMAT)
    log_handler.setFormatter(log_formatter)
    logger = logging.getLogger()
    original_level = logger.level
    logger.propagate = True

    logger.setLevel(logging.NOTSET)  # Set to NOTSET to capture logs of all levels
    logger.addHandler(log_handler)

    try:
        call_command(*cmd_args, stdout=stdout_buffer, stderr=stderr_buffer)
        if stderr_buffer.getvalue():
            success = False
        else:
            success = True
        return {
            "success": success,
            "message": stdout_buffer.getvalue(),
            "error": stderr_buffer.getvalue(),
            "logs": log_buffer.getvalue(),
        }
    except Exception as e:
        return {
            "success": False,
            "message": stdout_buffer.getvalue(),
            "error": str(e) + "\n" + stderr_buffer.getvalue(),
            "logs": log_buffer.getvalue(),
        }
    finally:
        logger.removeHandler(log_handler)
        logger.setLevel(original_level)  # Reset the logger level to its original level
        logger.propagate = False
