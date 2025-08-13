import { serve } from '@hono/node-server';
import { logger } from "hono/logger";
import { Hono } from 'hono';
import dotenv from 'dotenv';

import authRouter from './routes/authRouter.js';
dotenv.config() 
const app = new Hono();


app.use('*', async (c, next) => {
  c.header('Access-Control-Allow-Origin', process.env.CORS_ORIGIN || '*');
  c.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  c.header('Access-Control-Allow-Headers', 'Content-Type');
  if (c.req.method === 'OPTIONS') return c.text('OK');
  await next();
});


app.use(logger());

app.get('/health', (c) => c.json({ ok: true }));

app.route("/auth", authRouter);


serve({ 
  fetch: app.fetch,
  port: Number(process.env.port) || 8787
}, (info) => {
  console.log(`Server running on http://localhost:${info.port}`);
  console.log(process.env.GMAIL_USER)
});
