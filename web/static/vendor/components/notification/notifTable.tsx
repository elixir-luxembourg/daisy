"use strict";
import React, {useEffect, useState} from "react";

const API_URL_NOTIFICATIONS_LIST = "/notifications/api/notifications";

export const NotificationList = () => {
    const [isLoading, setIsLoading] = useState(true);
    const [notifications, setNotifications] = useState([]);

    // Getting list of notifications from Django
    useEffect(() => {

    });
    return (<span>Hello from React TypeScript!</span>);
};