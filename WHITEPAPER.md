# School Messenger

## Overview
- [Connection](#connection)
    - [Versioning](#versions)
        - [v0](#v0)
        - [v1](#v1)
        - [v2](#v2)
- [Communication (Client-Server)](#communication)
    - [Request](#request)
    - [Response](#response)
- [Account](#account)
    - [Info](#account-info)
    - [Create](#create-account)
    - [Delete](#delete-account)
- [Get Token](#get-token)
- [Messages](#messages)
    - [Send](#send-messages)
    - [Fetch](#fetch-messages)
- [ID](#id)
    - [Technical](#id-technical)
    - [Types](#id-types)
- [Status Codes](#status-codes)

## Connection
You can connect by just calling the ˝REST˝full-API.
The HOST and PORT must be provided by the host, but by default you can use the PORT `3333`.
> Note: at the moment the connection goes over **`HTTP`** and *not* `HTTPS`

### Versions
The API is split into versions to keep "old" clients running, even if the structure of the response ect have changed.

#### v0
`v0` has all here listed endpoints in the way they're mentioned.
> Note: This version has default responses because it isn't connected to a database. But it still checks all data!

#### v1
`v1` is the first version and even with `v0`, but is connected to a database and can be used for communication.

#### v2
`v2` is like `v1`, but *all keys in (json-) response* are ***lowercase***.

## Communication
### Request
The header *must* contain `Authorization` and `User-Agent` on every request.
> **These Headers must always be added to the examples here!**

Example:
```yml
Authorization:  User <YOUR TOKEN>
User-Agent:     SchoolMessengerExamples Python3.9
```

### Response
The response-content is a `application/json`-response and always provides the field `message`.
This field is provided to make sure, a status-code won't be misinterpreted
(e.g. `404` can mean `Page Not Found` or `Entry Not Found`).
> *All other fields are described in the sections below where you can see how requests and responses are build.*

## Account
### Account Info
You can gain information about accounts by using the `users/info`-endpoint.
> Versions: `v0`, `v1`, `v2`
```yml
GET users/info
Query:          <USER NAME OR USER ID>
```
If you want to know who you are (have only your token from [here](#get-token)) you can use the `users/whoami`-endpoint.
> Versions: `v0`, `v1`, `v2`
```yml
GET users/whoami
```
All of these examples have the following response:

> Versions: `v0`, `v1`, `v2`

> Status: 200
```json
{
  "name": "<USER NAME>",
  "id": "<USER ID>"
}
```

### Create Account
You have to create an account to get an access token to use the messenger.
> Versions: `v0`, `v1`, `v2`
```yml
POST users/registration
Name:           <YOUR NAME>
Password:       <YOUR PASSWORD>
```
> **Here is *no `Authorization`* needed!**

> **NOTE: `name` can't be numeric-only and must contain at least one letter!**

> Versions: `v0`, `v1`

> Status: 201
```json
{
  "Token": "<TOKEN>"
}
```

> Versions: `v2`

> Status: 201
```json
{
  "token": "<TOKEN>"
}
```

### Delete Account
Deletes your account.
**THIS ACTION CANNOT MAKE UNDONE!!!**
> Versions: `v0`, `v1`, `v2`
```yml
DELETE users/registration
Password:       <YOUR PASSWORD>
```

> Status: 204


## Get Token
Of course, you need an access token for the `Authorization`.
There two ways to get the token:
1. by [Registration](#create-account) you can read it from the response or
2. by using the `users/me/token`-endpoint:
> Versions: `v0`, `v1`, `v2`
```yml
GET users/me/token
Name:           <YOUR NAME>
Password:       <YOUR PASSWORD>
```
> **Here is *no `Authorization`* needed!**

> Versions: `v0`, `v1`

> Status: 200
```json
{
  "Token": "<TOKEN>"
}
```

> Versions: `v2`

> Status: 200
```json
{
  "token": "<TOKEN>"
}
```

**Recommendation: you can store the token after registration ;)**

## Messages
### Send Messages
You can send messages by using the `messages`-endpoint.
> Versions: `v0`, `v1`, `v2`
```yml
POST messages
Content:        Hello World!
```

> Versions: `v0`, `v1`, `v2`

> Status: 201
```json
{
  "id": "<MESSAGE ID>"
}
```

### Fetch Messages
You can fetch messages by using the `messages`-endpoint.
> Versions: `v0`, `v1`, `v2`
```yml
GET messages
Amount:         <MAX. AMOUNT (-1 to get all) = 20>
Before:         <UTC-TIMESTAMP = -1>
After:          <UTC-TIMESTAMP = -1>
```

> Versions: `v0`, `v1`, `v2`

> Status: 200
```json
{
  "messages": [
    {
      "id": "<MESSAGE ID>",
      "content": "<MESSAGE CONTENT>",
      "author": {
        "id": "<AUTHOR ID>",
        "name": "<AUTHOR NAME>"
      }
    },
    ...
  ]
}
```

## ID
The IDs used in the messenger.

### ID Technical
- unsigned 64 bit integer

| Field           | Timestamp (UTC)                                  | Type                          | Increment                        |
|:----------------|:-------------------------------------------------|:------------------------------|:---------------------------------|
| **Binary**      | 000000000000000000000000000000000000000000000000 | 00000                         | 00000000000                      |
| **Bits**        | 63 to 15                                         | 15 to 11                      | 11 to 0                          |
| **Total Bits**  | 48                                               | 5                             | 11                               |
| **Description** | ms since `EPOCH`                                 | the type (message, user, ...) | increment to prevent doubled IDs |
| **Retrieval**   | ( `ID` >> 15 ) + `EPOCH`                         | (`ID` & F800 ) >> 0x1F        | `ID` & 0x7FF                     |

The above-mentioned `EPOCH` is `1609455600000` (UNIX timestamp from *`01/01/2021 00:00`*)

### ID Types
| Value | Type      |
|:-----:|:----------|
| **0** | undefined |
| **1** | user      |
| **2** | message   |

## Status Codes
All used status codes by the messenger:

| Code | Meaning                                             | Everything OK? |
|:----:|:----------------------------------------------------|:--------------:|
| 200  | OK                                                  | Yes            |
| 201  | Created                                             | Yes            |
| 204  | No Content (nothing to say...)                      | Yes            |
| 400  | Bad Request (mal formed or missing Header)          | No             |
| 401  | Unauthorized (missing `Authorization`/`User-Agent`) | No             |
| 403  | Forbidden                                           | No             |
| 404  | Not Found                                           | No             |
| 405  | Method Not Allowed                                  | No             |
| 5XX  | Internal Server Error (sorry if you see them)       | No             |
