# API Endpoints Documentation

## Overview

This document describes the API endpoints available in the CricVerse application.

## Authentication

Most endpoints require authentication. Users must log in to obtain a session cookie that is used for subsequent requests.

## Booking Service

### Book Seat

Books a seat for a specific event.

**Endpoint:** `POST /api/booking/book-seat`

**Request Body:**
```json
{
  "seat_id": 123,
  "event_id": 456,
  "customer_id": 789
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Seat booked successfully",
  "booking_id": 1,
  "ticket_id": 101
}
```

**Response (Error - Seat not found):**
```json
{
  "success": false,
  "message": "Seat not found"
}
```

**Response (Error - Seat already booked):**
```json
{
  "success": false,
  "message": "Seat is already booked for this event"
}
```

**Response (Error - General):**
```json
{
  "success": false,
  "message": "An error occurred: <error details>"
}
```

## Chatbot Service

The chatbot service is not directly exposed as an API endpoint but is used by the application's chat interface.

### Ask Gemini

Function to get a response from the Gemini AI.

**Function:** `ask_gemini(prompt)`

**Parameters:**
- `prompt` (string): The user's question or prompt

**Returns:**
- `string`: The AI's response or a fallback message if the API call fails

**Example:**
```python
response = ask_gemini("What are the upcoming matches?")
print(response)
```

## Error Handling

All API endpoints return appropriate HTTP status codes:

- `200`: Success
- `400`: Bad Request (missing parameters, validation errors)
- `401`: Unauthorized (authentication required)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found (resource not found)
- `500`: Internal Server Error (unexpected server error)

Error responses follow a consistent format:
```json
{
  "success": false,
  "message": "Description of the error"
}
```

## Rate Limiting

API endpoints may be rate-limited to prevent abuse. If a rate limit is exceeded, the API will return a `429 Too Many Requests` status code.

## Security

All API endpoints use secure session management and CSRF protection where appropriate. Sensitive operations require proper authentication and authorization.