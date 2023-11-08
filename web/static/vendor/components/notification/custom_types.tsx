"use strict";
// Defined custom types that are specific to the notification app here

import type {UserObject} from "../common/custom_types";

export type Notification = {
    id: number
    recipient: UserObject,
    verb: string,
    on: string|null,
    time: string,
    sentInApp: boolean,
    sentByEmail: boolean,
    dismissed: boolean,
    message: string,
    objectType: string,
    objectDisplayName: string,
    objectName: string,
    objectUrl: string,
};

export type NotifApiResponse = {
    data: Notification[]
};
