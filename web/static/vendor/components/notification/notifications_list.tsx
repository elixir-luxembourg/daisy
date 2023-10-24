"use strict";
import React, {useEffect, useState} from "react";
import {NotificationCard} from "./notification_card";
import * as CustomType from "./custom_types";

const API_URL_NOTIFICATIONS_LIST = "/notifications/api/notifications";

export const NotificationList = () => {
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [notifications, setNotifications] = useState<CustomType.Notification[]>([]);

    // Getting list of notifications from Django
    useEffect(() => {
        fetch(
            API_URL_NOTIFICATIONS_LIST,
        ).then(response => response.json() as Promise<CustomType.NotifApiResponse>
        ).then(json => {
            setNotifications(json.data);
            setIsLoading(false);
        }).catch(error => {
            console.error(error);
        });
    }, []);

    const notificationsPerContentType = notifications.reduce(
        (accumulator: {[key:string]: CustomType.Notification[]}, currentValue) => {
            (accumulator[currentValue.objectType] = accumulator[currentValue.objectType] || []).push(currentValue);
            return accumulator;
        }, {}
    );

    return (
        <>
            {isLoading || Object.keys(notificationsPerContentType).map(contentType =>
                <NotificationCard
                    key={`${contentType}-notifications`}
                    type={contentType}
                    data={notificationsPerContentType[contentType]}
                />
            )}
        </>
    );
};