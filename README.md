# BCal - Calendar Booking Application

A full-fledged calendar booking application similar to Calendly, built with FastAPI, React, and PostgreSQL.

## Features

- **User Authentication**: JWT-based authentication system
- **Calendar Management**: Users can set their availability and manage calendar settings
- **Booking System**: Public booking interface for scheduling appointments
- **Admin Dashboard**: Comprehensive dashboard for managing bookings and users
- **API Documentation**: Complete Swagger/OpenAPI documentation
- **Production Ready**: Docker containers for both development and production

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL**: Primary database
- **JWT**: Authentication tokens
- **Pydantic**: Data validation
- **Alembic**: Database migrations

### Frontend
- **React**: User interface framework
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **React Router**: Navigation
- **Axios**: HTTP client

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Reverse proxy (production)

## Quick Start

### Development
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Production
```bash
# Start production environment
docker-compose -f docker-compose.prod.yml up --build

# Access the application
# Frontend: http://localhost
# Backend API: http://localhost/api
# API Docs: http://localhost/api/docs
```

## Default Admin Credentials

On first startup, the application automatically creates a default admin user:

- **Email**: `admin@bcal.com`
- **Password**: `admin123`

⚠️ **Important**: Please change these credentials immediately after your first login for security purposes.

## Project Structure

```
BCal/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configurations
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic
│   ├── alembic/            # Database migrations
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── types/          # TypeScript types
│   └── package.json        # Node dependencies
├── docker-compose.dev.yml  # Development environment
├── docker-compose.prod.yml # Production environment
└── CHANGELOG.md           # Development changelog
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh JWT token

### Users
- `GET /api/users/me` - Get current user profile
- `PUT /api/users/me` - Update user profile
- `GET /api/users/{user_id}/availability` - Get user availability

### Calendar
- `GET /api/calendar/availability` - Get available time slots
- `POST /api/calendar/availability` - Set availability
- `DELETE /api/calendar/availability/{id}` - Remove availability

### Bookings
- `POST /api/bookings` - Create a booking
- `GET /api/bookings` - Get user's bookings
- `GET /api/bookings/{id}` - Get specific booking
- `PUT /api/bookings/{id}` - Update booking
- `DELETE /api/bookings/{id}` - Cancel booking

### Admin
- `GET /api/admin/bookings` - Get all bookings (admin only)
- `GET /api/admin/users` - Get all users (admin only)
- `GET /api/admin/dashboard` - Get dashboard stats (admin only)

## Environment Variables

### Backend
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time

### Frontend
- `REACT_APP_API_URL`: Backend API URL

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License
