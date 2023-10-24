// TYPES
import type {UserObject} from "../../customtypes/customtypes";

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
    objectName: string,
};

export type NotifApiResponse = {
    data: Notification[]
};
