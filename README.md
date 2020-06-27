# CalenderService

It lets the users of this application - 

1. to define available time slots
2. to book calender meeting with other users(of this application)


### User Authentication : 

All the APIs(except for user signup and login) mentioned below are allowed only for 
authenticated users only. The service supports both Token based and session based authentication.

For Token based authentication, the following key and value should be added in the request header - 

Authorization: Token <auth_token received from login response>
e.g 

`Authorization: Token 89a5e9c7dd1b22169d1cc5f122540b300af7eddb`


For session based authentication, along with the sessioned in the Cookie, CSRF token must be added in the 
request header - 
X-CSRFToken: <csrf token to be taken from cookie after successful login happens>
e.g 

`X-CSRFToken: 09BhDzVDH6IFsCjJbPowfDhn1lmYB04j04MWgwySQU5rnxYcGISv16TXdrXaZcCa`

### User Sign Up

**API** : https://calenderservice.herokuapp.com/api/user/sign_up/

**Method** : POST

**Request Payload** :

```
{
    "username": "test10",
    "email": "test10@test.com",
    "password": "Test@123"
}
```

**Sample Response** :

```
{
    "id": 4,
    "username": "test10",
    "email": "test10@test.com"
}
```


### User Login

**API** : https://calenderservice.herokuapp.com/api/user/login/

**Method** : POST

**Request Payload** :

```
{
    "username": "test10",
    "password": "Test@123"
}
```

**Sample Response** :

```
{
    "is_authenticated": true,
    "user": {
        "id": 4,
        "username": "test10",
        "email": "test10@test.com"
    },
    "auth_token": "89a5e9c7dd1b22169d1cc5f122540b300af7eddb"
}
```


### Define Available Time Slots For a Day

The user can define the available time slots for himself for a particular day. 

Here I have assumed the time slots to be fixed hourly time slots.

If a user does not define the available slots in a day, it is assumed that the user is available 
for the whole day

**API** : https://calenderservice.herokuapp.com/api/user/block_slots/

**Method**  : POST

**Authentication Required**: Yes

**Request Payload** : 

```
{
    "date": "2020-04-25",
    "blocked_slots": [10,15,17]
}
```

**Sample Response** :

```
{
    "response": {
        "id": 1,
        "user": {
            "id": 4,
            "username": "test10",
            "email": "test10@test.com"
        },
        "date": "2020-04-25",
        "blocked_slots": [10,15,17],
        "available_time_slots": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 16, 18, 19, 20, 21, 22, 23] ,
        "created": "2020-04-07 18:00:17",
        "modified": "2020-04-07 18:00:17"
    }
}
```

This API will return an error message if the user wants to block an time slot at which a event is already booked. e.g - 

```
{
    "err_message": [
        "There is already an event booked at time slot : 15"
    ]
}
```

### Get Available Time slot

The user can fetch the available time slots for any particular date and for any user. 

**API** : https://calenderservice.herokuapp.com/api/user/get_available_slots/

**Method**  : GET

**Authentication Required**: Yes

**Query Params** :

  *date*=<date in YYYY-MM-DD format e.g 2020-04-25> (mandatory)
  
  *user*=<user email id e.g test2@test2.com> (optional)   (if user is not given, it returns the available time 
                                                        slot of the current user)

**Sample Response**:

```
{
    "response": {
        "id": 1,
        "user": {
            "id": 4,
            "username": "test10",
            "email": "test10@test.com"
        },
        "date": "2020-04-25",
        "blocked_slots": [10,15,17],
        "available_time_slots": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 16, 18, 19, 20, 21, 22, 23] ,
        "created": "2020-04-07 18:00:17",
        "modified": "2020-04-07 18:00:17"
    }
}
```

### Book Meeting


A user can book an event with other participants and for a specific time slot.

**API** : https://calenderservice.herokuapp.com/api/event/

**Method**  : POST

**Authentication Required**: Yes

**Request Payload** :

```
{
    "title":"title",
    "time_slot": "2020-04-25 14:00:00",
    "description": "description",
    "participants": ["test@test.com", "xyz@test.com"]
}
```

Here participants is an array of attendee other than the current user(organiser)

Sample Response :

```
{
    "response": {
        "id": 1,
        "participants": [
            "test@test.com",
            "xyz@test.com",
            "test10@test.com"
        ],
        "organiser": "test10@test.com",
        "created": "2020-04-07 18:44:46",
        "modified": "2020-04-07 18:44:46",
        "title": "title",
        "description": "description",
        "time_slot": "2020-04-25 14:00:00",
        "status": "active"
    }
}
```

It will show an error message in the following cases - 
  - if the time slot is conflicting with another meeting for any participant.
    e.g 

```
          {
            "err_message": [
                "Time slot is conflicting with another event for user : test@test.com"
            ]
          }
```

  - If the time slot is not available for any participant
    e.g

```
          {
            "err_message": [
                "Time slot is not available for user : test10@test.com"
            ]
          }
```


### Fetch scheduled Meeting

The user can fetch all the scheduled future events with pagination(10 records/ page)

**API** : https://calenderservice.herokuapp.com/api/event/

**Method**  : GET

**Authentication Required**: Yes

**Sample Response**:

```
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "participants": [
                "test@test.com",
                "xyz@test.com",
                "test10@test.com"
            ],
            "organiser": "test10@test.com",
            "created": "2020-04-07 18:44:46",
            "modified": "2020-04-07 18:44:46",
            "title": "title",
            "description": "description",
            "time_slot": "2020-04-25 14:00:00",
            "status": "active"
        }
    ]
}
```


### Update Meeting

A user can update any scheduled meeting

**API** : https://calenderservice.herokuapp.com/api/event/<event_id>/

**Method** :  PUT / PATCH 

**Authentication Required**: Yes

**Request Payload**:

```
{
    "title":"title",
    "time_slot": "2020-04-25 14:00:00",
    "description": "description",
    "participants": [
                "test@test.com",
                "test10@test.com"
            ],
    "status": "active"
}
```

All the keys in request payload are not mandatory, if the request method is set as *PATCH*.

Sample Response:

```
{
    "response": {
        "id": 1,
        "participants": [
            "test@test.com",
            "test10@test.com"
        ],
        "organiser": "test10@test.com",
        "created": "2020-04-07 18:44:46",
        "modified": "2020-04-07 19:05:51",
        "title": "title",
        "description": "description",
        "time_slot": "2020-04-25 14:00:00",
        "status": "active"
    }
}
```


All the validations which are applied for meeting creation API, are applicable to update API as well.
