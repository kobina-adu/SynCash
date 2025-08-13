import { redis } from './redisClient.js';
import axios from 'axios';

type eventType = 
            | "COMPLETED"
            | "PENDING"
            | "CANCELLED"


export async function registerWebhook(userId: string, url: string) {
  await redis.set(`webhook:${userId}`, url);
}

export async function triggerWebhook(userId: string, event: eventType) {
  const url = await redis.get(`webhook:${userId}`);
  if (url) {
    try {
      await axios.post(url, event, { timeout: 5000 });
      console.log(`Webhook sent to ${url}`);
    } catch (err: any) {
      console.error(`Failed to send webhook to ${url}:`, err.message);
    }
  }
}

module.exports = { registerWebhook, triggerWebhook };
