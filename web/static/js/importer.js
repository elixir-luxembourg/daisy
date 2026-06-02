$(document).ready(function () {
    const importModal = document.getElementById("importModal");
    if (!importModal || typeof importDataUrl === "undefined") {
        return;
    }

    $("#importModalButton").click(function () {
        importModal.showModal();
        fetchForm();
    });

    $("#importModalClose").click(function () {
        importModal.close();
    });

    function fetchForm() {
        $.get(importDataUrl, function (data) {
            $("#importForm").html(data.form_html);
            $("#ajaxSubmitButton").prop("disabled", true);
            $("#id_file").on("change", function () {
                $("#ajaxSubmitButton").prop("disabled", !$(this).val());
            });
            $("#ajaxSubmitButton").on("click", function () {
                submitForm();
            });
        });
    }
});

function submitForm() {
    const form = $("#importForm form")[0];
    if (!form) {
        return;
    }
    const formData = new FormData(form);
    $.ajax({
        url: importDataUrl,
        type: "POST",
        data: formData,
        cache: false,
        contentType: false,
        processData: false,
        success: function (data) {
            $("#importForm form").html(data.form_html);
        },
        error: function (data) {
            $("#importForm form").html(data.form_html);
        }
    });
}
