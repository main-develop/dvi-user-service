## Overview

## Authentication

## Errors

This section describes the error responses that appear in every operation with some explanation. Therefore, they are excluded from the schema to avoid redundancy.

### 405 Method Not Allowed

This is returned when an endpoint is called with an unexpected HTTP method. For example, if updating a user's email requires a `POST` request and a `GET` is issued instead, this error is returned. Here's how the response would look:

```
{
  "type": "client_error",
  "errors": [
    {
      "code": "method_not_allowed",
      "message": "Method \"get\" not allowed.",
      "field": null
    }
  ]
}
```

### 406 Not Acceptable

This error is returned if the `Accept` header is submitted and contains a value other than `application/json`. Here's how the response would look:

```
{
  "type": "client_error",
  "errors": [
    {
      "code": "not_acceptable",
      "message": "Could not satisfy the request Accept header.",
      "field": null
    }
  ]
}
```

### 415 Unsupported Media Type

This error is returned when the request content type is not `json`. Here's how the response would look:

```
{
  "type": "client_error",
  "errors": [
    {
      "code": "unsupported_media_type",
      "message": "Unsupported media type \"application/json\" in request.",
      "field": null
    }
  ]
}
```

### 500 Internal Server Error

This error is returned when the API server encounters an unexpected error. Here's how the response would look:

```
{
  "type": "server_error",
  "errors": [
    {
      "code": "error",
      "message": "A server error occurred.",
      "field": null
    }
  ]
}
```
