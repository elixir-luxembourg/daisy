var $controls_with_add_buttons = $(".has-add-button");

var create_template = function(url) {
    var template = '<a class="add-button" target="_blank" href="';
    template += url;
    template += '">Click here to add new one</a>';
    return template;
};

var create_links_to_add_new_items = function() {
    $controls_with_add_buttons.each(function (index, el) {
        // Adds link to each control
        var $el = $(el);
        var $parent = $el.parent();
        var path = $el.data('path');
        $parent.append('<small class="form-text text-muted"></small>');
        var $small_el = $($parent.children("small")[0]);
        $small_el.append(create_template(path));
    });

    $("a.add-button").click(function () {
        if (save_form_contents == undefined) {
            console.error("form_persist.js was not loaded before using form_adder.js");
        }
        save_form_contents();
    });
}