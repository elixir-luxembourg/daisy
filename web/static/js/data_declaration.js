const skipInput = document.getElementById(skipInputID)
const skipButton = document.getElementById('skipButton')
if (!skipInput) {
    skipButton.remove();
}
if (skipButton) {
    skipButton.addEventListener('click', function () {
        if (skipInput) {
            skipInput.value = 'True';
            document.getElementById('wizard-form').submit();
        }
    });
}
$(document).ready(function () {
    $('input[type=radio]').change(function () {
        const submit_button = $("#buttons")
        $("#sub-form").remove();
        const sub_form = $("<div id='sub-form'>");
        submit_button.before(sub_form);
        const declaration_type = this.value;
        const forms_url = dataDeclarationsAddSubFormUrl + '?declaration_type=' + declaration_type + '&dataset_id=' + dataset_id;
        sub_form.load(forms_url, function () {
                sub_form.find('select').select2();
                sub_form.bootstrapMaterialDesign();
            }
        )
        ;
    });
});