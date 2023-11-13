$(document).ready(function () {
    // Show the modal when the button is clicked
    $('#importModalButton').click(function () {
        $('#importModal').modal('show');
        fetchForm();
    });

    // Fetch the form via AJAX
    function fetchForm() {
        $.get(importDataUrl, function (data) {
            $("#importForm").html(data.form_html);
            // Initially disable the submit button
            $("#ajaxSubmitButton").prop("disabled", true);
            // Monitor changes on the file input
            $("#id_file").on("change", function () {
                // If file input has a file, enable the submit button
                if ($(this).val()) {
                    $("#ajaxSubmitButton").prop("disabled", false);
                } else {
                    $("#ajaxSubmitButton").prop("disabled", true);
                }
            });
            $('#ajaxSubmitButton').on('click', function () {
                submitForm();
            });
        });
    }
});

function submitForm() {
    const formData = new FormData($('#importForm form')[0]);
    $.ajax({
        url: importDataUrl,
        type: 'POST',
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