import { z } from "zod";
//import { OpenAPIHono, createRoute, z as zopen } from "@hono/zod-openapi";
import { registerWebhook, deleteWebhook, getWebhook, getTxnState } from "../webhook.js";
import { WebhookRegistration } from "../types.js";

/**
 * NOTE: Requests here arrive THROUGH your API-Gateway.
 * We assume the gateway validated the user and injects merchant identity
 * via a header like: x-merchant-id
 */
const MerchantHeader = z.string().min(1).openapi({
  param: { name: "x-merchant-id", in: "header" },
  example: "merchant_123"
});

export const publicApi = new OpenAPIHono();

/** Register webhook */
publicApi.openapi(
  createRoute({
    method: "post",
    path: "/webhooks",
    request: {
      headers: zopen.object({ "x-merchant-id": MerchantHeader }),
      body: {
        content: {
          "application/json": {
            schema: zopen.object({
              url: zopen.string().url(),
              secret: zopen.string().min(16),
              events: zopen.array(zopen.string()).optional()
            })
          }
        }
      }
    },
    responses: {
      200: {
        description: "Registered",
        content: { "application/json": { schema: zopen.object({ ok: zopen.boolean() }) } }
      }
    },
    tags: ["Webhook"]
  }),
  async (c) => {
    const merchantId = c.req.header("x-merchant-id")!;
    const body = await c.req.json();
    const input = WebhookRegistration.parse({ merchantId, ...body });
    const res = await registerWebhook(input);
    return c.json(res);
  }
);

/** Delete webhook */
publicApi.openapi(
  createRoute({
    method: "delete",
    path: "/webhooks",
    request: { headers: zopen.object({ "x-merchant-id": MerchantHeader }) },
    responses: {
      200: {
        description: "Deleted",
        content: { "application/json": { schema: zopen.object({ ok: zopen.boolean() }) } }
      }
    },
    tags: ["Webhook"]
  }),
  async (c) => {
    const merchantId = c.req.header("x-merchant-id")!;
    const res = await deleteWebhook(merchantId);
    return c.json(res);
  }
);

/** Get my webhook registration */
publicApi.openapi(
  createRoute({
    method: "get",
    path: "/webhooks/me",
    request: { headers: zopen.object({ "x-merchant-id": MerchantHeader }) },
    responses: {
      200: {
        description: "Current registration",
        content: {
          "application/json": {
            schema: zopen
              .object({
                merchantId: zopen.string(),
                url: zopen.string(),
                secret: zopen.string(),
                events: zopen.array(zopen.string())
              })
              .or(zopen.null())
          }
        }
      }
    },
    tags: ["Webhook"]
  }),
  async (c) => {
    const merchantId = c.req.header("x-merchant-id")!;
    const reg = await getWebhook(merchantId);
    return c.json(reg);
  }
);

/** Get a transaction state */
publicApi.openapi(
  createRoute({
    method: "get",
    path: "/transactions/{transactionId}",
    request: {
      headers: zopen.object({ "x-merchant-id": MerchantHeader }),
      params: zopen.object({ transactionId: zopen.string().min(1) })
    },
    responses: {
      200: {
        description: "Transaction state",
        content: {
          "application/json": {
            schema: zopen
              .object({
                transactionId: zopen.string(),
                merchantId: zopen.string(),
                status: zopen.string(),
                updatedAt: zopen.string(),
                lastEvent: zopen.any().optional()
              })
              .or(zopen.null())
          }
        }
      }
    },
    tags: ["Transactions"]
  }),
  async (c) => {
    const { transactionId } = c.req.valid("param");
    const state = await getTxnState(transactionId);
    return c.json(state);
  }
);
