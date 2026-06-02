const skipInput = typeof skipInputID !== "undefined" ? document.getElementById(skipInputID) : null;
const skipButton = document.getElementById("skipButton");
if (skipButton && skipInput) {
    skipButton.addEventListener("click", function () {
        skipInput.value = "True";
        document.getElementById("wizard-form").submit();
    });
}

$(document).ready(function () {
    if (typeof stepName !== "undefined" && stepName === "data_declaration") {
        $("input[type=radio]").change(function () {
            const form_footer = $("#form_footer");
            $("#sub-form").remove();
            const sub_form = $("<div id='sub-form'>");
            form_footer.before(sub_form);
            const declaration_type = this.value;
            const forms_url = `${dataDeclarationsAddSubFormUrl}?declaration_type=${declaration_type}&dataset_id=${dataset_id}`;
            sub_form.load(forms_url, function () {
                if ($.fn.select2) {
                    sub_form.find("select").select2();
                }
            });
        });
    }

});
