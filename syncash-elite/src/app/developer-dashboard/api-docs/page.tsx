"use client";

import { useEffect } from "react";

// Placeholder: Replace with your Swagger docs URL
const SWAGGER_URL = "https://your-swagger-url-here.com/docs";

export default function ApiDocsRedirect() {
  useEffect(() => {
    // Redirect to Swagger docs
    window.location.href = SWAGGER_URL;
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-grey-50 dark:bg-navy-900">
      <div className="text-center">
        <div className="text-2xl font-bold mb-2">Redirecting to API Documentation...</div>
        <div className="text-grey-500 dark:text-grey-300">If you are not redirected, <a href={SWAGGER_URL} className="text-blue-600 underline">click here</a>.</div>
      </div>
    </div>
  );
}
