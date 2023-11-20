$(document).ready(function (){
    const notifFilterForm = $("#admin-notifications-filter")[0];
    const showDismissedSwitch = $("#showDismissedNotifications")[0];

    const baseAction = notifFilterForm.action;
    const showDismissedParamPrefix = notifFilterForm.action.includes("?") ? "&" : "?";
    notifFilterForm.action = baseAction + `${showDismissedParamPrefix}show_dismissed=${showDismissedSwitch.checked}`;
    showDismissedSwitch.addEventListener("click", () => {
        notifFilterForm.action = baseAction + `${showDismissedParamPrefix}show_dismissed=${showDismissedSwitch.checked}`;
    })
})