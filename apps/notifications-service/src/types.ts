import { z } from "zod";

// Payment event from Kafka
export const PaymentEvent = z.object({
  transactionId: z.string(),
  merchantId: z.string(),
  status: z.enum(["initiated", "pending", "completed", "failed", "refunded"]),
  amount: z.number().nonnegative(),
  currency: z.string().min(3).max(10),
  occurredAt: z.string(),
  // Add any other fields you emit from your payments service:
  metadata: z.record(z.string(), z.string()).optional()
});

export type PaymentEvent = z.infer<typeof PaymentEvent>;

// Webhook registration
export const WebhookRegistration = z.object({
  merchantId: z.string(),
  url: z.string().url(),
  // Secret used for HMAC signing of payloads
  secret: z.string().min(16),
  // Limit subscription to specific event types if you want
  events: z.array(z.string()).default(["payment.completed", "payment.failed", "payment.refunded"])
});

export type WebhookRegistration = z.infer<typeof WebhookRegistration>;

// Query state response
export const TxnState = z.object({
  transactionId: z.string(),
  merchantId: z.string(),
  status: z.string(),
  updatedAt: z.string(),
  lastEvent: PaymentEvent.optional()
});

export type TxnState = z.infer<typeof TxnState>;
