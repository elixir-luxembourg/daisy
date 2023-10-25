"use strict";
import React, {useEffect, useState} from "react";
import {NotificationCard} from "./notification_card";
import * as CustomType from "./custom_types";
import {NotificationsTable} from "./notification_table";

const API_URL_NOTIFICATIONS_LIST = "/notifications/api/notifications";


export const NotificationList = ({showDismissed}: {showDismissed: boolean}) => {
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [notifications, setNotifications] = useState<CustomType.Notification[]>([]);

    // Getting list of notifications from Django
    useEffect(() => {
        fetch(
            `${API_URL_NOTIFICATIONS_LIST}?show_dismissed=${showDismissed}`,
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

    const dismissNotification = (id: number) => {
        console.log(`Dismissing notification ${id}`);
    };

    return (
        <>
            {isLoading || Object.keys(notificationsPerContentType).map(contentType => {
                const newNotifNumber = notificationsPerContentType[contentType].filter(notif => !notif.dismissed).length;
                return (
                    <NotificationCard
                        key={`${contentType}-notifications`}
                        type={contentType}
                        newNotifNumber={newNotifNumber}
                    >
                        <NotificationsTable
                            data={notificationsPerContentType[contentType]}
                            showRecipient={true}
                            showDismiss={true} onDismiss={dismissNotification}/>
                    </NotificationCard>
                );
            })}
        </>
    );
};