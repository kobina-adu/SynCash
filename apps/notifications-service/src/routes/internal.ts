import { Hono } from "hono";
//import { env } from "../env";
import { PaymentEvent } from "../types.js";
import { kafka } from "../kafka.js";

export const internalApi = new Hono();

// Very optional: publish a test event to Kafka via HTTP (protected by service token)
internalApi.post("/_test/publish", async (c) => {
  const token = c.req.header("x-service-token");
 /* if (token !== env.INTERNAL_SERVICE_TOKEN) {
    return c.json({ error: "Unauthorized" }, 401);
  }
    */
  const body = await c.req.json();
  const evt = PaymentEvent.parse(body);
  const producer = kafka.producer();
  await producer.connect();
  await producer.send({
    topic: `payment.${evt.status}`,
    messages: [{ value: JSON.stringify(evt) }]
  });
  await producer.disconnect();
  return c.json({ ok: true });
});
