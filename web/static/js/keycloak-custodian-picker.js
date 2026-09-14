$(function () {
    $(document).on("click", ".keycloak-custodian-add", function () {
        const trigger = $(this);
        const select = $("#" + trigger.data("select-id"));
        const modal = $("#modal");
        const body = modal.find(".modal-body");
        const title = modal.find(".modal-title");
        title.text("Add local custodian");
        body.empty().append($("<form>", {
            class: "space-y-4",
            html: `
                <label class="block text-sm font-medium text-primary-900">Email
                    <input type="email" required class="mt-1 block w-full rounded-xs border border-gray-300 px-3 py-2" autofocus>
                </label>
                <div role="alert" class="hidden text-sm text-danger-900"></div>
                <div class="keycloak-custodian-results space-y-2"></div>
                <div class="flex justify-end">
                    <button type="submit" class="inline-flex h-10 items-center justify-center rounded-lg bg-primary-900 px-4 text-sm font-medium text-on-primary">Search</button>
                </div>`,
        }));
        openModal(modal);

        body.find("form").on("submit", function (event) {
            event.preventDefault();
            const form = $(this);
            const error = form.find("[role=alert]").addClass("hidden");
            const results = form.find(".keycloak-custodian-results").empty();
            const email = form.find("input").val();
            $.get(trigger.data("search-url"), {email: email}).done(function (response) {
                if (!response.results.length) {
                    error.text("No matching account found.").removeClass("hidden");
                    return;
                }
                response.results.forEach(function (candidate) {
                    const button = $("<button>", {
                        type: "button",
                        class: "block w-full rounded-xs border border-gray-300 px-3 py-2 text-left text-sm text-primary-900 hover:border-primary-900 disabled:cursor-not-allowed disabled:opacity-50",
                        text: candidate.text,
                        disabled: !candidate.is_active,
                    });
                    button.on("click", function () {
                        if (candidate.id.startsWith("keycloak:")) {
                            provisionCandidate(candidate.id.substring("keycloak:".length), trigger.data("provision-url"), select, modal, error);
                        } else {
                            addUser(select, candidate, modal);
                        }
                    });
                    results.append(button);
                });
            }).fail(function () {
                error.text("Could not search Keycloak.").removeClass("hidden");
            });
        });
    });

    function provisionCandidate(oidcId, provisionUrl, select, modal, error) {
        $.post(provisionUrl, {csrfmiddlewaretoken: Cookies.get("csrftoken"), oidc_id: oidcId}).done(function (response) {
            addUser(select, response.user, modal);
        }).fail(function (xhr) {
            error.text(xhr.responseJSON ? xhr.responseJSON.error : "Could not add user.").removeClass("hidden");
        });
    }

    function addUser(select, user, modal) {
        if (!select.find("option[value='" + user.id + "']").length) {
            select.append(new Option(user.text, user.id, true, true));
        }
        select.val(select.val().concat([String(user.id)])).trigger("change");
        closeModal(modal);
    }
});