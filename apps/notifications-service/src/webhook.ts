import { createHmac, timingSafeEqual } from "crypto";
import { redis, keyWebhook, keyDeliveryList, keyTxn } from "./redis.js";
import { WebhookRegistration, PaymentEvent, TxnState } from "./types.js";
import { webhookSentCounter, webhookLatencyHistogram } from "./metrics.js";
import { env } from "./env.js";
import { setTimeout as delay } from "timers/promises";

type DeliveryResult = {
  status: number;
  body?: unknown;
};

export async function registerWebhook(input: WebhookRegistration) {
  const existing = await redis.get(keyWebhook(input.merchantId));
  const payload = JSON.stringify(input);
  if (existing) {
    await redis.set(keyWebhook(input.merchantId), payload);
  } else {
    await redis.set(keyWebhook(input.merchantId), payload);
  }
  return { ok: true };
}

export async function deleteWebhook(merchantId: string) {
  await redis.del(keyWebhook(merchantId));
  return { ok: true };
}

export async function getWebhook(merchantId: string) {
  const v = await redis.get(keyWebhook(merchantId));
  if (!v) return null;
  return WebhookRegistration.parse(JSON.parse(v));
}

export function signPayload(secret: string, body: string) {
  return createHmac("sha256", secret).update(body).digest("hex");
}

export function verifySignature(secret: string, body: string, signature: string) {
  const expected = signPayload(secret, body);
  // Safe compare
  const a = Buffer.from(expected, "utf8");
  const b = Buffer.from(signature, "utf8");
  return a.length === b.length && timingSafeEqual(a, b);
}

export async function persistTxnState(evt: PaymentEvent) {
  const state: TxnState = {
    transactionId: evt.transactionId,
    merchantId: evt.merchantId,
    status: evt.status,
    updatedAt: new Date().toISOString(),
    lastEvent: evt
  };
  await redis.set(keyTxn(evt.transactionId), JSON.stringify(state));
  return state;
}

export async function getTxnState(txnId: string) {
  const v = await redis.get(keyTxn(txnId));
  return v ? (JSON.parse(v) as TxnState) : null;
}

async function deliverOnce(url: string, body: string, headers: Record<string, string>, timeoutMs: number): Promise<DeliveryResult> {
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      method: "POST",
      body,
      headers: { "Content-Type": "application/json", ...headers },
      signal: ac.signal
    });
    const status = res.status;
    let data: unknown;
    try { data = await res.json(); } catch { /* ignore */ }
    return { status, body: data };
  } finally {
    clearTimeout(t);
  }
}

/**
 * Deliver with retries + exponential backoff
 */
export async function triggerWebhookDelivery(reg: WebhookRegistration, evt: PaymentEvent) {
  const body = JSON.stringify(evt);
  const signature = signPayload(reg.secret, body);
  const headers = {
    "X-Webhook-Signature": signature,
    "X-Event-Type": `payment.${evt.status}`,
    "X-Transaction-Id": evt.transactionId
  };
  const timeout = Number(env.WEBHOOK_DEFAULT_TIMEOUT_MS);

  const start = Date.now();
  const maxAttempts = 5;
  let attempt = 0;
  let lastStatus = 0;

  while (attempt < maxAttempts) {
    attempt++;
    try {
      const res = await deliverOnce(reg.url, body, headers, timeout);
      lastStatus = res.status;
      // Store delivery log
      await redis.lpush(
        keyDeliveryList(evt.transactionId),
        JSON.stringify({
          ts: new Date().toISOString(),
          attempt,
          status: res.status,
          responseBody: res.body ?? null
        })
      );
      if (res.status >= 200 && res.status < 300) {
        webhookSentCounter.labels({ merchantId: reg.merchantId, status: "success" }).inc();
        webhookLatencyHistogram.observe(Date.now() - start);
        return true;
      }
    } catch (e: any) {
      await redis.lpush(
        keyDeliveryList(evt.transactionId),
        JSON.stringify({
          ts: new Date().toISOString(),
          attempt,
          status: "network_error",
          error: e?.message ?? "unknown"
        })
      );
    }
    
    webhookSentCounter.labels({ merchantId: reg.merchantId, status: "retry" }).inc();
    const backoff = Math.min(2000 * Math.pow(2, attempt - 1), 15000);
    await delay(backoff);
  }

  webhookSentCounter.labels({ merchantId: reg.merchantId, status: "failed" }).inc();
  webhookLatencyHistogram.observe(Date.now() - start);
  return false;
}
