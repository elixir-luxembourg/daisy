const skipInput = document.getElementById(skipInputID)
const skipButton = document.getElementById('skipButton')

if (skipButton) {
    skipButton.addEventListener('click', function () {
        if (skipInput) {
            skipInput.value = 'True';
            document.getElementById('wizard-form').submit();
        }
    });
}

/*
 * On page load, this script checks if the current step is `data_declaration`.
 * If true, it listens for changes on any radio button input. When a radio button
 * input changes, the script dynamically loads and inserts a sub-form based on
 * the selected declaration type and the dataset ID. This sub-form is placed
 * before the form footer. Additionally, after loading the sub-form, it initializes
 * select2 on any select fields and applies Bootstrap Material Design styles.
 */

$(document).ready(function () {
    if (stepName === 'data_declaration') {
        $('input[type=radio]').change(function () {
            const form_footer = $("#form_footer")
            $("#sub-form").remove();
            const sub_form = $("<div id='sub-form'>");
            form_footer.before(sub_form);
            const declaration_type = this.value;
            const forms_url = dataDeclarationsAddSubFormUrl + '?declaration_type=' + declaration_type + '&dataset_id=' + dataset_id;
            sub_form.load(forms_url, function () {
                    sub_form.find('select').select2();
                    sub_form.bootstrapMaterialDesign();
                }
            )
            ;
        });
    }

});