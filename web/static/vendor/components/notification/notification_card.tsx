"use strict";
import React, {MouseEventHandler, useState} from "react";

type NotificationHeaderProps = {
    className: string,
    category: string,
    newNotifications: number,
    showDismissNumber: boolean,
    isCollapsed: boolean,
    onClick: MouseEventHandler,
};

/**
 * NotificationHeader: The header for each notification card
 * @param className - The title of the notification card
 * @param category - The category of the notification
 * @param newNotifications - The number of new notifications in the category
 * @param showDismissNumber - Whether to show the number of new notifications
 * @param isCollapsed - Whether the card is collapsed or not
 * @param onClick - The function to call when the header is clicked
 *
 * @return - The header for the notification card
 */
const NotificationHeader = ({className, category, newNotifications, showDismissNumber, isCollapsed, onClick}: NotificationHeaderProps) => {
    const title = `${className.charAt(0).toUpperCase()}${className.substring(1)} Notifications`;
    return (
        <div
            id={`accordion-header-${category}`}
            className={"card-header btn btn-link d-flex justify-content-center"}
            data-toggle={"collapse"}
            data-target={`#accordion-body-${category}`}
            aria-expanded={"false"}
            aria-controls={`accordion-body-${category}`}
            onClick={onClick}
        >
            <div className={"position-relative"}>
                <h2 className={"card-title"}>{title}</h2>
                {showDismissNumber && newNotifications > 0 &&
                    <span className={"badge badge-danger card-badge"}>{newNotifications}</span>
                }
            </div>
            <div className={"accordion-toggle"}>
                {isCollapsed ?
                    <i className={"material-icons"}>expand_less</i> :
                    <i className={"material-icons"}>expand_more</i>
                }
            </div>
        </div>
    );
};

type NotificationCardProps = {
    title: string,
    type: string
    children: React.ReactElement,
    newNotifNumber: number,
    showDismissBtn: boolean,
    dismissAll: (contentType: string) => void,
};

/**
 * NotificationCard: The card for each notification category
 * @param title - The title of the notification card
 * @param type - The category of the notification
 * @param newNotifNumber - The number of new notifications in the category
 * @param children - The React components to render in the card
 * @param showDismissBtn - Whether to show the dismiss all button
 * @param dismissAll - The function to dismiss all notifications in the category
 *
 * @return - The card for the notification category
 */
export const NotificationCard = ({title, type, newNotifNumber, children, showDismissBtn, dismissAll}: NotificationCardProps) => {
    const [isCollapsed, setCollapsed] = useState(true);
    return (
        <div className={"row mt-4 accordion"}>
            <div className={"card col px-0"}>
                <NotificationHeader
                    className={title}
                    category={type}
                    showDismissNumber={showDismissBtn}
                    newNotifications={newNotifNumber}
                    isCollapsed={isCollapsed}
                    onClick={() => setCollapsed(c => !c)}
                />
                { isCollapsed ||
                    <div id={`accordion-body-${type}`} className={"collapse p-3"}>
                        {showDismissBtn && newNotifNumber > 0 &&
                            <div className={"d-flex justify-content-end"}>
                                <button
                                    className={"btn btn-link btn-outline float-right"}
                                    type={"button"}
                                    onClick={() => dismissAll(type)}
                                >
                                    Dismiss all
                                </button>
                            </div>
                        }
                        <div className={"card-body"}>
                            <div id={`form-container-${type}`} className={"card-text table-responsive"}>
                                {children}
                            </div>
                        </div>
                    </div>
                }
            </div>
        </div>
    );
};
