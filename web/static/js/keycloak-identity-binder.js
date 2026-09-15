$(function () {
    $(document).on("click", ".keycloak-bind", function () {
        const trigger = $(this);
        const modal = $("#modal");
        const body = modal.find(".modal-body");
        modal.find(".modal-title").text("Find in Keycloak");
        body.empty().append($("<div>", {
            class: "space-y-4",
            html: `
                <p class="text-sm text-gray-500">Accounts for <span class="font-medium text-primary-900">${trigger.data("email")}</span></p>
                <div role="alert" class="hidden text-sm text-danger-900"></div>
                <div class="keycloak-candidates space-y-2"></div>`,
        }));
        openModal(modal);

        const error = body.find("[role=alert]");
        const candidates = body.find(".keycloak-candidates");
        $.get(trigger.data("candidates-url")).done(function (response) {
            if (!response.results.length) {
                error.text("No matching account found. Correct the email of the user first.").removeClass("hidden");
                return;
            }
            response.results.forEach(function (candidate) {
                const button = $("<button>", {
                    type: "button",
                    class: "block w-full rounded-xs border border-gray-300 px-3 py-2 text-left text-sm text-primary-900 hover:border-primary-900",
                    text: candidate.text,
                });
                button.on("click", function () {
                    bindIdentity(candidate.id, trigger, modal, error);
                });
                candidates.append(button);
            });
        }).fail(function (xhr) {
            error.text(xhr.responseJSON ? xhr.responseJSON.error : "Could not search Keycloak.").removeClass("hidden");
        });
    });

    function bindIdentity(oidcId, trigger, modal, error) {
        $.post(trigger.data("bind-url"), {
            csrfmiddlewaretoken: Cookies.get("csrftoken"),
            oidc_id: oidcId,
        }).done(function (response) {
            // the oidc_id is immutable, so the cell becomes a plain value
            trigger.replaceWith($("<span>", {
                class: "font-mono text-xs",
                text: response.user.oidc_id,
            }));
            closeModal(modal);
        }).fail(function (xhr) {
            error.text(xhr.responseJSON ? xhr.responseJSON.error : "Could not bind the account.").removeClass("hidden");
        });
    }
});
