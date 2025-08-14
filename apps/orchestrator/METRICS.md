# SyncCash Orchestrator - Prometheus Metrics Implementation

## Overview

This document describes the comprehensive Prometheus metrics implementation for the SyncCash Orchestrator service, providing enterprise-grade observability and monitoring capabilities.

## Metrics Categories

### 1. Payment Processing Metrics

- **`synccash_payment_requests_total`** - Total payment requests received
  - Labels: `user_id`, `status`, `provider`, `risk_level`
- **`synccash_payment_processing_duration_seconds`** - Payment processing time
  - Labels: `status`, `provider`, `risk_level`
- **`synccash_transaction_status_changes_total`** - Transaction status changes
  - Labels: `from_status`, `to_status`, `provider`
- **`synccash_transaction_amounts_ghs`** - Transaction amount distribution
  - Labels: `provider`, `status`

### 2. Fraud Detection Metrics

- **`synccash_fraud_checks_total`** - Fraud detection checks performed
  - Labels: `risk_level`, `result`
- **`synccash_fraud_scores`** - Fraud risk score distribution
  - Labels: `risk_level`
- **`synccash_blocked_transactions_total`** - Blocked transactions
  - Labels: `reason`, `risk_level`

### 3. Provider Metrics

- **`synccash_provider_requests_total`** - Provider API requests
  - Labels: `provider`, `status`, `operation`
- **`synccash_provider_response_time_seconds`** - Provider response times
  - Labels: `provider`, `status`
- **`synccash_provider_errors_total`** - Provider errors
  - Labels: `provider`, `error_type`, `error_code`

### 4. System Health Metrics

- **`synccash_active_transactions`** - Active transaction count
  - Labels: `status`
- **`synccash_database_connections`** - Database connection count
  - Labels: `pool_status`
- **`synccash_redis_operations_total`** - Redis operations
  - Labels: `operation`, `status`

### 5. API Metrics

- **`synccash_http_requests_total`** - HTTP requests received
  - Labels: `method`, `endpoint`, `status_code`
- **`synccash_http_request_duration_seconds`** - HTTP request duration
  - Labels: `method`, `endpoint`, `status_code`

### 6. Business Metrics

- **`synccash_daily_transaction_volume_ghs`** - Daily transaction volume
  - Labels: `provider`
- **`synccash_daily_transaction_count`** - Daily transaction count
  - Labels: `provider`, `status`
- **`synccash_success_rate_percentage`** - Success rate percentage
  - Labels: `provider`, `time_window`

### 7. Error Tracking

- **`synccash_application_errors_total`** - Application errors
  - Labels: `error_type`, `component`, `severity`
- **`synccash_validation_errors_total`** - Validation errors
  - Labels: `field`, `error_type`

### 8. Resilience Metrics

- **`synccash_retry_attempts_total`** - Retry attempts
  - Labels: `operation`, `provider`, `attempt_number`
- **`synccash_circuit_breaker_state`** - Circuit breaker states
  - Labels: `service`

## API Endpoints

### Metrics Endpoints

- **`GET /api/v1/metrics`** - Prometheus metrics endpoint (Prometheus format)
- **`GET /api/v1/metrics/health`** - Metrics system health check
- **`GET /api/v1/metrics/summary`** - Human-readable metrics summary

## Implementation Details

### Core Components

1. **`src/core/metrics.py`** - Prometheus metrics definitions and collector
2. **`src/core/middleware.py`** - HTTP metrics collection middleware
3. **`src/api/v1/metrics.py`** - Metrics API endpoints

### Integration Points

- **Payment Orchestrator** - Automatic metrics collection for all payment operations
- **HTTP Middleware** - Request/response metrics for all API endpoints
- **Database Operations** - Connection pool and query metrics
- **Redis Operations** - Cache and session metrics

### Grafana Dashboard

A comprehensive Grafana dashboard is provided at `grafana/dashboards/synccash-orchestrator.json` with:

- Payment request rate visualization
- Success rate gauges
- Processing duration histograms
- Active transaction distribution
- Daily volume tracking
- Error rate monitoring

## Configuration

### Prometheus Configuration

The Prometheus configuration (`prometheus/prometheus.yml`) includes:

- Orchestrator service scraping at `/api/v1/metrics`
- 10-second scrape interval for real-time monitoring
- Integration with system exporters (Node, Redis)

### Docker Compose Setup

The monitoring stack includes:

- **Prometheus** - Metrics collection and storage
- **Grafana** - Visualization and alerting
- **Node Exporter** - System metrics
- **Redis Exporter** - Redis metrics

## Usage

### Starting the Monitoring Stack

```bash
docker-compose up -d prometheus grafana node-exporter redis-exporter
```

### Accessing Services

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:9091 (admin/synccash123)
- **Orchestrator Metrics**: http://localhost:8000/api/v1/metrics

### Example Queries

```promql
# Payment success rate
rate(synccash_payment_requests_total{status="confirmed"}[5m]) / rate(synccash_payment_requests_total[5m]) * 100

# Average processing time
rate(synccash_payment_processing_duration_seconds_sum[5m]) / rate(synccash_payment_processing_duration_seconds_count[5m])

# Error rate by component
rate(synccash_application_errors_total[5m])
```

## Alerting

The metrics support alerting on:

- High error rates
- Slow processing times
- Low success rates
- System resource issues
- Provider failures

## Security Considerations

- User IDs are anonymized in metrics (first 8 characters + ***)
- No sensitive payment data is exposed in metrics
- Metrics endpoint can be secured with authentication if needed

## Performance Impact

- Minimal performance overhead (< 1ms per request)
- Efficient memory usage with histogram buckets
- Asynchronous metrics collection where possible

## Troubleshooting

### Common Issues

1. **Metrics not appearing**: Check Prometheus target health at http://localhost:9090/targets
2. **Dashboard not loading**: Verify Grafana datasource configuration
3. **High memory usage**: Adjust histogram buckets or retention settings

### Debug Endpoints

- **`/api/v1/metrics/health`** - Check metrics system status
- **`/api/v1/metrics/summary`** - View current metrics summary
- **`/health/detailed`** - Overall system health including metrics

## Future Enhancements

- Custom alerting rules
- Additional business metrics
- Provider-specific dashboards
- Mobile app metrics integration
- Real-time fraud detection metrics
