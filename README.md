# CricVerse

A comprehensive stadium management and ticket booking platform specifically designed for Big Bash League (BBL) cricket. CricVerse serves as a one-stop destination for cricket fans to book tickets, explore team information, manage stadium experiences including parking and food court orders, and stay updated with match schedules and player statistics.

## Features

*   **BBL Team Management:** Complete profiles for all 8 Big Bash League teams with players, statistics, and achievements.
*   **Stadium Directory:** Comprehensive venue information with interactive seating charts and amenities.
*   **Smart Booking System:** Seamless ticket booking with seat selection, parking, and food court integration.
*   **Administrative Dashboard:** Complete management tools for stadiums, matches, and events.
*   **Stadium Owner Analytics:** Performance metrics, revenue tracking, and operational insights.
*   **AI Assistant:** Intelligent chatbot for booking assistance and match information.
*   **Vegetarian Food Court:** Comprehensive vegetarian menu with dietary information.
*   **Secure Authentication:** Multi-role access control for users, administrators, and stadium owners.

## Project Structure

The project follows a modular Flask application structure:

```
cricverse/
├── app/                    # Main application package
│   ├── __init__.py         # Application factory
│   ├── models/             # Database models
│   ├── routes/             # API routes and endpoints
│   ├── services/           # Business logic and services
│   ├── templates/          # HTML templates
│   └── static/             # Static assets (CSS, JS, images)
├── config.py              # Configuration settings
├── run.py                 # Application entry point
├── requirements.txt       # Python dependencies
├── Procfile               # Production deployment configuration
├── .env                   # Environment variables (not in repo)
├── tests/                 # Unit and integration tests
├── docs/                  # Documentation
└── README.md              # This file
```

## New Features

### 1. Concurrency-Safe Booking Logic
- Atomic booking operations using SQLAlchemy transactions
- SELECT... FOR UPDATE to prevent double-booking
- Comprehensive error handling and rollback mechanisms

### 2. Gemini AI Chatbot Integration
- Natural language processing for customer queries
- Graceful error handling for API failures
- Service-layer implementation for modularity

### 3. Enhanced Security
- Secure session management
- Environment-based configuration
- Production-ready security headers

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/cricverse.git
    cd cricverse
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up the database:**
    - Create a `.env` file based on `.env.example`
    - Add your `DATABASE_URL` and `SECRET_KEY`
    - Run the application to initialize the database

5.  **Configure AI services (optional):**
    - Add `GOOGLE_API_KEY` for Gemini AI features

## Usage

1.  **Run the application:**
    ```bash
    python run.py
    ```

2.  **Access the application:**
    - Open your web browser and go to `http://127.0.0.1:5000`

## API Endpoints

### Booking Service
- `POST /api/booking/book-seat` - Book a seat for an event

### Chatbot Service
- Service function `ask_gemini(prompt)` - Get AI response for a prompt

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

Or run individual test files:
```bash
python tests/test_chatbot_service.py
```

## Deployment

The application is configured for deployment on platforms like Heroku or Railway:

1.  **Set environment variables:**
    - `DATABASE_URL`
    - `SECRET_KEY`
    - `GOOGLE_API_KEY` (for AI features)

2.  **Deploy using the Procfile:**
    ```
    web: gunicorn run:app
    ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.