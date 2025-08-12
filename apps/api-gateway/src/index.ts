import { serve } from '@hono/node-server';
import { logger } from "hono/logger";
import { Hono } from 'hono';
import { auth } from './utils/auth.js';

const app = new Hono();
const authRouter = new Hono();

app.use(logger());

// Example route: user signup
authRouter.post('/signup', async (c) => {
  logger.info("User signup initiated");
  const { email, password }: { email: string; password: string;} = await c.req.json();
  const result = await auth.api.signUpEmail({
    body: {
      name: email,
      email: email,
      password: password
    },
    asResponse: true,
  });

  logger.info("User signup completed", result);
  return c.json(result);
});

authRouter.post("/change-password", async (c) => {
  logger.info("User change password initiated");
  const { email, oldPassword, newPassword }: { email: string; oldPassword: string; newPassword: string; } = await c.req.json();
  const result = await auth.api.changePassword({
    body: {
      email: email,
      oldPassword: oldPassword,
      newPassword: newPassword
    },
    asResponse: true
  });
  logger.info("User change password completed", result);
  return c.json(result);
});


// Example route: user login
app.post('/login', async (c) => {
  logger.info("User login initiated");
  const body = await c.req.json();
  const result = await auth.api.signInEmail({
    body: {
      email: body.email,
      password: body.password
    },
    asResponse: true
  });
  logger.info("User login completed", result);
  return c.json(result);
});

app.route("/auth", authRouter);

serve({ 
  fetch: app.fetch,
  port: 3001
}, (info) => {
  console.log(`Server running on http://localhost:${info.port}`);
});
