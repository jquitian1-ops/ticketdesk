# TicketDesk Enterprise - Backend

FastAPI + SQLAlchemy backend for AI-powered candidate screening.

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15
- pip/venv

### Setup

1. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Setup database**:
```bash
# Create database and user
createdb ticketdesk_dev
createuser ticketdesk_user
psql -d ticketdesk_dev -c "ALTER USER ticketdesk_user WITH PASSWORD 'dev_password';"
psql -d ticketdesk_dev -c "GRANT ALL PRIVILEGES ON DATABASE ticketdesk_dev TO ticketdesk_user;"

# Run migrations
alembic upgrade head
```

4. **Start development server**:
```bash
uvicorn src.main:app --reload
```

Server runs at http://localhost:8000

## API Documentation

- **OpenAPI (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/unit/test_user_aggregate.py -v

# Run in watch mode
pytest --looponfail
```

## Code Quality

```bash
# Format code
black src/ tests/

# Lint
pylint src/
flake8 src/

# Type checking
mypy src/

# Security check
bandit -r src/
```

## Project Structure

```
backend/
├── src/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── config.py         # Settings
│   ├── models/           # SQLAlchemy models
│   ├── services/         # Business logic
│   ├── api/              # API routes
│   ├── schemas/          # Pydantic models
│   └── middleware/       # Middlewares
├── tests/
│   ├── unit/            # Unit tests
│   ├── integration/      # Integration tests
│   └── conftest.py
├── migrations/          # Alembic migrations
├── requirements.txt     # Python dependencies
└── Dockerfile
```

## Semana 1 Tasks

- **T1.1**: Database Schema (PostgreSQL)
- **T1.2**: User Aggregate + Repository
- **T1.3**: Authentication Service (JWT)
- **T1.4**: RBAC (Role-Based Access Control)
- **T1.5**: Audit Logging Framework (LGPD)
- **T1.6**: Docker Setup + CI/CD

See `../Estación 6/docs/tasks/` for detailed task files.

## Environment Variables

Create `.env` file in backend root:

```
DATABASE_URL=postgresql://ticketdesk_user:dev_password@localhost:5432/ticketdesk_dev
DATABASE_SSL=false
JWT_SECRET_KEY=your-secret-key-here
LOG_LEVEL=INFO
```

Never commit `.env` file!

## Docker

Build and run with Docker Compose:

```bash
cd ..
docker-compose up -d backend

# View logs
docker-compose logs -f backend

# Access PostgreSQL
docker-compose exec postgres psql -U ticketdesk_user -d ticketdesk_dev

# Stop
docker-compose down
```

## Documentation

- See `../CLAUDE.md` for development guide
- See `../Estación 6/DESIGN.md` for architecture
- See `../Estación 6/VALIDATION-FRAMEWORK.md` for quality standards
