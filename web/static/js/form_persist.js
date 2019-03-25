var save_inputs = function() {
    var results = [];
    $("form input[type!=checkbox][type!=hidden]").not("[class*=select2]").each(function(index, el) {
       var $el = $(el);
       var el_value =  $el.val();

       var entry = {
            'name': el.name,
            'type': 'input',
            'value': el_value
        };
        results.push(entry);
    });
    return results;
};

var save_checkboxes = function() {
    var results = [];
    $("form input[type=checkbox]").each(function(index, el) {
       var is_checked = el.checked;
       var entry = {
            'type': 'checkbox',
            'value': is_checked,
            'name': el.name
        };
       results.push(entry);
    });
    return results;
};

var save_textareas = function() {
    var results = [];
    $("form textarea").each(function(index, el) {
        var entry = {
            'type': 'textarea',
            'name': el.name,
            'value': el.value
        };
        results.push(entry);
    });
    return results;
};

var save_selects = function() {
    var results = [];
    $("form select").each(function(index, el) {
        var ids = [];

        for (var i = 0, length = el.options.length; i < length; i++) {
            if ( el.options[i].selected ) {
                ids.push(el.options[i].value);
            }
        }

        var entry = {
            'type': 'select',
            'name': el.name,
            'value': ids
        };
        results.push(entry);
    });
    return results;
};

var save_form_contents = function() {
    var to_be_saved = [];
    to_be_saved = to_be_saved.concat(save_inputs());
    to_be_saved = to_be_saved.concat(save_textareas());
    to_be_saved = to_be_saved.concat(save_selects());
    to_be_saved = to_be_saved.concat(save_checkboxes());
    to_be_saved_json = JSON.stringify(to_be_saved);
    to_be_saved_json_b64 = btoa(to_be_saved_json);
    localStorage.setItem(window.location.href, to_be_saved_json_b64);
};

var restore_form_contents = function() {
    if (!window.localStorage.getItem(window.location.href))
        return;

    var state_json = atob(localStorage.getItem(window.location.href));
    var state = JSON.parse(state_json);

    $.each(state, function(index, el) {
        if (el['type'] == 'checkbox') {
            $("input[type=checkbox][name=" + el['name'] + "]").attr('checked', el['value']);
        } else if (el['type'] == 'input') {
            $("input[name=" + el['name'] + "]").val(el['value']);
        } else if (el['type'] == 'select') {
            var dom_el = $("select[name=" + el['name'] + "]");
            var $dom_el = $(dom_el);
            var ids = el['value'];
            var id_length = ids.length;

            $dom_el.select2();
            $dom_el.val(ids);
            $dom_el.trigger('change');

        } else if (el['type'] == 'textarea') {
            $("textarea[name=" + el['name'] + "]").val(el['value']);
        };
    });

    window.localStorage.removeItem(window.location.href);
};