"use strict";
import React, {useEffect, useState} from "react";
import {NotificationCard} from "./notification_card";
import * as CustomType from "./custom_types";
import {NotificationsTable} from "./notification_table";

const API_URL_NOTIFICATIONS_LIST = "/notifications/api/notifications";
const API_URL_DISMISS_NOTIFICATION = "/notifications/api/dismiss";
const API_URL_DISMISS_ALL_NOTIFICATION = "/notifications/api/dismiss-all";

type NotificationListProps = {
    showDismissed: boolean,
    showRecipientColumn: boolean,
    showDismissColumn: boolean,
    recipientFilter: number | null,
    csrf: string,
}

/**
 * NotificationList: React component that displays a list of notifications
 * @param showDismissed - If true, the list will display dismissed notifications
 * @param showRecipientColumn - If true, the list will display the recipient column
 * @param showDismissColumn - If true, the list will display the dismiss column
 * @param recipientFilter - If not null, the list will only display notifications for the given recipient
 * @param csrf - CSRF token
 *
 * @return - The list of notifications divided into cards by content type
 */
export const NotificationList = ({showDismissed, showRecipientColumn, showDismissColumn, recipientFilter, csrf}: NotificationListProps) => {
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [notifications, setNotifications] = useState<Record<string, CustomType.Notification[]>>({});

    /**
     * Group notifications by content type
     * @param data - List of notifications
     */
    const groupNotifications = (data: CustomType.Notification[]) => {
        return data.reduce(
            (accumulator: Record<string, CustomType.Notification[]>, currentValue) => {
                (accumulator[currentValue.objectType] = accumulator[currentValue.objectType] || []).push(currentValue);
                return accumulator;
            }, {}
        );
    };

    // Fetch notifications from the API
    useEffect(() => {
        let url = `${API_URL_NOTIFICATIONS_LIST}?show_dismissed=${showDismissed}&as_admin=${showRecipientColumn}`;
        if (recipientFilter) {
            url += `&recipient=${recipientFilter}`;
        }
        fetch(url)
            .then(response => response.json() as Promise<CustomType.NotifApiResponse>)
            .then(json => {
                setNotifications(groupNotifications(json.data));
                setIsLoading(false);
            }).catch(error => {
                console.error(error);
            });
    }, [showDismissed, showRecipientColumn, recipientFilter]);

    /**
     * Method to dismiss a notification
     * @param notification - Notification to dismiss
     */
    const dismissNotification = (notification: CustomType.Notification) => {
        fetch(
            `${API_URL_DISMISS_NOTIFICATION}/${notification.id}`,
            {
                method: "PATCH",
                body: null,
                headers: {"Content-Type": "application/json", "X-CSRFToken": csrf}
            },
        )
            .then(response => response.json() as Promise<CustomType.NotifApiResponse>)
            .then((json) => {
                const newNotifications = {...notifications};
                newNotifications[notification.objectType] = [...json.data];
                if (showDismissed) {
                    setNotifications(newNotifications);
                }
                else {
                    newNotifications[notification.objectType] = newNotifications[notification.objectType].filter((notif) => !notif.dismissed);
                    setNotifications(newNotifications);
                }
            })
            .catch(error => {
                console.error(`An error occurred while dismissing notification ${notification.id}`, error);
            });
    };

    /**
     * Method to dismiss all notifications of a given content type
     * @param contentType - Content type of the notifications to dismiss
     */
    const dismissAllNotifications = (contentType: string) => {
        fetch(
            `${API_URL_DISMISS_ALL_NOTIFICATION}/${contentType}`,
            {
                method: "PATCH",
                body: null,
                headers: {"Content-Type": "application/json", "X-CSRFToken": csrf},
            }
        )
            .then(response => response.json() as Promise<CustomType.NotifApiResponse>)
            .then((json) => {
                const newNotifications = {...notifications};
                if (showDismissed) {
                    newNotifications[contentType] = json.data;
                    setNotifications(newNotifications);
                }
                else {
                    newNotifications[contentType] = [];
                    setNotifications(newNotifications);
                }
            })
            .catch(error => {
                console.error(`An error occurred while dismissing notifications for ${contentType}`, error);
            });
    };


    if (Object.keys(notifications).some(contentType => notifications[contentType].length > 0)){
        // Display the list of notifications if there are any
        return (
            isLoading || Object.keys(notifications).sort().map(contentType => {
                if (notifications[contentType].length > 0) {
                    const newNotifNumber = notifications[contentType].filter(notif => !notif.dismissed).length;
                    return (
                        <NotificationCard
                            key={`${contentType}-notifications`}
                            type={contentType}
                            title={notifications[contentType][0].objectDisplayName}
                            newNotifNumber={newNotifNumber}
                            showDismissBtn={showDismissColumn}
                            dismissAll={dismissAllNotifications}
                        >
                            <NotificationsTable
                                data={notifications[contentType]}
                                showRecipient={showRecipientColumn}
                                showDismiss={showDismissColumn} onDismiss={dismissNotification}
                            />
                        </NotificationCard>
                    );
                }
            })
        );
    } else {
        // Display a message if there are no notifications
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