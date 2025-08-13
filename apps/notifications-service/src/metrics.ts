import client from "prom-client";
import type { Context } from "hono";

// Default system metrics
client.collectDefaultMetrics();

export const metricsRegistry = client.register;

// Custom metrics
export const webhookSentCounter = new client.Counter({
  name: "webhook_sent_total",
  help: "Total number of webhook delivery attempts",
  labelNames: ["merchantId", "status"] as const
});

export const webhookLatencyHistogram = new client.Histogram({
  name: "webhook_latency_ms",
  help: "Latency of webhook deliveries in ms",
  buckets: [50, 100, 200, 500, 1000, 2000, 5000]
});

export const kafkaEventsCounter = new client.Counter({
  name: "kafka_events_consumed_total",
  help: "Total number of Kafka events consumed",
  labelNames: ["topic"] as const
});

export const metricsHandler = async (_c: Context) => {
  const body = await metricsRegistry.metrics();
  return new Response(body, {
    status: 200,
    headers: { "Content-Type": metricsRegistry.contentType }
  });
};
