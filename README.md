# Neurula Health - Backend API

FastAPI-based backend for Neurula Health mobile and web applications.

## Features

- ✅ **Authentication System**: JWT-based auth with OTP verification
- ✅ **Patient Management**: Complete patient profile management
- ✅ **Doctor Directory**: Search and filter doctors
- ✅ **Security**: Password hashing, JWT tokens, Emirates ID validation
- ✅ **Database**: PostgreSQL with SQLAlchemy ORM
- ✅ **Caching**: Redis for OTP and session management
- ✅ **API Documentation**: Auto-generated OpenAPI/Swagger docs
- ✅ **Migrations**: Alembic for database migrations
- ✅ **Testing**: Pytest test suite

## Technology Stack

- **Framework**: FastAPI 0.109+
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0 (async)
- **Cache**: Redis 7+
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt
- **Migrations**: Alembic
- **Testing**: pytest, pytest-asyncio
- **Server**: Uvicorn

## Project Structure

```
neurula-patient-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration settings
│   ├── database.py             # Database setup
│   ├── dependencies.py         # Dependency injection
│   │
│   ├── api/                    # API endpoints
│   │   ├── v1/
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── patients.py     # Patient endpoints
│   │   │   └── doctors.py      # Doctor endpoints
│   │   └── router.py           # API router
│   │
│   ├── core/                   # Core functionality
│   │   ├── security.py         # JWT, password hashing
│   │   ├── middleware.py       # Custom middleware
│   │   └── exceptions.py       # Custom exceptions
│   │
│   ├── models/                 # Database models
│   │   ├── user.py
│   │   ├── patient.py
│   │   └── doctor.py
│   │
│   ├── schemas/                # Pydantic schemas
│   │   ├── auth.py
│   │   ├── patient.py
│   │   └── doctor.py
│   │
│   ├── services/               # Business logic
│   │   ├── auth_service.py
│   │   ├── otp_service.py
│   │   ├── patient_service.py
│   │   └── doctor_service.py
│   │
│   └── utils/                  # Utilities
│       ├── redis_client.py
│       └── validators.py
│
├── tests/                      # Test suite
│   ├── conftest.py
│   └── test_auth.py
│
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
│
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
├── alembic.ini
├── pytest.ini
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### 1. Create Virtual Environment

```bash
cd neurula-patient-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt

# For development (includes testing tools)
pip install -r requirements-dev.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and update the following:

```env
# Database
DATABASE_URL=postgresql+asyncpg://neurula:neurula_password@localhost:5432/neurula_db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT Secret (generate a secure random string)
JWT_SECRET_KEY=your-super-secret-key-min-32-characters-long

# AES Encryption Key (32 bytes)
AES_ENCRYPTION_KEY=your-32-byte-aes-encryption-key-here
```

### 4. Setup PostgreSQL

```bash
# Create database
psql -U postgres
CREATE DATABASE neurula_db;
CREATE USER neurula WITH PASSWORD 'neurula_password';
GRANT ALL PRIVILEGES ON DATABASE neurula_db TO neurula;
\q
```

### 5. Setup Redis

```bash
# Install and start Redis
# On Ubuntu/Debian:
sudo apt-get install redis-server
sudo systemctl start redis

# On macOS:
brew install redis
brew services start redis

# On Windows:
# Download from https://github.com/tporadowski/redis/releases
```

### 6. Run Database Migrations

```bash
# Initialize Alembic (first time only)
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 7. Run the Application

```bash
# Development mode (with auto-reload)
python app/main.py

# Or with uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### 8. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/verify-otp` | Verify OTP |
| POST | `/api/v1/auth/resend-otp` | Resend OTP |
| POST | `/api/v1/auth/login` | User login |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/change-password` | Change password |
| GET | `/api/v1/auth/me` | Get current user |
| POST | `/api/v1/auth/logout` | Logout user |

### Patients

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/patients/me` | Get my profile |
| GET | `/api/v1/patients/{id}` | Get patient by ID |
| PUT | `/api/v1/patients/me` | Update my profile |
| GET | `/api/v1/patients/me/profile-completion` | Get profile completion |
| DELETE | `/api/v1/patients/me` | Delete my profile |

### Doctors

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/doctors` | Search doctors |
| GET | `/api/v1/doctors/{id}` | Get doctor by ID |
| GET | `/api/v1/doctors/specialties` | Get all specialties |

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/` | API info |

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

### View Coverage Report

```bash
# Open HTML coverage report
open htmlcov/index.html
```

## Development Workflow

### Create Database Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Code Quality

```bash
# Format code with black
black app/

# Sort imports with isort
isort app/

# Lint with flake8
flake8 app/

# Type checking with mypy
mypy app/
```

## API Usage Examples

### 1. Register New User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "+971501234567",
    "password": "SecurePass123!",
    "registration_method": "manual",
    "date_of_birth": "1990-01-15",
    "gender": "Male",
    "nationality": "UAE",
    "height": 175,
    "weight": 70,
    "emirate": "Dubai"
  }'
```

### 2. Verify OTP

```bash
curl -X POST "http://localhost:8000/api/v1/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "otp": "123456"
  }'
```

### 3. Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john@example.com",
    "password": "SecurePass123!",
    "remember_me": false
  }'
```

### 4. Get Patient Profile (Authenticated)

```bash
curl -X GET "http://localhost:8000/api/v1/patients/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. Search Doctors

```bash
curl -X GET "http://localhost:8000/api/v1/doctors?specialty=Cardiology&page=1&limit=10"
```

## Security Features

- **Password Hashing**: bcrypt with configurable rounds
- **JWT Tokens**: Access tokens (15 min) + Refresh tokens (7 days)
- **OTP Verification**: 6-digit OTP with expiry and rate limiting
- **Emirates ID Validation**: Format validation (784-XXXX-XXXXXXX-X)
- **Input Sanitization**: XSS and injection prevention
- **CORS**: Configurable allowed origins
- **Rate Limiting**: Per-endpoint rate limits
- **Soft Delete**: Data retention with soft delete

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `JWT_SECRET_KEY` | Secret key for JWT signing | Required (32+ chars) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry | `15` |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiry | `7` |
| `OTP_LENGTH` | OTP code length | `6` |
| `OTP_EXPIRE_MINUTES` | OTP expiry time | `5` |
| `PASSWORD_MIN_LENGTH` | Minimum password length | `8` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Troubleshooting

### Database Connection Error

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -U neurula -d neurula_db -h localhost
```

### Redis Connection Error

```bash
# Check Redis is running
redis-cli ping
# Should return: PONG
```

### Migration Issues

```bash
# Reset database (WARNING: Deletes all data)
alembic downgrade base
alembic upgrade head
```

## Next Steps

The following features are planned for future implementation:

- [ ] Appointment booking system
- [ ] Payment integration (Stripe, Network UAE)
- [ ] File upload service (MinIO/S3)
- [ ] Real-time chat (WebSocket)
- [ ] Video consultation (WebRTC/Twilio)
- [ ] Notification service (Email/SMS)
- [ ] NABIDH integration
- [ ] Analytics and reporting
- [ ] Admin dashboard

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `pytest`
4. Format code: `black app/`
5. Submit a pull request

## License

Copyright © 2025 Neurula Health. All rights reserved.

## Support

For issues and questions:
- GitHub Issues: [neurula-patient-backend/issues]
- Email: support@neurula.health
