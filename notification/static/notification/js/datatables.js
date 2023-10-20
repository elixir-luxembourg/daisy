// import DataTable from "datatables.net";

const notificationsDT = document.querySelectorAll(".notifications-dt");
$(document).ready(() => {
    notificationsDT.forEach((notifTable) => {
        const colNb = notifTable.rows[0].cells.length;
        $(`#${notifTable.id}`).DataTable({
            "order": [[colNb-1, "desc"]],
        })
    })
});
