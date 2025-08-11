import { serve } from '@hono/node-server'
import { Hono } from 'hono'
import { auth } from "./utils/auth.js"

const app = new Hono();

// Middleware for better auth for authentication

// Set up security for internal microservices communication


// Midddleware re-routes to respective services

app.get('/', (c) => {
  return c.text('Hello Hono!');
});

// const response = await auth.api.signInEmail({
//     body: {
//         email,
//         password
//     },
//     asResponse: true // returns a response object instead of data
// });

serve({
  fetch: app.fetch,
  port: 3000
}, (info) => {
  console.log(`Server is running on http://localhost:${info.port}`)
})
