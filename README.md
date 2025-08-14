# SynCash

Welcome to SynCash—a modular, microservices-based financial orchestration platform for secure, scalable, and observable digital payments. This README is crafted to be the definitive onboarding and technical reference, reflecting the insights and best practices discussed in this session.

---

## Table of Contents
- [Overview](#overview)
- [Business Logic](#business-logic)
- [Directory Structure](#directory-structure)
- [Microservices Architecture](#microservices-architecture)
- [Frontend](#frontend)
- [How to Run the System](#how-to-run-the-system)
- [API Usage](#api-usage)
- [Design Decisions and Trade-offs](#design-decisions-and-trade-offs)
- [Failure Handling](#failure-handling)
- [Monitoring & Observability](#monitoring--observability)
- [Environment Variables](#environment-variables)
- [Local Development Note](#local-development-note)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Resources](#resources)
- [Contact](#contact)
- [Contributors](#contributors)
- [Issue Tracking / Support](#issue-tracking--support)
- [Contribution Guidelines](#contribution-guidelines)
- [Architecture Diagram](#architecture-diagram)
- [FAQ](#faq)

---

## Overview

SynCash is designed for extensibility, security, and real-time financial operations. It leverages FastAPI (Python), Hono (Node.js/TypeScript), and Next.js (React) for backend and frontend, with robust support for monitoring, authentication, fraud detection, and real-time notifications via Kafka and Redis. The main homepage and user-facing frontend is deployed at [syncash.vercel.app](https://syncash.vercel.app).

---

## Business Logic

SynCash operates as a comprehensive financial orchestration platform with the following core business flows:

### Payment Processing Flow
1. **Payment Initiation**: Users initiate payments through the frontend (syncash-elite) or external APIs via the API Gateway.
2. **Authentication & Authorization**: API Gateway validates requests using HMAC/JWT authentication.
3. **Fraud Detection**: Orchestrator sends transaction data to the fraud detector for ML-based risk scoring.
4. **Payment Orchestration**: Based on fraud scores, orchestrator coordinates with wallet service and external payment providers.
5. **Real-time Notifications**: Notifications service publishes events via Kafka/Redis for real-time updates to subscribers.
6. **Transaction Status**: All parties receive real-time updates on payment status through webhooks or pub/sub.

### Key Business Rules
- **Fraud Prevention**: All transactions undergo ML-based fraud scoring before processing.
- **Real-time Updates**: External systems can subscribe to transaction events via Kafka/Redis.
- **Audit Trail**: Complete transaction history and status tracking for compliance.
- **Multi-channel Support**: SMS, email, and webhook notifications for different user preferences.
- **Scalable Architecture**: Each service can scale independently based on load.

---

## Directory Structure

```
/workspaces/SynCash
│
├── compose.yml
├── detector.py
├── README.md
│
├── apps/
│   ├── api-gateway/
│   ├── fraud-detector/
│   ├── notifications-service/
│   ├── orchestrator/
│   └── wallet-service/
│
├── grafana/
├── prometheus/
└── syncash-elite/
```

---

## Microservices Architecture

### Orchestrator (`apps/orchestrator`)
- **Purpose:** Central FastAPI service for payment orchestration, transaction management, and API aggregation.
- **Key Files:** `src/main.py`, `src/api/v1/`, `src/core/`, `src/models/`, `requirements.txt`
- **How to Run:**
  - Locally:
    ```sh
    cd apps/orchestrator
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
    ```
  - Docker:
    ```sh
    docker compose up orchestrator
    ```
- **Endpoints:** `/api/v1/payments/initiate`, `/api/v1/payments/{transaction_id}/status`, `/api/v1/payments/{transaction_id}/cancel`, `/api/docs`, `/api/v1/health`
- **Dependencies:** PostgreSQL, Redis

### API Gateway (`apps/api-gateway`)
- **Purpose:** Node.js/TypeScript service using Hono for routing, authentication, and OpenAPI documentation. Entry point for frontend and external API consumers.
- **Key Files:** `src/index.ts`, `src/routes/`, `src/utils/`, `drizzle.config.ts`, `Dockerfile`
- **Observability:** `/metrics`, `/health`, `/doc`, `/ui`
- **How to Run:**
  - Locally:
    ```sh
    cd apps/api-gateway
    npm install
    npm run dev
    ```
  - Docker:
    ```sh
    docker compose up api-gateway
    ```
- **Authentication:** HMAC and JWT-based

### Fraud Detector (`apps/fraud-detector`)
- **Purpose:** Python-based ML service for fraud detection and feature extraction.
- **Key Files:** `anti_fraud.py`, `anti_fraud_model_pipeline.pkl`, `feature_extraction.ipynb`, `DataAnalysis.ipynb`, `Datasets/`
- **How to Run:**
  - Locally:
    ```sh
    cd apps/fraud-detector
    python anti_fraud.py
    ```
  - Jupyter:
    ```sh
    jupyter notebook
    ```
- **Integration:** Orchestrator calls fraud detector for transaction risk scoring.

### Notifications Service (`apps/notifications-service`)
- **Purpose:** Node.js microservice for sending notifications via SMS, webhooks, and real-time pub/sub using Kafka and Redis. Enables external systems to subscribe to service events and receive updates on request/response status.
- **Key Files:** `src/index.ts`, `Dockerfile`
- **Features:**
  - **SMS, Email, Webhook Delivery:** Pluggable notification channels.
  - **Kafka & Redis Pub/Sub:** Implements event-driven architecture for real-time updates. Any client can subscribe to topics and receive notifications about service requests and responses.
  - **Webhooks:** External systems can register webhooks to receive status updates.
- **How to Run:**
  - Locally:
    ```sh
    cd apps/notifications-service
    npm install
    npm run start
    ```
  - Docker:
    ```sh
    docker compose up notifications-service
    ```
- **Integration:** Other services publish events to Kafka/Redis; notifications-service consumes and dispatches them to subscribers/webhooks.

### Wallet Service (`apps/wallet-service`)
- **Purpose:** Handles wallet operations, balances, and transactions.
- **Key Files:** See `README.md` in the service directory for details.

---

## Frontend

### Syncash Elite (`syncash-elite`)
- **Purpose:** Next.js 14+ app for user-facing dashboard, authentication, onboarding, and transaction management.
- **Key Files:** `src/app/`, `src/components/`, `src/lib/`, `public/images/`, `next.config.js`, `tailwind.config.ts`
- **How to Run:**
  - Locally:
    ```sh
    cd syncash-elite
    npm install
    npm run dev
    ```
  - Production:
    ```sh
    npm run build
    npm run start
    ```
- **Deployment:** [syncash.vercel.app](https://syncash.vercel.app)
- **Notes:** Suspense boundaries for client-side hooks, API Gateway integration, built-in observability and error handling.

---

## Monitoring & Observability

- **Prometheus:** Scrapes `/metrics` endpoints from API Gateway and other services.
---

## Environment Variables

- **Orchestrator:** `ENVIRONMENT`, `DATABASE_URL`, `REDIS_URL`, `LOG_LEVEL`, `LOG_FORMAT`
- **API Gateway:** `PORT`, `DATABASE_URL`, `JWT_SECRET`, `EMAIL_CONFIG`
- **Notifications Service:** `KAFKA_BROKER_URL`, `REDIS_URL`, `WEBHOOK_SECRET`
- **Fraud Detector:** Model and data paths as needed

---

## Local Development Note

**Important:**
If you are running the project locally with Docker, you must edit the `compose.yml` file. The current configuration uses a public IP from an EC2 server for service networking. Change all occurrences of that public IP to `localhost` or `127.0.0.1` to ensure services communicate correctly on your local machine.

**Example:**
```
-  DB_HOST: "<EC2_PUBLIC_IP>"
+  DB_HOST: "localhost"
```

Failure to update these IPs will result in connection errors between services when running locally.

---

## Best Practices

- **Microservices:** Each service is independently deployable and testable.
- **API Contracts:** Use OpenAPI/Swagger for documentation and testing.
- **Security:** HMAC/JWT authentication, environment-based secrets, and fraud detection.
- **Observability:** Metrics, health checks, logging, and event-driven notifications are mandatory for all services.
- **CI/CD:** Use Docker for consistent builds and deployments.
- **Event-Driven Architecture:** Leverage Kafka/Redis for scalable pub/sub and real-time integrations.

---

## Troubleshooting

- **Build Errors:** Check for missing Suspense boundaries, outdated Next.js config, and correct metadata exports.
- **Service Startup:** Ensure all dependencies (DB, Redis, Kafka) are running and environment variables are set.
- **API Issues:** Use Swagger UI and health endpoints for diagnostics.
- **Metrics:** Validate Prometheus scrape configs and Grafana dashboards.
- **Notifications:** Ensure Kafka/Redis brokers are reachable and webhooks are correctly registered.

---

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Hono Documentation](https://hono.dev/)
- [Prometheus](https://prometheus.io/docs/introduction/overview/)
- [Grafana](https://grafana.com/docs/)
- [Kafka](https://kafka.apache.org/documentation/)
- [Redis Pub/Sub](https://redis.io/docs/manual/pubsub/)

---

## Contact

For further questions, reach out to the project maintainers or check the internal Slack/Discord channel.

---

## Contributors

We gratefully acknowledge the following individuals and teams for their contributions to SynCash:

- kobina-adu (Project Owner)
- Gideon Atikor
- Michael-cmd-sys
- Seth Asiedu Osei
- Kelvin Semanu

Want to contribute? See the guidelines below!

---

## Issue Tracking / Support

- Issues and feature requests are managed via [GitHub Issues](https://github.com/kobina-adu/SynCash/issues).
- For urgent support, contact the maintainers or use the internal Slack/Discord channel.

---

## Contribution Guidelines

We welcome contributions from the community! To maintain code quality and consistency, please follow these guidelines:

1. Fork the repository and create your branch from `main`.
2. Write clear, concise commit messages.
3. Ensure your code passes all tests and linting checks.
4. Submit a pull request with a detailed description of your changes.
5. Participate in code reviews and respond to feedback.

For major changes, please open an issue first to discuss what you would like to change.

---

## Architecture Diagram

Below is a high-level overview of the SynCash microservices architecture:

```
+-------------------+      +-------------------+      +-------------------+
|   syncash-elite   |<---->|   API Gateway     |<---->|   Orchestrator    |
+-------------------+      +-------------------+      +-------------------+
        |                        |                        |
        v                        v                        v
+-------------------+   +-------------------+   +-------------------+
| Notifications     |   | Fraud Detector    |   | Wallet Service    |
| Service (Kafka,   |   | (ML, Python)      |   | (Balances, Txns)  |
| Redis, Webhooks)  |   +-------------------+   +-------------------+
+-------------------+
        |
        v
+-------------------+
| External Systems  |
+-------------------+
```

- **syncash-elite**: Next.js frontend
- **API Gateway**: Hono/Node.js, routing/auth/metrics
- **Orchestrator**: FastAPI, business logic
- **Notifications Service**: Kafka/Redis/webhooks for real-time updates
- **Fraud Detector**: ML-based risk scoring
- **Wallet Service**: Account and transaction management

---

## FAQ

**Q: How do I run the project locally?**
A: See the "How to Run the System" section above. Remember to update `compose.yml` for local IPs.

**Q: How do I add a new microservice?**
A: Create a new folder under `apps/`, add your Dockerfile and service code, and update `compose.yml`.

**Q: How do I subscribe to notifications?**
A: Use Kafka/Redis pub/sub or register a webhook with the notifications service.

**Q: Who do I contact for help?**
A: Use GitHub Issues or reach out via Slack/Discord.

---

---

## How to Run the System

### Using Docker Compose (Recommended)

**Run all services:**
```sh
docker compose up
```

**Run specific services:**
```sh
# Run orchestrator with dependencies (PostgreSQL, Redis)
docker compose up orchestrator

# Run API Gateway
docker compose up api-gateway

# Run frontend
docker compose up syncash-elite

# Run with monitoring stack
docker compose up orchestrator grafana prometheus
```

**Background execution:**
```sh
docker compose up -d
```

**Stop services:**
```sh
docker compose down
```

### Individual Service Setup

**Prerequisites:**
- PostgreSQL (for orchestrator, API gateway)
- Redis (for caching, pub/sub)
- Kafka (for notifications)
- Python 3.9+ (for orchestrator, fraud detector)
- Node.js 18+ (for API gateway, notifications, frontend)

**Run individual services:** (See each service section above for detailed commands)

---

## API Usage

### OpenAPI Documentation
- **Orchestrator API**: `http://localhost:8000/api/docs`
- **API Gateway**: `http://localhost:8080/ui`

### Key Endpoints

**Payment Operations:**
```bash
# Initiate Payment
curl -X POST http://localhost:8000/api/v1/payments/initiate 
  -H "Content-Type: application/json" 
  -d '{
    "amount": 100.00,
    "recipient_phone": "+233123456789",
    "recipient_name": "John Doe",
    "description": "Payment for services"
  }'

# Check Payment Status
curl -X GET http://localhost:8000/api/v1/payments/{transaction_id}/status

# Cancel Payment
curl -X POST http://localhost:8000/api/v1/payments/{transaction_id}/cancel
```

**Health Checks:**
```bash
# Orchestrator health
curl http://localhost:8000/api/v1/health

# API Gateway health
curl http://localhost:8080/health

# Metrics (Prometheus format)
curl http://localhost:8080/metrics
```

### Postman Collection
Import the OpenAPI specs from `/api/docs` or `/ui` endpoints into Postman for interactive testing.

---

## Design Decisions and Trade-offs

### Architecture Decisions

**Microservices Architecture**
- **Decision**: Decomposed system into independent services (orchestrator, API gateway, fraud detector, notifications, wallet).
- **Benefits**: Independent scaling, team autonomy, technology diversity, fault isolation.
- **Trade-offs**: Increased complexity, network latency, distributed system challenges.

**Technology Stack**
- **FastAPI (Orchestrator)**: High performance, automatic OpenAPI docs, type safety.
- **Hono (API Gateway)**: Lightweight, fast, edge-runtime compatible.
- **Next.js (Frontend)**: Server-side rendering, performance, developer experience.
- **Trade-off**: Multiple technologies increase learning curve but optimize for each use case.

**Event-Driven Architecture (Kafka/Redis)**
- **Decision**: Asynchronous communication via pub/sub for notifications and real-time updates.
- **Benefits**: Loose coupling, scalability, real-time capabilities.
- **Trade-offs**: Eventual consistency, debugging complexity, infrastructure overhead.

**Machine Learning Integration**
- **Decision**: Separate fraud detection service with pre-trained models.
- **Benefits**: Specialized ML workflows, independent scaling, model versioning.
- **Trade-offs**: Additional service complexity, model deployment challenges.

### Security Trade-offs
- **HMAC + JWT**: Balance between security and performance.
- **Service-to-service communication**: Internal network security vs. encryption overhead.

---

## Failure Handling

### Health Monitoring
- **Health Checks**: Each service exposes `/health` endpoints for load balancer and orchestration.
- **Metrics**: Prometheus metrics for performance monitoring and alerting.
- **Structured Logging**: Centralized logging with correlation IDs for distributed tracing.

### Resilience Patterns

**Circuit Breaker**
- Fraud detector failures don't block payments (graceful degradation).
- Configurable timeouts and retry policies.

**Graceful Degradation**
- If fraud detector is unavailable, payments proceed with basic validation.
- Notifications failures don't impact core payment processing.

**Data Consistency**
- Database transactions ensure payment state consistency.
- Event sourcing for audit trails and replay capabilities.

**Monitoring & Alerting**
- **Grafana Dashboards**: Real-time service health, performance metrics.
- **Prometheus Alerts**: Automated alerting for service failures, high error rates.
- **Dead Letter Queues**: Failed messages captured for manual intervention.

**Backup & Recovery**
- Database backups and point-in-time recovery.
- Stateless services enable quick restarts and horizontal scaling.

### Error Handling
- **API Errors**: Structured error responses with correlation IDs.
- **Retry Logic**: Exponential backoff for transient failures.
- **Timeout Management**: Configurable timeouts prevent cascading failures.

---

## Monitoring & Observability

---

## Onboarding Steps

1. **Clone the repository:**
   ```sh
   git clone <repo-url>
   cd SynCash
   ```
2. **Install dependencies for each service:**
   - Python: `pip install -r requirements.txt`
   - Node.js: `npm install`
3. **Set up environment variables** (see above).
4. **Start dependencies** (PostgreSQL, Redis, Kafka).
5. **Run services locally or via Docker Compose.**
6. **Access frontend at [syncash.vercel.app](https://syncash.vercel.app) or locally at `localhost:3000`.**
7. **Monitor metrics via Grafana (`localhost:3001`) and Prometheus (`localhost:9090`).**
8. **Subscribe to notifications via Kafka/Redis or register webhooks for real-time updates.**

---

## Local Development Note

**Important:**
If you are running the project locally with Docker, you must edit the `compose.yml` file. The current configuration uses a public IP from an EC2 server for service networking. Change all occurrences of that public IP to `localhost` or `127.0.0.1` to ensure services communicate correctly on your local machine.

**Example:**
```
-  DB_HOST: "<EC2_PUBLIC_IP>"
+  DB_HOST: "localhost"
```

Failure to update these IPs will result in connection errors between services when running locally.

---

## Best Practices

- **Microservices:** Each service is independently deployable and testable.
- **API Contracts:** Use OpenAPI/Swagger for documentation and testing.
- **Security:** HMAC/JWT authentication, environment-based secrets, and fraud detection.
- **Observability:** Metrics, health checks, logging, and event-driven notifications are mandatory for all services.
- **CI/CD:** Use Docker for consistent builds and deployments.
- **Event-Driven Architecture:** Leverage Kafka/Redis for scalable pub/sub and real-time integrations.

---

## Troubleshooting

- **Build Errors:** Check for missing Suspense boundaries, outdated Next.js config, and correct metadata exports.
- **Service Startup:** Ensure all dependencies (DB, Redis, Kafka) are running and environment variables are set.
- **API Issues:** Use Swagger UI and health endpoints for diagnostics.
- **Metrics:** Validate Prometheus scrape configs and Grafana dashboards.
- **Notifications:** Ensure Kafka/Redis brokers are reachable and webhooks are correctly registered.

---

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Hono Documentation](https://hono.dev/)
- [Prometheus](https://prometheus.io/docs/introduction/overview/)
- [Grafana](https://grafana.com/docs/)
- [Kafka](https://kafka.apache.org/documentation/)
- [Redis Pub/Sub](https://redis.io/docs/manual/pubsub/)

---

## Contact

For further questions, reach out to the project maintainers or check the internal Slack/Discord channel.

---

## Contributors

We gratefully acknowledge the following individuals and teams for their contributions to SynCash:

- kobina-adu (Project Owner)
- Gideon Atikor
- Michael-cmd-sys
- Seth Asiedu Osei
- Semanu Sebuava

Want to contribute? See the guidelines below!

---

## Issue Tracking / Support

- Issues and feature requests are managed via [GitHub Issues](https://github.com/kobina-adu/SynCash/issues).
- For urgent support, contact the maintainers or use the internal Slack/Discord channel.

---

## Contribution Guidelines

We welcome contributions from the community! To maintain code quality and consistency, please follow these guidelines:

1. Fork the repository and create your branch from `main`.
2. Write clear, concise commit messages.
3. Ensure your code passes all tests and linting checks.
4. Submit a pull request with a detailed description of your changes.
5. Participate in code reviews and respond to feedback.

For major changes, please open an issue first to discuss what you would like to change.

---

## Architecture Diagram

Below is a high-level overview of the SynCash microservices architecture:

```
+-------------------+      +-------------------+      +-------------------+
|   syncash-elite   |<---->|   API Gateway     |<---->|   Orchestrator    |
+-------------------+      +-------------------+      +-------------------+
        |                        |                        |
        v                        v                        v
+-------------------+   +-------------------+   +-------------------+
| Notifications     |   | Fraud Detector    |   | Wallet Service    |
| Service (Kafka,   |   | (ML, Python)      |   | (Balances, Txns)  |
| Redis, Webhooks)  |   +-------------------+   +-------------------+
+-------------------+
        |
        v
+-------------------+
| External Systems  |
+-------------------+
```

- **syncash-elite**: Next.js frontend
- **API Gateway**: Hono/Node.js, routing/auth/metrics
- **Orchestrator**: FastAPI, business logic
- **Notifications Service**: Kafka/Redis/webhooks for real-time updates
- **Fraud Detector**: ML-based risk scoring
- **Wallet Service**: Account and transaction management

---

## FAQ

**Q: How do I run the project locally?**
A: See the onboarding steps above. Remember to update `compose.yml` for local IPs.

**Q: How do I add a new microservice?**
A: Create a new folder under `apps/`, add your Dockerfile and service code, and update `compose.yml`.

**Q: How do I subscribe to notifications?**
A: Use Kafka/Redis pub/sub or register a webhook with the notifications service.

**Q: Who do I contact for help?**
A: Use GitHub Issues or reach out via Slack/Discord.

---

## Shoutout

Special thanks to **Heidelberg Materials-digitalhub-Ghana** for giving us the opportunity to push ourselves to the limit and discover the unique joy in learning something new. From exploring AWS services, deploying containers to the cloud, and embracing best practices as a team, we see ourselves as winners—regardless of what the results might say. Your support and encouragement have been instrumental in our growth and success.

---

**Welcome to SynCash! Build, test, and ship with confidence.**
