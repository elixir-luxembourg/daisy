"use strict";
import React from "react";
import {createRoot} from "react-dom/client";
import type {Root} from "react-dom/client";
import {NotificationList} from "./notifications_list";


const notifDivDOM = document.getElementById("react-notifications");
const csrfTokenNode = document.querySelector<HTMLInputElement>("input[name=csrfmiddlewaretoken]");
const showDismissedToggle = document.querySelector<HTMLInputElement>("#showDismissedNotifications");
if (notifDivDOM && csrfTokenNode){
    const recipientFilter = notifDivDOM.dataset.recipientFilter ?
        parseInt(notifDivDOM.dataset.recipientFilter, 10) :
        null;

    const renderNotifications = (reactRoot: Root) => {
        reactRoot.render(
            <React.StrictMode>
                <NotificationList
                    showDismissed={showDismissedToggle ? showDismissedToggle.checked : false}
                    showRecipientColumn={notifDivDOM.dataset.showRecipientColumn === "true"}
                    showDismissColumn={notifDivDOM.dataset.showDismissColumn === "true"}
                    recipientFilter={recipientFilter}
                    csrf={csrfTokenNode.value}
                />
            </React.StrictMode>
        );
    };

    const root = createRoot(notifDivDOM);
    renderNotifications(root);

    if (showDismissedToggle) {
        showDismissedToggle.addEventListener("click", () => {
            renderNotifications(root);
        });
    }
}