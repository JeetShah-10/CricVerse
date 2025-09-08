# WARP.md

This file provides guidance to WARP (warp.dev) when working with the CricVerse codebase - a comprehensive Big Bash League (BBL) cricket stadium management and booking platform.

## Common Development Commands

### Application Setup and Running
```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up database environment (create cricverse.env or .env file)
# Add DATABASE_URL=postgresql://postgres:<password>@localhost:5432/cricverse_db
# Add SECRET_KEY=your-secret-key-here

# Create PostgreSQL database if using PostgreSQL
createdb cricverse_db

# Run the Flask application
python app.py

# Run with explicit Flask development server
flask run --debug

# Access application at http://127.0.0.1:5000
```

### Database Management
```bash
# Initialize/reset database with sample data
python seed.py

# Run application tests
python test_app.py

# Drop and recreate database tables (via seed.py)
python seed.py  # This will DROP CASCADE all tables and recreate them
```

### Frontend Dependencies
```bash
# Install frontend dependencies (Bootstrap)
npm install

# Bootstrap is included via package.json
```

## Architecture Overview

### Technology Stack
- **Backend**: Flask (Python web framework)
- **Database**: PostgreSQL (primary) or SQLite (fallback)
- **ORM**: Flask-SQLAlchemy
- **Authentication**: Flask-Login with Werkzeug password hashing
- **Frontend**: HTML templates with Jinja2, Bootstrap 5.3.3
- **Environment**: python-dotenv for configuration

### Core Application Structure

**Single File Architecture**: The application follows a monolithic Flask pattern with everything in `app.py` (~1536 lines). This is a complete stadium management system with:

**Database Models** (Lines 40-348):
- `Stadium` - Core venue entity with capacity, location, features
- `Team` & `Player` - Sports team management
- `Event` & `Match` - Event scheduling and match results  
- `Customer` - User management with role-based access (`customer`, `admin`, `stadium_owner`)
- `Ticket`, `Booking`, `Payment` - Ticketing system with seat selection
- `Concession`, `MenuItem`, `Order` - Food service management
- `Parking`, `ParkingBooking` - Parking reservation system
- Junction tables: `StadiumAdmin`, `StadiumOwner`, `EventUmpire`

**Authentication & Authorization** (Lines 349-415):
- Role-based decorators: `@admin_required`, `@customer_required`, `@stadium_owner_required`
- Stadium-specific admin access via `@stadium_admin_required()`
- Flask-Login integration with `Customer` model as `UserMixin`

**Route Organization**:
- **Admin Routes** (Lines 426-971): Complete admin dashboard with stadium management, analytics, CRUD operations
- **Public Routes** (Lines 972-1456): Customer-facing pages for browsing, booking, concessions
- **Authentication Routes**: Login/register/logout with role-based redirects

### Key Architectural Patterns

**Role-Based Access Control**: 
- Three primary roles: `customer`, `admin`, `stadium_owner`
- Stadium admins can only manage stadiums they're assigned to via `StadiumAdmin` junction table
- Admin permission checks happen at route level and within templates

**Booking System Architecture**:
- `Booking` represents a transaction (one booking can have multiple tickets)
- `Ticket` links to specific seats and events
- `Payment` is 1:1 with booking for transaction tracking
- Seat selection uses dynamic availability checking

**Database Configuration**:
- Environment-based config with fallbacks (DATABASE_URL → SQLite)
- Prefers `stadium.env` over `.env` for configuration
- Auto-initialization on startup via `init_db()`

### Development Patterns

**Template Organization**: All HTML templates in `/templates/` with clear naming:
- `admin_*` - Admin interface templates
- Base templates: `base.html`, `admin_base.html`
- Feature-specific: `seat_selection.html`, `concession_menu.html`

**Error Handling**: Basic Flask flash messaging throughout with try/catch blocks for database operations

**Testing**: Simple test suite in `test_app.py` covering:
- Application startup and database initialization
- Model relationships and methods
- Basic route accessibility

## Environment Configuration

### Required Environment Variables
Create `cricverse.env` or `.env` file:
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/cricverse_db
SECRET_KEY=your-secret-key-change-in-production
```

### Database Fallback
If `DATABASE_URL` is not set, application automatically falls back to SQLite (`sqlite:///cricverse.db`)

## Testing and Debugging

### Running Tests
```bash
python test_app.py  # Comprehensive application tests
```

### Development Features
- `TEMPLATES_AUTO_RELOAD = True` - Templates reload automatically
- `debug=True` in main application run
- Extensive console logging for database operations

### Sample Data
The `seed.py` script provides complete sample data including:
- 8 BBL (Big Bash League) teams with logos
- 8 corresponding stadiums across Australia
- Sample matches, players, concessions, parking
- Test users for each role (admin@example.com, owner@example.com, user@example.com)

## Role-Specific Functionality

### Admin Users
- Create and manage stadiums (assigned automatically on creation)
- Add events, concessions, parking zones, and bulk seat creation
- View analytics and booking statistics per stadium
- Multi-stadium support via `StadiumAdmin` assignments

### Stadium Owners
- Basic stadium ownership tracking via `StadiumOwner` junction table
- Separate dashboard (minimal implementation)

### Customers  
- Browse stadiums, events, teams, and players
- Book tickets with interactive seat selection
- Order from concession menus
- Reserve parking spaces
- Personal dashboard showing all bookings and orders

## Important Notes

- **Monolithic Design**: Entire application logic in single `app.py` file
- **Database Relationships**: Complex foreign key relationships require careful migration handling
- **Authentication**: Uses Flask-Login sessions (not JWT)
- **Payment Processing**: Simulated payment system with transaction ID generation
- **Seat Management**: Dynamic seat availability calculated per event
- **Bootstrap Integration**: Frontend styling via Bootstrap 5.3.3 (npm managed)
