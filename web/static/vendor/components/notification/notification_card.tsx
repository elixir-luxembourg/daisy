import React from "react";
import {Notification} from "./custom_types";
import {NotificationsTable} from "./notification_table";

type NotificationHeaderProps = {
    category: string,
    newNotifications: number
};

const NotificationHeader = (props: NotificationHeaderProps) => {
    const title = `${props.category.charAt(0).toUpperCase()}${props.category.substring(1)} Notifications`;
    return (
        <div
            id={`accordion-header-${props.category}`}
            className={"card-header btn btn-link position-relative"}
            data-toggle={"collapse"}
            data-target={`#accordion-body-${props.category}`}
            aria-expanded={"false"}
            aria-controls={`accordion-body-${props.category}`}
        >
            <h2 className={"card-title"}>{title}</h2>
            {props.newNotifications > 0 &&
                <h5 className={"badge badge-primary card-badge"}>{props.newNotifications}</h5>
            }
        </div>
    );
};

type NotificationCardProps = {
    type: string
    data: Notification[],
};

export const NotificationCard = ({type, data}: NotificationCardProps) => {
    const newNotificationsNumber = data.filter(notif => !notif.dismissed).length;
    return (
        <div className={"row mt-4 accordion"}>
            <div className={"card col px-0"}>
                <NotificationHeader category={type} newNotifications={newNotificationsNumber} />
                <div id={`accordion-body-${type}`} className={"collapse"}>
                    <div className={"card-body"}>
                        <div id={`form-container-${type}`} className={"card-text"}>
                            <NotificationsTable data={data} showRecipient={true} showDismiss={true} />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};



