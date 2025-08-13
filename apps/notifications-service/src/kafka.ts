import { Kafka, logLevel, type EachMessagePayload } from "kafkajs";
//import { env } from "./env.js";
import { PaymentEvent } from "./types.js";
import { persistTxnState, getWebhook, triggerWebhookDelivery } from "./webhook.js";
import { kafkaEventsCounter } from "./metrics.js";

// const brokers = env.KAFKA_BROKERS.split(",").map(s => s.trim());

export const kafka = new Kafka({
  clientId: process.env.KAFKA_CLIENT_ID,
  brokers,
  logLevel: logLevel.INFO
});

export const consumer = kafka.consumer({ groupId: process.env.KAFKA_GROUP_ID! });

export async function startKafkaConsumer() {
  await consumer.connect();

  // Topics you emit from the payments domain
  const topics = ["payment.initiated", "payment.pending", "payment.completed", "payment.failed", "payment.refunded"];
  for (const t of topics) {
    await consumer.subscribe({ topic: t, fromBeginning: false });
  }

  await consumer.run({
    eachMessage: async ({ topic, message }: EachMessagePayload) => {
      kafkaEventsCounter.labels({ topic }).inc();

      if (!message.value) return;
      const json = JSON.parse(message.value.toString());
      const evt = PaymentEvent.parse(json);

      // Persist state
      await persistTxnState(evt);

      // Load webhook config for merchant
      const reg = await getWebhook(evt.merchantId);
      if (!reg) return; // merchant hasn't registered a webhook

      // Optional: filter by event type if merchant subscribed to subsets
      const eventType = `payment.${evt.status}`;
      if (!reg.events.includes(eventType)) return;

      // Deliver webhook
      await triggerWebhookDelivery(reg, evt);
    }
  });
}
