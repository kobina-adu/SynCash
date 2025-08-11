# SyncCash Orchestrator Service

The SyncCash Orchestrator is the core business logic microservice for the unified multi-wallet payment platform in Ghana. It orchestrates payment workflows across MTN MoMo, AirtelTigo, and Vodafone/Telecel Cash providers.

## Features

- **Payment Orchestration**: Manages complete payment lifecycle from initiation to confirmation
- **Provider Selection**: Smart routing based on balances, fees, and reliability
- **Fraud Detection**: Real-time risk assessment and transaction monitoring
- **Retry Logic**: Intelligent retry handling with exponential backoff
- **Event-Driven Architecture**: Async event publishing for audit and integration
- **State Management**: Persistent transaction state with comprehensive audit trails
- **Background Processing**: Celery-based async task processing
- **Health Monitoring**: Comprehensive health checks for dependencies

## Tech Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI (async web framework)
- **Database**: PostgreSQL with async SQLAlchemy
- **Cache/Queue**: Redis + Celery
- **Authentication**: BetterAuth integration (planned)
- **Containerization**: Docker + Docker Compose

## Project Structure

```
src/
├── api/v1/                 # API endpoints
│   ├── health.py          # Health check endpoints
│   └── payments.py        # Payment API endpoints
├── config/                # Configuration management
│   └── settings.py        # Pydantic settings
├── core/                  # Core infrastructure
│   ├── database.py        # Database connection
│   └── redis_client.py    # Redis client
├── models/                # Database models
│   └── transaction.py     # Transaction models
├── services/              # Business logic services
│   └── payment_orchestrator.py  # Core orchestration logic
├── tasks/                 # Background tasks
│   ├── celery_app.py      # Celery configuration
│   └── payment_tasks.py   # Payment processing tasks
└── main.py               # FastAPI application
```

## Quick Start

### 1. Environment Setup

Copy the example environment file and configure:

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 2. Start with Docker Compose

```bash
docker-compose up -d
```

This starts:
- PostgreSQL database
- Redis cache/message broker
- Orchestrator API service
- Celery worker
- Celery beat scheduler

### 3. Verify Installation

Check service health:
```bash
curl http://localhost:8000/api/v1/health/detailed
```

### 4. API Documentation

Visit the interactive API docs:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## API Endpoints

### Payment Operations

- `POST /api/v1/payments/initiate` - Initiate new payment
- `GET /api/v1/payments/{id}/status` - Get payment status
- `POST /api/v1/payments/{id}/cancel` - Cancel pending payment

### Health Checks

- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/detailed` - Detailed health with dependencies
- `GET /api/v1/health/ready` - Kubernetes readiness probe
- `GET /api/v1/health/live` - Kubernetes liveness probe

## Configuration

Key environment variables:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# Security
JWT_SECRET_KEY=your-secret-key

# Transaction Limits
MIN_TRANSACTION_AMOUNT=1.0
MAX_TRANSACTION_AMOUNT=50000.0
TRANSACTION_TIMEOUT_SECONDS=300
```

## Development

### Local Development Setup

1. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

2. **Start local services**:
```bash
# Start PostgreSQL and Redis
docker-compose up postgres redis -d
```

3. **Run the application**:
```bash
# Set environment variables
export DATABASE_URL="postgresql+asyncpg://synccash:synccash123@localhost:5432/synccash_orchestrator"
export REDIS_URL="redis://localhost:6379/0"

# Run FastAPI server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

4. **Run Celery worker** (in separate terminal):
```bash
celery -A src.tasks.celery_app worker --loglevel=info
```

5. **Run Celery beat** (in separate terminal):
```bash
celery -A src.tasks.celery_app beat --loglevel=info
```

### Testing

Run tests (when implemented):
```bash
pytest tests/
```

## Transaction States

The orchestrator manages transactions through these states:

1. **INITIATED** - Transaction created
2. **VALIDATING** - Performing validation checks
3. **PENDING** - Awaiting processing
4. **PROCESSING** - Being processed by provider
5. **CONFIRMED** - Successfully completed
6. **FAILED** - Processing failed
7. **EXPIRED** - Transaction timed out
8. **REFUNDED** - Transaction refunded
9. **CANCELLED** - Cancelled by user

## Background Tasks

- **Payment Processing**: Async payment execution
- **Transaction Validation**: Fraud checks and validation
- **Cleanup**: Remove expired transactions
- **Reporting**: Daily transaction reports

## Monitoring

The service provides comprehensive health checks and structured logging:

- Database connectivity monitoring
- Redis connectivity monitoring
- Transaction processing metrics
- Error tracking and alerting

## Security

- Input validation with Pydantic models
- Structured logging for audit trails
- Transaction state integrity
- Rate limiting (planned)
- JWT authentication integration (planned)

## Deployment

### Docker Production

```bash
# Build production image
docker build -t synccash-orchestrator:latest .

# Run with production config
docker run -d \
  --name orchestrator \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e DATABASE_URL=... \
  -e REDIS_URL=... \
  synccash-orchestrator:latest
```

### Kubernetes

Kubernetes manifests can be generated from the Docker Compose configuration.

## Contributing

1. Follow Python PEP 8 style guidelines
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Use structured logging for observability
5. Ensure async/await patterns for I/O operations

## License

Proprietary - SyncCash Platform
