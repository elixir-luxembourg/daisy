
var csrftoken;

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});



// Adapting the datatables width when accordions are clicked



$(document).ready(() => {
    csrftoken = Cookies.get("csrftoken");

    const notificationsDT = document.querySelectorAll(".notifications-dt");

    notificationsDT.forEach((notifTable) => {
        console.log(notifTable);
        // Building the datatable
        const colIndexes = {}
        for (const index of Array(notifTable.rows[0].cells.length).keys()){
            const header = notifTable.rows[0].cells[index];
            colIndexes[header.innerText.toString().replace(" ", "-").toLowerCase()] = index;
        }

        // Building default options
        const tableOptions = {
            "order": [[colIndexes["received-on"], "desc"]],
        };

        // Adding options for 'dismiss' columns when it exists
        if (colIndexes["dismissed"]){
            tableOptions["columnDefs"] = [
                {orderable: false, searchable: false, targets: colIndexes["dismiss-all"]},
                {visible: false, targets: colIndexes["dismissed"]},
                {visible: true, targets: '_all'},
            ];
        }

        // Building the table
        const individualDataTable = $(`#${notifTable.id}`).DataTable(tableOptions)
        individualDataTable.columns.adjust().draw();

        if (colIndexes["dismissed"]) {
            // Hiding dismissed notifications by default;]
            individualDataTable.columns(colIndexes["dismissed"]).search("False").draw();

            // Build the checkbox to display/hide dismissed notifications
            const showDismissedDOM = `&nbsp;&nbsp;/&nbsp;&nbsp;<label>Show dismissed&nbsp;&nbsp;</label><input id="${notifTable.id}-show-dismissed" type="checkbox" />`;
            $(`#${notifTable.id}_length`).append(showDismissedDOM);
            const showDismissed = document.querySelector(`#${notifTable.id}-show-dismissed`);
            showDismissed.addEventListener("input", () => {
                if (showDismissed.checked) {
                    individualDataTable.columns(colIndexes["dismissed"]).search("").draw();
                } else {
                    individualDataTable.columns(colIndexes["dismissed"]).search("False").draw();
                }
            });
        }
        console.log(individualDataTable.data());
    })

    // Write method to call api to get notifications regarding a user (default is None for admin) and a content_type
    document.querySelectorAll(".btn[data-toggle='collapse']").forEach((el) => {
       el.addEventListener("shown.bs.collapse", () => {
           console.log("Accordion is triggered to show");
           $.dataTable.tables({ visible: true }).columns.adjust();
       })
    });
});
