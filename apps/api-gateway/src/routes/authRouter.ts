import { logger } from "hono/logger";
import { Hono } from 'hono';
import dotenv from "dotenv";

import { auth } from '../utils/auth.js';

dotenv.config();

type userSignUpType = {
    email: string;
    name: string;
    password: string;
    callbackURL: string;
    rememberMe?: boolean;
}

const authRouter = new Hono();

authRouter.use(logger());

// Example route: user signup
authRouter.post('/signup', async (c) => {
  const { email, password, name, callbackURL, rememberMe }: userSignUpType = await c.req.json();
  const result = await auth.api.signUpEmail({
    body: {
      name: email,
      email,
      password,
      callbackURL,
      rememberMe
    },
    asResponse: true,
  });

  return c.json(result);
});


authRouter.post("/change-password", async (c) => {
  const { email, currentPassword, newPassword }: { email: string; currentPassword: string; newPassword: string; } = await c.req.json();
  const result = await auth.api.changePassword({
    body: {
      currentPassword,
      newPassword,
      revokeOtherSessions: true,
    },
    asResponse: true
  });
  return c.json(result);
});


authRouter.post('/login', async (c) => {
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


// Request OTP (for sign-in)
authRouter.post('/auth/send-otp', async (c) => {
  const { email } = await c.req.json();
  await auth.sendOTP({ email, type: 'sign-in' });
  return c.json({ ok: true });
});

// Verify OTP
authRouter.post('/auth/verify-otp', async (c) => {
  const { email, otp } = await c.req.json();
  const result = await auth.verifyOTP({ email, otp, type: 'sign-in' });
  if (result.success) {
    // Generate session or token if necessary (you can return a JWT or session cookie)
    return c.json({ ok: true, message: 'OTP verified' });
  }
  return c.json({ ok: false, message: 'Invalid OTP' }, 400);
});

export default authRouter