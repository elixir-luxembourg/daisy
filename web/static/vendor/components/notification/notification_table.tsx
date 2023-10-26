"use strict";
import React, {useState, useEffect} from "react";
import {createColumnHelper, flexRender, getCoreRowModel, useReactTable} from "@tanstack/react-table";
import type {Notification} from "./custom_types";

// TODO:
// - Add links to objects (where possible)

type DismissButtonProps = {
    notification: Notification
    onClick: (notification: Notification) => void,
}

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

type NotificationsTableProps = {
    data: Notification[]
    showRecipient: boolean,
    showDismiss: boolean,
    onDismiss: (notification: Notification) => void,
}

export const NotificationsTable = (props: NotificationsTableProps) => {
    const [notifications, setNotifications] = useState(props.data);
    useEffect(() => {
        setNotifications(props.data);
    }, [props.data]);

    const columns = [
        columnHelper.accessor("recipient.name", {
            header: "Recipient",
            id: "fullName",
            enableHiding: true,
        }),
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
        columnHelper.accessor("message", {
            header: "Description",
            cell: cell => {
                const text = cell.getValue();
                return (
                    <span>
                        {text.length < 70 ? text : text.substring(0, 70) + "..."}
                    </span>
                );
            }
        }),
        columnHelper.accessor("on", {
            header: "Event date",
            cell: cell => {
                const isoDateTime = cell.getValue();
                return isoDateTime ? dateFormatter.format(new Date(isoDateTime)) : "";
            },
        }),
        columnHelper.accessor("time", {
            header: "Sent on",
            cell: cell => dateFormatter.format(new Date(cell.getValue())),
        }),
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
                            <td key={cell.id}>
                                {flexRender(cell.column.columnDef.cell, cell.getContext())}
                            </td>
                        ))}
                    </tr>
                ))}
            </tbody>
        </table>
    );
};
