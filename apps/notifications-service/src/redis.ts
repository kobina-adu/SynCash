import Redis from "ioredis";
import { env } from "./env";

export const redis = new Redis(env.REDIS_URL, {
  lazyConnect: false,
  maxRetriesPerRequest: null,
  enableReadyCheck: true
});

// Keys
export const keyWebhook = (merchantId: string) => `webhook:${merchantId}`;
export const keyTxn = (txnId: string) => `txn:${txnId}`;
export const keyDeliveryList = (txnId: string) => `delivery:${txnId}`; // list of JSON logs
