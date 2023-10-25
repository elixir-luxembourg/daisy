"use strict";
import React from "react";
import {createRoot} from "react-dom/client";
import {NotificationList} from "./notifications_list";


const notifDivDOM = document.getElementById("react-notifications");
if (notifDivDOM){
    const root = createRoot(notifDivDOM);
    root.render(
        <React.StrictMode>
            <NotificationList showDismissed={notifDivDOM.dataset.showDismissed === "true"}/>
        </React.StrictMode>
    );
}