"use strict";
import React, {useEffect, useState} from "react";
import {NotificationCard} from "./notification_card";
import * as CustomType from "./custom_types";
import {NotificationsTable} from "./notification_table";

const API_URL_NOTIFICATIONS_LIST = "/notifications/api/notifications";
const API_URL_DISMISS_NOTIFICATION = "/notifications/api/dismiss";
const API_URL_DISMIS_ALL_NOTIFICATION = "/notifications/api/dismiss-all";

type NotificationListProps = {
    showDismissed: boolean,
    showRecipientColumn: boolean,
    showDismissColumn: boolean
    csrf: string,
}
export const NotificationList = ({showDismissed, showRecipientColumn, showDismissColumn, csrf}: NotificationListProps) => {
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [notifications, setNotifications] = useState<{[key: string]: CustomType.Notification[]}>({});

    const groupNotifications = (data: CustomType.Notification[]) => {
        return data.reduce(
            (accumulator: {[key:string]: CustomType.Notification[]}, currentValue) => {
                (accumulator[currentValue.objectType] = accumulator[currentValue.objectType] || []).push(currentValue);
                return accumulator;
            }, {}
        );
    };

    // Getting list of notifications from Django
    useEffect(() => {
        fetch(
            `${API_URL_NOTIFICATIONS_LIST}?show_dismissed=${showDismissed}&as_admin=${showRecipientColumn}`,
        ).then(response => response.json() as Promise<CustomType.NotifApiResponse>
        ).then(json => {
            setNotifications(groupNotifications(json.data));
            setIsLoading(false);
        }).catch(error => {
            console.error(error);
        });
    }, [showDismissed, showRecipientColumn]);

    const dismissNotification = (notification: CustomType.Notification) => {
        fetch(
            `${API_URL_DISMISS_NOTIFICATION}/${notification.id}`,
            {
                method: "PATCH",
                body: null,
                headers: {"Content-Type": "application/json", "X-CSRFToken": csrf}
            },
        ).then(() => {
            const newNotifications = JSON.parse(JSON.stringify(notifications)) as {[key:string]: CustomType.Notification[]};
            if (showDismissed) {
                const updatedNotification = newNotifications[notification.objectType].find(notif => notif.id === notification.id);
                if (updatedNotification){
                    updatedNotification.dismissed = true;
                    setNotifications(newNotifications);
                }
                else {
                    throw `Notification ${notification.id} was not found in list of notifications`;
                }
            }
            else {
                newNotifications[notification.objectType] = newNotifications[notification.objectType].filter((notif) => notif.id !== notification.id);
                setNotifications(newNotifications);
            }
        }).catch(error => {
            console.error(`An error occurred while dismissing notification ${notification.id}`, error);
        });
    };

    const dismissAllNotifications = (contentType: string) => {
        fetch(
            `${API_URL_DISMIS_ALL_NOTIFICATION}/${contentType}`,
            {
                method: "PATCH",
                body: null,
                headers: {"Content-Type": "application/json", "X-CSRFToken": csrf},
            }
        ).then(() => {
            const newNotifications = JSON.parse(JSON.stringify(notifications)) as {[key:string]: CustomType.Notification[]};
            if (showDismissed) {
                newNotifications[contentType].forEach(notif => notif.dismissed = true);
                setNotifications(newNotifications);
            }
            else {
                newNotifications[contentType] = [];
                setNotifications(newNotifications);
            }
        }).catch(error => {
            console.error(`An error occurred while dismissing notifications for ${contentType}`, error);
        });
    };
    if (Object.keys(notifications).some(contentType => notifications[contentType].length > 0)){
        return (
            isLoading || Object.keys(notifications).map(contentType => {
                if (notifications[contentType].length > 0) {
                    const newNotifNumber = notifications[contentType].filter(notif => !notif.dismissed).length;
                    return (
                        <NotificationCard
                            key={`${contentType}-notifications`}
                            type={contentType}
                            newNotifNumber={newNotifNumber}
                            showDismissBtn={showDismissColumn}
                            dismissAll={dismissAllNotifications}
                        >
                            <NotificationsTable
                                data={notifications[contentType]}
                                showRecipient={showRecipientColumn}
                                showDismiss={showDismissColumn} onDismiss={dismissNotification}/>
                        </NotificationCard>
                    );
                }
            })
        );
    } else {
        return (
            <div className={"row mt-4 accordion"}>
                <div className={"card col px-0"}>
                    <div className={"card-header"}>
                        <h2 className={"card-title"}>Notifications</h2>
                    </div>
                    <div className={"card-body"}>
                        <p className={"card-text"}>No notification was found</p>
                    </div>
                </div>
            </div>
        );
    }
};