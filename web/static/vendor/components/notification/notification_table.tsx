"use strict";
import React, {useState, useEffect} from "react";
import {createColumnHelper, flexRender, getCoreRowModel, useReactTable} from "@tanstack/react-table";
import type {Notification} from "./custom_types";


type DismissButtonProps = {
    notification: Notification
    onClick: (notification: Notification) => void,
}

/**
 * DismissButton: React component that displays a button to dismiss a notification
 * @param notification - Notification to dismiss
 * @param onClick - Function to call when the button is clicked
 *
 * @return - The button to dismiss the notification
 */
const DismissButton = ({notification, onClick}: DismissButtonProps) => {
    return <span className={"btn btn-link p-0 m-0"} onClick={() => onClick(notification)}>Dismiss</span>;
};

const columnHelper = createColumnHelper<Notification>();
const dateFormatter = new Intl.DateTimeFormat(
    Intl.DateTimeFormat().resolvedOptions().locale,
    {
        year: "numeric",
        month: "short",
        day: "numeric",
    }
);

/**
 * NotificationsTableProps: Props for the NotificationsTable component
 *
 * @param data - List of notifications to display
 * @param showRecipient - If true, the table will display the recipient column
 * @param showDismiss - If true, the table will display the dismiss column
 * @param onDismiss - Function to call when a notification is dismissed
 *
 */
type NotificationsTableProps = {
    data: Notification[]
    showRecipient: boolean,
    showDismiss: boolean,
    onDismiss: (notification: Notification) => void,
}

/**
 * NotificationsTable: React component to display a table of notifications
 * @param {NotificationsTableProps} props
 *
 * @return - The table of notifications
 */
export const NotificationsTable = (props: NotificationsTableProps) => {
    const [notifications, setNotifications] = useState(props.data);

    // Update the notifications when the props change
    useEffect(() => {
        setNotifications(props.data);
    }, [props.data]);

    const columns = [
        // The recipient columns displays the full name of the recipient
        columnHelper.accessor("recipient.name", {
            header: "Recipient",
            id: "fullName",
            enableHiding: true,
        }),
        // The objectName column displays the name of the object that triggered the notification
        columnHelper.accessor("objectName", {
            header: () => {
                const title = notifications[0].objectType;
                return title.charAt(0).toUpperCase() + title.substring(1);
            },
            cell: cell => {
                const text = cell.getValue();
                const displayedText = text.length < 70 ? text : text.substring(0, 70) + "...";
                return (
                    cell.row.original.objectUrl ?
                        <a href={cell.row.original.objectUrl}>
                            {displayedText}
                        </a> :
                        <span>
                            {displayedText}
                        </span>
                );
            }
        }),
        // The message column displays the description of the notification
        columnHelper.accessor("message", {
            header: "Description",
            cell: ({cell}) => {
                const text = cell.getValue();
                return (
                    <span>
                        {text.length < 70 ? text : text.substring(0, 70) + "..."}
                    </span>
                );
            }
        }),
        // The on column displays the date of the event that triggered the notification
        columnHelper.accessor("on", {
            header: "Event date",
            cell: cell => {
                const isoDateTime = cell.getValue();
                return isoDateTime ? dateFormatter.format(new Date(isoDateTime)) : "";
            },
        }),
        // The time column displays the date when the notification was sent
        columnHelper.accessor("time", {
            header: "Sent on",
            cell: cell => dateFormatter.format(new Date(cell.getValue())),
        }),
        // The dismissAction column displays a button to dismiss the notification if it is not already dismissed
        columnHelper.display({
            id: "dismissAction",
            cell: cell => cell.row.original.dismissed || <DismissButton notification={cell.row.original} onClick={props.onDismiss}/>,
            enableHiding: true,
        }),
    ];

    const columnVisibility = {
        "fullName": props.showRecipient,
        "dismissAction": props.showDismiss,
    };

    const table = useReactTable({
        data: notifications,
        columns: columns,
        state: {
            columnVisibility
        },
        getCoreRowModel: getCoreRowModel(),
    });

    const shouldDisplayTitle = (identifier: string) => {
        return ["message", "objectName"].includes(identifier);
    };

    return (
        <table className={"table table-striped"}>
            <thead>
                {table.getHeaderGroups().map(headerGroup => (
                    <tr key={headerGroup.id} style={{position: "relative"}}>
                        {headerGroup.headers.map(header => (
                            <th
                                key={header.id}
                                scope="col"
                            >
                                {header.isPlaceholder ?
                                    null :
                                    flexRender(header.column.columnDef.header,header.getContext())
                                }
                            </th>
                        ))}
                    </tr>
                ))}
            </thead>
            <tbody>
                {table.getRowModel().rows.map(row => (
                    <tr key={row.id}>
                        {row.getVisibleCells().map(cell => (
                            <td key={cell.id} title={shouldDisplayTitle(cell.column.id) ? (cell.getValue() as string) : undefined}>
                                {flexRender(cell.column.columnDef.cell, cell.getContext())}
                            </td>
                        ))}
                    </tr>
                ))}
            </tbody>
        </table>
    );
};
