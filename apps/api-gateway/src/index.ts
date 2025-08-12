import { serve } from '@hono/node-server';
import { logger } from "hono/logger";
import { Hono } from 'hono';
import { auth } from './utils/auth.js';

const app = new Hono();
const authRouter = new Hono();

app.use(logger());

// Example route: user signup
authRouter.post('/signup', async (c) => {
  const { email, password }: { email: string; password: string;} = await c.req.json();
  const result = await auth.api.signUpEmail({
    body: {
      name: email,
      email: email,
      password: password
    },
    asResponse: true,
  });
  return c.json(result);
});

authRouter.post("/change-password")
// Example route: user login
app.post('/login', async (c) => {
  const body = await c.req.json();
  const result = await auth.api.signInEmail({
    body: {
      email: body.email,
      password: body.password
    },
    asResponse: true
  });
  return c.json(result);
});

app.route("/auth", authRouter);
serve({ 
  fetch: app.fetch,
  port: 3000
}, (info) => {
  console.log(`Server running on http://localhost:${info.port}`);
});
