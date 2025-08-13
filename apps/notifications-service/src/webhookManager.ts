import redis from './redisClient.js';
import axios from 'axios';

async function registerWebhook(userId, url) {
  await redis.set(`webhook:${userId}`, url);
}

async function triggerWebhook(userId, event) {
  const url = await redis.get(`webhook:${userId}`);
  if (url) {
    try {
      await axios.post(url, event, { timeout: 5000 });
      console.log(`Webhook sent to ${url}`);
    } catch (err) {
      console.error(`Failed to send webhook to ${url}:`, err.message);
    }
  }
}

module.exports = { registerWebhook, triggerWebhook };
