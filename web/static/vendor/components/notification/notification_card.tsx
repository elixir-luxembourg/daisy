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
        <button
            type={"button"}
            id={`accordion-header-${category}`}
            className={"flex w-full items-center justify-between gap-4 px-4 py-3 text-left hover:bg-gray-50"}
            aria-expanded={!isCollapsed}
            aria-controls={`accordion-body-${category}`}
            onClick={onClick}
        >
            <div className={"relative"}>
                <h2 className={"text-lg font-semibold text-blue-950"}>{title}</h2>
                {showDismissNumber && newNotifications > 0 &&
                    <span className={"absolute -right-6 -top-2 inline-flex min-w-5 items-center justify-center rounded-full bg-red-900 px-1 text-xs font-semibold text-white"}>{newNotifications}</span>
                }
            </div>
            <svg
                xmlns={"http://www.w3.org/2000/svg"}
                width={"20"}
                height={"20"}
                viewBox={"0 0 24 24"}
                fill={"none"}
                stroke={"currentColor"}
                strokeWidth={"2"}
                strokeLinecap={"round"}
                strokeLinejoin={"round"}
                aria-hidden={"true"}
                className={`h-5 w-5 shrink-0 text-blue-900 transition-transform duration-200 ease-out ${isCollapsed ? "" : "rotate-180"}`}
            >
                <path d={"m6 9 6 6 6-6"}/>
            </svg>
        </button>
    );
};

type NotificationCardProps = {
    title: string,
    type: string
    children: React.ReactElement,
    newNotifNumber: number,
    showDismissBtn: boolean,
};

/**
 * NotificationCard: The card for each notification category
 * @param title - The title of the notification card
 * @param type - The category of the notification
 * @param newNotifNumber - The number of new notifications in the category
 * @param children - The React components to render in the card
 * @param showDismissBtn - Whether to show the dismiss all button
 *
 * @return - The card for the notification category
 */
export const NotificationCard = ({title, type, newNotifNumber, children, showDismissBtn}: NotificationCardProps) => {
    const [isCollapsed, setCollapsed] = useState(true);
    return (
        <div className={"mt-4 rounded border border-gray-200 bg-white shadow-sm"}>
            <div>
                <NotificationHeader
                    className={title}
                    category={type}
                    showDismissNumber={showDismissBtn}
                    newNotifications={newNotifNumber}
                    isCollapsed={isCollapsed}
                    onClick={() => setCollapsed(c => !c)}
                />
                { isCollapsed ||
                    <div id={`accordion-body-${type}`} className={"overflow-x-auto border-t border-gray-200 text-sm"}>
                        {children}
                    </div>
                }
            </div>
        </div>
    );
};
