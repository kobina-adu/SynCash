import { serve } from '@hono/node-server';
import { swaggerUI } from '@hono/swagger-ui';
import { logger } from "hono/logger";
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import promClient from "prom-client";

import dotenv from 'dotenv';
import authRouter from './routes/authRouter.js';
import { auth } from './utils/auth.js';

dotenv.config();

// Prometheus metrics setup
const collectDefaultMetrics = promClient.collectDefaultMetrics;
collectDefaultMetrics();

const openApiDoc = {
  openapi: "3.0.0",
  info: {
    title: "API Documentation",
    version: "1.0.0",
    description: "API documentation for your service",
  },
  paths: {
    "/health": {
      get: {
        summary: "Health check",
        responses: {
          "200": {
            description: "OK",
          },
        },
      },
    },

    "/ui": {
      get: {
        summary: "Swagger UI",
        responses: {
          "200": {
            description: "OK",
          },
        },
      },
    },

  },
};


const app = new Hono();

app.use(cors({
  origin: ["localhost:3000", "localhost:8080", "*"], // * is added here for now to allow devs be able to access this as well
  allowHeaders: ["Content-Type", "Authorization"],
  allowMethods: ["POST", "GET", "OPTIONS"],
  exposeHeaders: ["Content-Length"],
  maxAge: 600,
  credentials: true,
}));

app.use(logger());

app.on(["GET", "POST"], "/api/auth/**", (c) => auth.handler(c.req.raw));

// Serve the OpenAPI document
app.get("/doc", (c) => c.json(openApiDoc));

// Use the middleware to serve Swagger UI at /ui
app.get('/ui', swaggerUI({ url: '/doc' }))

app.get("/health", (c) => c.text("OK"));

// Metrics endpoint
app.get('/metrics', async (c) => {
  return c.text(
    await promClient.register.metrics(),
    200,
    { 'Content-Type': promClient.register.contentType }
  );
});

serve({ 
  fetch: app.fetch,
  port: Number(process.env.PORT) || 8080
}, (info) => {
  console.log(`Server running on http://localhost:${info.port}`);
});
