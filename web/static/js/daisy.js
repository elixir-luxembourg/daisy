function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

let csrftoken;

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

function initDatepickers(elements) {
    if (!elements.length) {
        return;
    }
    elements.attr("type", "date");
}

function initDatetimepickers(elements) {
    if (!elements.length) {
        return;
    }
    elements.attr("type", "datetime-local");
}

function initFormsets(elements) {
    if (!elements.length || !$.fn.formset) {
        return;
    }
    elements.formset({
        addText: '<span class="inline-flex items-center gap-1"><i data-lucide="plus" class="h-5 w-5"></i><span>Add new</span></span>',
        deleteText: '<i data-lucide="trash-2" class="h-5 w-5 text-red-600"></i>',
        addCssClass: 'add-row inline-flex items-center gap-1 mt-3 text-sm font-medium text-blue-900 hover:text-blue-700',
        deleteCssClass: 'delete-row inline-flex cursor-pointer text-red-600 hover:text-red-700'
    });
    if (window.lucide) {
        window.lucide.createIcons();
    }
}

function setupNotificationsIcon(){
    const bellIcon = $("#notifications-bell");
    if (bellIcon.length){
        $.get(bellIcon.data().ajaxUrl, function(data){
            if (data.data > 0){
                bellIcon.find("i").addClass("text-white");
                bellIcon.find("#notifications-badge").text(data.data);
            }
        });
    }
}

function openModal(modal) {
    modal.removeAttr("hidden").addClass("flex").attr("aria-hidden", "false");
    $("body").addClass("overflow-hidden");
    if (window.lucide) {
        window.lucide.createIcons();
    }
}

function closeModal(modal) {
    modal.attr("hidden", "").removeClass("flex").attr("aria-hidden", "true");
    modal.find(".modal-body").empty();
    $("body").removeClass("overflow-hidden");
}

function insertParamInURL(url, key, value) {
    const parsedURL = new URL(url, window.location.origin);
    parsedURL.searchParams.set(key, value);
    return parsedURL.pathname + parsedURL.search + parsedURL.hash;
}

function getModalTitle(modal) {
    return modal.find(".modal-title, #modalLabel").first();
}

function clearModalErrors(modal) {
    modal.find(".invalid-feedback, .ajax-field-error").remove();
    modal.find(".is-invalid").removeClass("is-invalid");
    modal.find("[name]").removeClass("border-red-500 focus:border-red-500 focus:ring-red-500");
}

function addFieldError(input, error) {
    input.addClass("border-red-500 focus:border-red-500 focus:ring-red-500");
    input.after($('<div class="invalid-feedback ajax-field-error mt-1 text-sm text-red-600">' + error + '</div>'));
}

function showModalErrors(modalForm, errors) {
    Object.keys(errors).forEach(function (name) {
        const messages = Array.isArray(errors[name]) ? errors[name] : [errors[name]];
        if (name === "__all__") {
            messages.forEach(function (error) {
                modalForm.prepend(
                    $('<div class="invalid-feedback ajax-field-error mb-3 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">' + error + '</div>')
                );
            });
            return;
        }
        const input = modalForm.find("[name]").filter(function () {
            return this.name === name;
        }).first();
        if (input.length) {
            messages.forEach(function (error) {
                addFieldError(input, error);
            });
        }
    });
}

function confirmDialog(msg) {
    const def = $.Deferred();
    if (window.confirm("Proceed with " + msg + "?")) {
        def.resolve();
    } else {
        def.reject();
    }
    return def.promise();
}

function loadModal(modal, title, url, button, postMode, ajaxRefreshSelector, ajaxRefreshParam, redirectURI, data) {
    const modalBody = modal.find(".modal-body");
    const modalTitle = getModalTitle(modal);
    if (data !== undefined) {
        url = insertParamInURL(url, ajaxRefreshParam, data);
    }
    modalTitle.text(title || "");
    modalBody.html('<div class="py-8 text-center text-sm text-gray-500">Loading...</div>');
    openModal(modal);
    modalBody.load(url, function () {
        initDatepickers(modal.find(".datepicker"));
        initDatetimepickers(modal.find(".datetimepicker"));
        initFormsets(modal.find(".formset-row"));
        if ($.fn.select2) {
            modal.find("select").not(".dummy-select").select2({dropdownParent: modal});
        }
        if (window.lucide) {
            window.lucide.createIcons();
        }
        if (postMode) {
            const modalForm = modal.find("form");
            modalForm.off("submit.daisyModal").on("submit.daisyModal", function (e) {
                clearModalErrors(modal);
                e.preventDefault();
                $.ajax({
                    url: url,
                    type: "post",
                    dataType: "json",
                    data: new FormData(modalForm[0]),
                    contentType: false,
                    processData: false,
                    cache: false,
                    success: function (results) {
                        if (redirectURI !== undefined) {
                            window.location.replace(redirectURI);
                            return;
                        }
                        const select = button.siblings("select");
                        if (select.length) {
                            const newOption = new Option(results.label, results.pk, true, true);
                            select.append(newOption).trigger("change");
                        }
                        closeModal(modal);
                    },
                    error: function (response) {
                        showModalErrors(modalForm, response.responseJSON || {});
                    }
                });
            });
        }
        if (ajaxRefreshSelector !== undefined) {
            modal.find(ajaxRefreshSelector).off("change.daisyModal").on("change.daisyModal", function () {
                loadModal(modal, title, url, button, postMode, ajaxRefreshSelector, ajaxRefreshParam, redirectURI, $(this).val());
            });
        }
    });
}

function showModalFromTrigger(trigger) {
    const target = trigger.data("target") || "#modal";
    const modal = $(target);
    if (!modal.length) {
        return;
    }
    const title = trigger.data("modal-title") || trigger.attr("title") || "";
    const content = trigger.data("modal-content");
    const ajaxUrl = trigger.data("ajax-url");
    const postMode = trigger.data("post-mode") !== undefined && trigger.data("post-mode") !== false;
    const ajaxRefreshSelector = trigger.data("ajax-refresh-selector");
    const ajaxRefreshParam = trigger.data("ajax-refresh-param");
    const redirectURI = trigger.data("ajax-redirect-uri");
    modal.find(".modal-body").empty();
    if (ajaxUrl !== undefined) {
        loadModal(modal, title, ajaxUrl, trigger, postMode, ajaxRefreshSelector, ajaxRefreshParam, redirectURI);
        return;
    }
    getModalTitle(modal).text(title);
    modal.find(".modal-body").text(content || "");
    openModal(modal);
}

$(document).ready(function () {

    csrftoken = Cookies.get("csrftoken");

    $(document).on("click", ".reset-form-button", function(){
        const $t = $(this);
        const targetId = $t.data("resets");
        const submits = $t.data("submits");
        const $el = $("#" + targetId);
        $el.val("").focus();
        if (submits) {
            $el.closest("form").submit();
        }
    });

    if ($.fn.DataTable && $("#users_table").length) {
        $("#users_table").DataTable();
    }

    if ($.fn.select2) {
        $(".nice-selects select").not(".dummy-select").select2({"width": "100%"});

        $(".ontocomplete").select2({
            ajax: {
                url: function () {
                    return $(this).attr("data-url");
                },
                dataType: "json",
                delay: 250,
                data: function (params) {
                    return {
                        search: params.term,
                        page: params.page || 1
                    };
                },
                cache: true
            },
            placeholder: "Search a term",
            minimumInputLength: 2
        });
    }

    initDatepickers($(".datepicker"));
    initDatetimepickers($(".datetimepicker"));
    initFormsets($(".formset-row"));

    $(document).on("click", '[data-toggle="modal"]', function (event) {
        event.preventDefault();
        showModalFromTrigger($(this));
    });
    $(document).on("click", "[data-modal-close]", function () {
        closeModal($("#modal"));
    });
    $("#modal").on("click", function (event) {
        if (event.target === this) {
            closeModal($(this));
        }
    });
    $(document).on("keydown", function (event) {
        if (event.key === "Escape" && !$("#modal").attr("hidden")) {
            closeModal($("#modal"));
        }
    });

    $(".deletable").hover(function () {
        const url_delete = $(this).data("url");
        const delete_link = $('<i data-lucide="trash-2" class="delete-button ml-2 inline-flex h-4 w-4 cursor-pointer align-middle text-red-600"></i>').attr("data-url", url_delete);
        const delete_title = $(this).data("delete-title");
        if (delete_title){
            delete_link.attr("title", delete_title);
        }
        $(this).append(delete_link);
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }, function () {
        $(this).find(".delete-button").remove();
    });
    $(".deletable").on("click", ".delete-button", function () {
        const url_delete = $(this).data("url");
        const that_parent = $(this).parent();
        confirmDialog("delete").done(function() {
            $.ajax({
                url: url_delete,
                type: "DELETE",
                success: function () {
                    that_parent.remove();
                }
            });
        });
    });
    $(".clickable").css("cursor", "pointer").click(function () {
        const urlClick = $(this).data("url");
        const method = $(this).data("method");
        if (!urlClick || !method) {
            return;
        }
        const parentElementClassToRemove = $(this).data("parent-to-remove");
        const parentElementToRemove = $(this).closest(parentElementClassToRemove);
        const confirmation = $(this).data("confirmation");
        if (confirmation) {
            confirmDialog(confirmation).done(function() {
                $.ajax({
                    url: urlClick,
                    type: method,
                    success: function () {
                        if (parentElementClassToRemove) {
                            parentElementToRemove.remove();
                        }
                    }
                });
            });
        } else{
            $.ajax({
                url: urlClick,
                type: method,
                success: function () {
                    if (parentElementClassToRemove) {
                        parentElementToRemove.remove();
                    }
                }
            });
        }
    });

    setupNotificationsIcon();

    $(document).on("click", "a[data-confirm]", function(e) {
        const message = $(this).data("confirm");
        if (!confirm(message)) {
            e.stopImmediatePropagation();
            e.preventDefault();
        }
    });
});
