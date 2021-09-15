# School Messenger

## Overview
- [Connection](#connection)
- [Header](#header)
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
> ***`TODO`***

## Header
The header *must* contain `Authorization` and `User-Agent` on every request.
> **These Headers must always be added to the examples here!**

Example:
```yml
Authorization:  User <YOUR TOKEN>
User-Agent:     SchoolMessengerExamples Python3.9
```

## Account
### Account Info
You can gain information about accounts by using the `users/info`-endpoint.
```yml
GET users/info
query:          <USER NAME OR USER ID>
```
If you want to know who you are (have only your token from [here](#get-token)) you can use the `users/whoami`-endpoint.
```yml
GET users/whoami
```
All of these examples have the following response:
```yml
Status:         200
name:           <USER NAME>
id:             <USER ID>
```

### Create Account
You have to create an account to get an access token to use the messenger.
```yml
POST users/registration
name:           <YOUR NAME>
password:       <YOUR PASSWORD>
```
> **Here is *no `Authorization`* needed!**
```yml
Status:         201
Token:          <YOUR TOKEN>
```

### Delete Account
Deletes your account.
**THIS ACTION CANNOT MAKE UNDONE!!!**
```yml
DELETE users/registration
password:       <YOUR PASSWORD>
```
```yml
Status:         204
```

## Get Token
Of course, you need an access token for the `Authorization`.
There two ways to get the token:
1. by [Registration](#create-account) you can read it from the response or
2. by using the `users/me/token`-endpoint:
```yml
GET users/me/token
name:           <YOUR NAME>
password:       <YOUR PASSWORD>
```
> **Here is *no `Authorization`* needed!**
```yml
Status:         200
Token:          <TOKEN>
```
**Recommendation: you can store the token after registration ;)**

## Messages
### Send Messages
You can send messages by using the `messages`-endpoint.
```yml
POST messages
content:        Hello World!\nThis is my first message!
```
```yml
Status:         201
ID:             <MESSAGE ID>
```

### Fetch Messages
You can fetch messages by using the `messages`-endpoint.
```yml
GET messages
amount:         <MAX. AMOUNT (-1 to get all) = 20>
before:         <UTC-TIMESTAMP = -1>
after:          <UTC-TIMESTAMP = -1>
```
```yml
Status:         200
messages:       [{'id': '<MESSAGE ID>', 'content': '<MESSAGE CONTENT>', 'author': {'id': '<AUTHOR ID>', 'name': '<AUTHOR NAME>'}}, ...]
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
| 400  | Bad Request (mal formed Header)                     | No             |
| 401  | Unauthorized (missing `Authorization`/`User-Agent`) | No             |
| 403  | Forbidden                                           | No             |
| 404  | Not Found                                           | No             |
| 405  | Method Not Allowed                                  | No             |
| 406  | Not Acceptable (wrong headers)                      | No             |
| 5XX  | Internal Server Error (sorry if you see them)       | No             |
