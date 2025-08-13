import { OpenAPIHono } from "@hono/zod-openapi";
import { publicApi } from "./routes/public.";

// Create a combined app for OpenAPI
export const openapiApp = new OpenAPIHono();

openapiApp.route("/", publicApi);

// OpenAPI JSON
openapiApp.doc("/openapi.json", {
  openapi: "3.0.0",
  info: {
    title: "Notifications Service",
    version: "1.0.0",
    description:
      "Webhooks + transaction state for the payment platform. All public routes assume requests pass through the API Gateway which injects `x-merchant-id`."
  },
  tags: [
    { name: "Webhook", description: "Register & manage webhooks" },
    { name: "Transactions", description: "Query transaction state" }
  ]
});

// Minimal Swagger UI (served from CDN)
const html = (specUrl: string) => `<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Notifications Service API Docs</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist/swagger-ui.css" />
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist/swagger-ui-bundle.js"></script>
  <script>
    window.onload = () => {
      SwaggerUIBundle({ url: '${specUrl}', dom_id: '#swagger-ui' });
    };
  </script>
</body>
</html>`;

openapiApp.get("/docs", (c) =>
  c.html(html(new URL("/openapi.json", c.req.url).toString()))
);
