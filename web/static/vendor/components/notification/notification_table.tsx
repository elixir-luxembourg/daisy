import React, {useState} from "react";
import {createColumnHelper, flexRender, getCoreRowModel, useReactTable} from "@tanstack/react-table";
import type {Notification} from "./custom_types";

// TODO:
// - Fix the width of the columns
// - Add links to objects (where possible)
// - Format the dates
// - Set the behavior for the DISMISS btn

type DismissButtonProps = {
    id: number
}

const DismissButton = ({id}: DismissButtonProps) => {
    const onClick = () => {
        console.log(`Dismissing notification ${id}`);
    };

    return <span className={"btn btn-link p-0 m-0"} onClick={onClick}>Dismiss</span>;
};

const columnHelper = createColumnHelper<Notification>();

type NotificationsTableProps = {
    data: Notification[]
    showRecipient: boolean,
    showDismiss: boolean,
}

export const NotificationsTable = (props: NotificationsTableProps) => {
    const [notifications,] = useState(props.data);

    const columns = [
        columnHelper.accessor("recipient.name", {
            header: "Recipient",
            enableHiding: true,
            size: 150,
        }),
        columnHelper.accessor("objectName", {
            header: () => {
                const title = notifications[0].objectType;
                return title.charAt(0).toUpperCase() + title.substring(1);
            },
            size: 350,
            cell: cell => <span className={"text-truncate d-block"}>{cell.getValue()}</span>
        }),
        columnHelper.accessor("message", {
            header: "Description",
            size: 350,
            cell: cell => <span className={"text-truncate d-block"}>{cell.getValue()}</span>
        }),
        columnHelper.accessor("on", {
            header: "Event date",
            cell: cell => {
                const isoDateTime = cell.getValue();
                return isoDateTime ? new Date(isoDateTime).toDateString() : "";
            },
            size: 150,
        }),
        columnHelper.accessor("time", {
            header: "Sent on",
            cell: cell => new Date(cell.getValue()).toDateString(),
            size: 150,
        }),
        columnHelper.display({
            id: "dismiss",
            cell: cell => cell.row.original.dismissed || <DismissButton id={cell.row.original.id} />,
            size: 85,
        }),
    ];
    const columnVisibility = {
        "recipient": !props.showRecipient,
        "dismissAction": !props.showDismiss,
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
        <table className={"table table-striped table-borderless table-sm"}>
            <thead>
                {table.getHeaderGroups().map(headerGroup => (
                    <tr key={headerGroup.id} style={{position: "relative"}}>
                        {headerGroup.headers.map(header => (
                            <th
                                key={header.id}
                                scope="col"
                                style={{maxWidth: header.getSize()}}
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
                            <td key={cell.id} style={{maxWidth: cell.column.getSize()}}>
                                {flexRender(cell.column.columnDef.cell, cell.getContext())}
                            </td>
                        ))}
                    </tr>
                ))}
            </tbody>
        </table>
    );
};
