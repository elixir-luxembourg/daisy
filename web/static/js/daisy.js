$.fn.select2.defaults.set("theme", "bootstrap");


function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

var csrftoken;

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

function initDatepickers(elements) {
    elements.bootstrapMaterialDatePicker(
        {
            "time": false
        }
    );
}

function initDatetimepickers(elements) {

    elements.bootstrapMaterialDatePicker({
        "format": "YYYY-MM-DD H:mm:ss"
    });


}

function initFormsets(elements) {

    elements.formset({
        addText: '<h5><button class="btn bmd-btn-fab bmd-btn-fab-sm" type="button"><i class="material-icons">add</i><div class="ripple-container"></div></button><span class="ml-1">Add new</span></h5>',
        deleteText: '<i class="material-icons">delete</i>'
    });
}

function setupNotificationsIcon(){
    // Get number of new notifications
    const bellIcon = $("#notifications-bell");
    if (bellIcon.length){
        $.get(bellIcon.data().ajaxUrl, function(data){
            if (data.data > 0 && !bellIcon.parent().hasClass("active")){
                bellIcon.find("i").addClass("text-light");
                bellIcon.find("#notifications-badge").text(data.data);
            }
        });
    }
}

$(document).ready(function () {

    csrftoken = Cookies.get("csrftoken");

    $(".input-group-text>i.reset-form-button").click(function(){
        var $t = $(this);  // get the element
        var target_id = $t.data("resets");  // get the ID of element to reset
        var submits = $t.data("submits");  // should the form be submitted after resetting?
        var $el = $("#" + target_id);
        $el.val('').focus();  // reset the contents of editbox
        if (submits) {
            $el.form().submit();  // submit the form
        }
    });

    $('#users_table').DataTable();

    $('.nice-selects select').not('.dummy-select').select2({'width': '100%'});

    $('.ontocomplete').select2({
        ajax: {
            url: function (params) {
                return $(this).attr('data-url');
                },
            dataType: 'json',
            delay: 250,
            data: function (params) {
                var query = {
                    search: params.term,
                    page: params.page || 1
                }
                return query;
            },
            cache: true
        },
        placeholder: 'Search a term',
        minimumInputLength: 2
    });

    initDatepickers($('.datepicker'));
    initDatetimepickers($('.datetimepicker'));
    initFormsets($('.formset-row'));

    function _insertParamInURL(key, value) {
        // https://stackoverflow.com/a/487049
        key = encodeURI(key);
        value = encodeURI(value);

        var kvp = document.location.search.substr(1).split('&');

        var i = kvp.length;
        var x;
        while (i--) {
            x = kvp[i].split('=');
            if (x[0] == key) {
                x[1] = value;
                kvp[i] = x.join('=');
                break;
            }
        }
        if (i < 0) {
            kvp[kvp.length] = [key, value].join('=');
        }
        return kvp.join('&');
    }
    function confirmDialog(msg) {
        var def = $.Deferred();
        $("<div></div>").html("Proceed with "+ msg +"?").dialog({
            modal: true,
            title: 'Confirmation',
            buttons: {
                'Proceed': function() {
                    def.resolve();
                    $(this).dialog( "close" );
                },
                'Cancel': function() {
                    def.reject();
                    $(this).dialog( "close" );
                }
            },
            close: function() {
                $(this).dialog('destroy').remove();
                //$(this).remove();
            }
        });
        return def.promise();
    }

    function _loadModal(modal, title, url, button, postMode, ajaxRefreshSelector, ajaxRefreshParam, redirectURI, data) {
        if (data !== undefined) {
            url = url.split('?')[0];
            url += '?' + _insertParamInURL(ajaxRefreshParam, data);
        }
        modal.find('.modal-title').text(title);
        modal.find('.modal-body').load(url, function () {

            modal.bootstrapMaterialDesign();
            initDatepickers(modal.find('.datepicker'));
            initDatetimepickers(modal.find('.datetimepicker'));
            initFormsets(modal.find('.formset-row'));
            modal.find('select').not('.dummy-select').select2({dropdownParent: $('#modal')});

            // if postMode we will submit the form with ajax
            if (postMode) {
                var modalForm = modal.find('form');
                modalForm.submit(function (e) {
                    // remove is-invalid classes and feedback
                    modal.find(".invalid-feedback").remove();
                    modalForm.find(".form-control").removeClass('is-invalid');
                    e.preventDefault();
                    $.ajax({
                        url: url,
                        type: 'post',
                        dataType: 'json',
                        data: new FormData(modalForm[0]),
                        contentType: false,
                        processData: false,
                        cache: false,
                        success: function (results) {
                            if (redirectURI !== undefined) {
                                window.location.replace(redirectURI);
                            } else {
                                var select = button.siblings('select');
                                modal.modal('toggle');
                                var pk = results.pk;
                                var label = results.label;
                                var newOption = new Option(label, pk, true, true);
                                select.append(newOption).trigger('change');
                            }
                        },
                        error: function (response) {
                            var errors = response.responseJSON;
                            for (var i in errors) {
                                if (i === '__all__'){
                                    errors[i].map( (error) => {
                                        modalForm.after(
                                            $('<div class="invalid-feedback d-block">' + error + '</div>')
                                        );
                                    })}
                                else {
                                    var input = modalForm.find('[name=' + i + ']');
                                    input.addClass('is-invalid');
                                    input.after($('<div class="invalid-feedback">' + errors[i] + '</div>'));
                                }
                            }
                        }
                    });

                });
            }

            // an action can be trigered via a field on change
            if (ajaxRefreshSelector !== undefined) {
                modal.find(ajaxRefreshSelector).on('change', function (evt) {
                    var data = $(ajaxRefreshSelector).val();
                    _loadModal(modal, title, url, button, postMode, ajaxRefreshSelector, ajaxRefreshParam, redirectURI, data);
                })
            }
        });
    }

    // MODAL WINDOWS
    $('#modal').on('show.bs.modal', function (event) {
        var modal = $(this);
        modal.find('.modal-body').empty();
        var button = $(event.relatedTarget); // Button that triggered the modal
        var title = button.data('modal-title');
        var content = button.data('modal-content');
        var ajaxUrl = button.data('ajax-url');
        var postMode = button.data('post-mode');
        var ajaxRefreshSelector = button.data('ajax-refresh-selector');
        var ajaxRefreshParam = button.data('ajax-refresh-param');
        var redirectURI = button.data('ajax-redirect-uri');
        if (ajaxUrl !== undefined) {
            _loadModal(modal, title, ajaxUrl, button, postMode, ajaxRefreshSelector, ajaxRefreshParam, redirectURI);
        } else {
            modal.find('.modal-body').text(content);
        }
    });
    // TOOLTIPS
    $('[data-toggle="tooltip"]').tooltip();
    // DELETABLE
    $('.deletable').hover(function () {
        var url_delete = $(this).data('url');
        var delete_link = $("<i  id='dynamic_delete_button' class='red delete-button material-icons'>delete_forever</i>").data('url', url_delete);
        var delete_title = $(this).data('delete-title');
         if (delete_title){
            delete_link.attr('title', delete_title);
        }
        $(this).append(delete_link);
    }, function () {
        $(this).find('.delete-button').remove();
    });
    $('.deletable').on('click', '.delete-button', function () {
        var url_delete = $(this).data('url');
        var that_parent = $(this).parent();
        confirmDialog("delete").done(function() {
            $.ajax({
                url: url_delete,
                type: 'DELETE',
                success: function (result) {
                    that_parent.remove();
                }
            });
        });
    });
    $('.clickable').css('cursor', 'pointer').click(function () {
        var urlClick = $(this).data('url');
        var method = $(this).data('method');
        var parentElementClassToRemove = $(this).data('parent-to-remove');
        var parentElementToRemove = $(this).closest(parentElementClassToRemove);
        var confirmation = $(this).data('confirmation');
        if (confirmation) {
            confirmDialog(confirmation).done(function() {
                $.ajax({
                    url: urlClick,
                    type: method,
                    success: function (result) {
                        if (parentElementClassToRemove) {
                            parentElementToRemove.remove();
                            return;
                        }
                    }
                });
            });
        } else{
            $.ajax({
                url: urlClick,
                type: method,
                success: function (result) {
                    if (parentElementClassToRemove) {
                        parentElementToRemove.remove();
                        return;
                    }
                }
            });
    }
    });

    // Load notifications bell
    setupNotificationsIcon();

    $(document).on('click', 'a[data-confirm]', function(e) {
        var message = $(this).data('confirm');
        if (!confirm(message)) {
            e.stopImmediatePropagation();
            e.preventDefault();
        }
    });
});

