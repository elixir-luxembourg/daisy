"use strict";
import React from "react";
import {createRoot} from "react-dom/client";
import {NotificationList} from "./notifications_list";


const notifDivDOM = document.getElementById("react-notifications");
const csrfTokenNode: HTMLInputElement | null = document.querySelector<HTMLInputElement>("input[name=csrfmiddlewaretoken]");
if (notifDivDOM && csrfTokenNode){
    const root = createRoot(notifDivDOM);
    root.render(
        <React.StrictMode>
            <NotificationList
                showDismissed={notifDivDOM.dataset.showDismissed === "true"}
                showRecipientColumn={notifDivDOM.dataset.showRecipientColumn === "true"}
                showDismissColumn={notifDivDOM.dataset.showDismissColumn === "true"}
                csrf={csrfTokenNode.value}
            />
        </React.StrictMode>
    );
}