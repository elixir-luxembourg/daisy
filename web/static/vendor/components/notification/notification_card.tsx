"use strict";
import React from "react";

type NotificationHeaderProps = {
    category: string,
    newNotifications: number
    showDismissNumber: boolean
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
            {props.showDismissNumber && props.newNotifications > 0 &&
                <h5 className={"badge badge-primary card-badge"}>{props.newNotifications}</h5>
            }
        </div>
    );
};

type NotificationCardProps = {
    type: string
    children: React.ReactElement,
    newNotifNumber: number,
    showDismissBtn: boolean,
    dismissAll: (contentType: string) => void,
};

export const NotificationCard = ({type, newNotifNumber, children, showDismissBtn, dismissAll}: NotificationCardProps) => {
    return (
        <div className={"row mt-4 accordion"}>
            <div className={"card col px-0"}>
                <NotificationHeader category={type} showDismissNumber={showDismissBtn} newNotifications={newNotifNumber} />
                <div id={`accordion-body-${type}`} className={"collapse p-3"}>
                    {showDismissBtn &&
                        <div className={"d-flex justify-content-end"}>
                            <a className={"btn btn-link btn-outline float-right"} onClick={() => dismissAll(type)}>Dismiss all</a>
                        </div>
                    }
                    <div className={"card-body"}>
                        <div id={`form-container-${type}`} className={"card-text table-responsive"}>
                            { children }
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};



