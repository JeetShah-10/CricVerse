# Project Structure Documentation

## Overview

This document describes the refactored project structure for CricVerse, following Flask best practices for modularity and scalability.

## Directory Structure

```
cricverse/
├── app/                    # Main application package
│   ├── __init__.py         # Application factory and initialization
│   ├── models/             # Database models
│   │   ├── __init__.py
│   │   └── booking.py      # Booking-related models (Booking, Ticket, Seat)
│   ├── routes/             # API routes and endpoints
│   │   ├── __init__.py
│   │   └── booking_routes.py  # Booking-related API endpoints
│   ├── services/           # Business logic and services
│   │   ├── __init__.py
│   │   ├── booking_service.py  # Concurrency-safe booking logic
│   │   └── chatbot_service.py  # Gemini AI chatbot integration
│   ├── templates/          # HTML templates (copied from original templates/)
│   └── static/             # Static assets (CSS, JS, images) (copied from original static/)
├── config.py              # Configuration settings for different environments
├── run.py                 # Application entry point
├── requirements.txt       # Python dependencies
├── Procfile               # Production deployment configuration
├── .env                   # Environment variables (not in repo)
├── tests/                 # Unit and integration tests
│   ├── conftest.py        # Pytest configuration
│   ├── test_booking_service.py    # Tests for booking service
│   ├── test_booking_concurrency.py # Concurrency tests for booking
│   └── test_chatbot_service.py    # Tests for chatbot service
├── docs/                  # Documentation
│   └── project_structure.md       # This file
└── README.md              # Project overview and usage instructions
```

## Component Descriptions

### app/__init__.py
- Implements the application factory pattern
- Initializes Flask extensions (SQLAlchemy, LoginManager)
- Registers blueprints for different route modules
- Handles database initialization

### app/models/
- Contains SQLAlchemy ORM models
- Each model file represents a logical grouping of related models
- Models are properly linked with relationships

### app/routes/
- Contains Flask Blueprints for organizing API endpoints
- Each blueprint file manages a specific set of related endpoints
- Follows RESTful conventions where applicable

### app/services/
- Contains business logic separated from routes
- Implements concurrency-safe operations
- Handles external API integrations (e.g., Gemini AI)
- Provides clean interface for route handlers

### config.py
- Centralized configuration management
- Environment-specific settings (development, production, testing)
- Secure handling of sensitive information via environment variables

### run.py
- Entry point for the application
- Initializes the Flask app using the factory pattern
- Configures host, port, and debug settings

### tests/
- Comprehensive test suite for all components
- Unit tests for individual functions
- Integration tests for service interactions
- Concurrency tests for critical operations

## Key Improvements

1. **Modularity**: Clear separation of concerns with models, routes, and services
2. **Scalability**: Flask Blueprints allow easy addition of new features
3. **Testability**: Business logic isolated in services for easier testing
4. **Security**: Environment-based configuration for sensitive data
5. **Maintainability**: Consistent structure makes code easier to navigate
6. **Production Ready**: Proper configuration for deployment platforms

## Migration Notes

When migrating from the original structure:
1. Models were moved from a single file to modular files in `app/models/`
2. Routes were organized into Blueprints in `app/routes/`
3. Business logic was extracted to services in `app/services/`
4. Configuration was centralized in `config.py`
5. Entry point was moved to `run.py`
6. Tests were organized in the `tests/` directory
7. Documentation was moved to the `docs/` directory