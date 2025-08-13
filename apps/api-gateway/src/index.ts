import { serve } from '@hono/node-server';
import { logger } from "hono/logger";
import { Hono } from 'hono';
import dotenv from 'dotenv';

import authRouter from './routes/authRouter.js';


dotenv.config() 
const app = new Hono();


app.use(logger());


app.route("/auth", authRouter);


serve({ 
  fetch: app.fetch,
  port: Number(process.env.port) || 8787
}, (info) => {
  console.log(`Server running on http://localhost:${info.port}`);
  console.log(process.env.GMAIL_USER)
});
