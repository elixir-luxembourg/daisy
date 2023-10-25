import React from "react";

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
    children: React.ReactElement,
    newNotifNumber: number,
};

export const NotificationCard = ({type, newNotifNumber, children}: NotificationCardProps) => {
    return (
        <div className={"row mt-4 accordion"}>
            <div className={"card col px-0"}>
                <NotificationHeader category={type} newNotifications={newNotifNumber} />
                <div id={`accordion-body-${type}`} className={"collapse"}>
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



