# School Messenger

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

## Registration
You must be registrated to get an access token
```yml
PUT users/registration/new
name:           <YOUR NAME>
password:       <YOUR PASSWORD>
```
> **Here is *no `Authorization`* needed!**
```yml
Status Code:    200
Token:          <YOUR TOKEN>
```

## Get Token
Of course you need an access token for the `Authorization`.
There a two ways to get the token:
1. by [Registration](##Registration) you can read it from the response or
2. by using the `users/me/token`-endpoint:
```yml
GET users/me/token
name:           <YOUR NAME>
password:       <YOUR PASSWORD>
```
> **Here is *no `Authorization`* needed!**
```yml
Status Code:    200
Token:          <TOKEN>
```
**Recommendation: you can store the token after registration ;)**

## Send Messages
You can send messages by using the `messages/new`.
```yml
POST messages/new
content:        Hey everyone!\nThis is my first message!
```
```yml
Status Code:    200
ID:             <MESSAGE ID>
```

## Fetch Messages
You can fetch messages by using the `messages/fetch`.
```yml
GET messages/fetch
amount:         <MAX. AMOUNT (-1 to get all) = 20>
before:         <UTC-TIMESTAMP = -1>
after:          <UTC-TIMESTAMP = -1>
```
```yml
Status Code:    200
messages:       [{'id': '<MESSAGE ID>', 'content': '<MESSAGE CONTENT>', 'author': {'id': '<AUTHOR ID>', 'name': '<AUTHOR NAME>'}}, ...]
```
