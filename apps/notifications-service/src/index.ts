import { Hono } from 'hono'
import { serve } from '@hono/node-server'
import dotenv from 'dotenv'
dotenv.config()

const app = new Hono()

// In-memory store for demo (use DB in production)
const webhooks = new Map()

// Middleware to check internal service token
const internalAuth = async (c, next) => {
  const token = c.req.header('x-service-token')
  if (token !== process.env.INTERNAL_TOKEN) {
    return c.json({ error: 'Unauthorized' }, 401)
  }
  await next()
}

// Register webhook
app.post('/register-webhook', async (c) => {
  const { merchantId, url } = await c.req.json()
  if (!merchantId || !url) {
    return c.json({ error: 'Missing fields' }, 400)
  }
  webhooks.set(merchantId, url)
  return c.json({ message: 'Webhook registered' })
})

// Internal endpoint to send webhook notification
app.post('/send', internalAuth, async (c) => {
  const { merchantId, payload } = await c.req.json()
  const url = webhooks.get(merchantId)

  if (!url) {
    return c.json({ error: 'No webhook for merchant' }, 404)
  }

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    return c.json({ message: 'Notification sent', status: res.status })
  } catch (err) {
    return c.json({ error: 'Failed to send webhook', details: err.message }, 500)
  }
})

// Health check
app.get('/health', (c) => c.text('OK'))

serve(app)
