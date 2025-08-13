"use client";

import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { motion } from "framer-motion";

export default function UsageStatsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-grey-50 via-white to-blue-50 dark:from-navy-900 dark:via-navy-800 dark:to-navy-900 section-padding py-12">
      <div className="w-full max-w-5xl mx-auto space-y-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="text-2xl">API Usage Statistics</CardTitle>
              <p className="text-grey-600 dark:text-grey-300 mt-2">
                Track your API usage, spot trends, and optimize your integration tactics.
              </p>
            </CardHeader>
            <CardContent>
              {/* Summary stats cards, charts, endpoint table, and best practices will go here */}
              <div className="flex flex-col md:flex-row gap-6 mt-6">
                {/* Placeholder for summary cards */}
                <div className="flex-1 bg-blue-100 dark:bg-navy-700 rounded-xl p-6 text-center">
                  <div className="text-3xl font-bold text-blue-700 dark:text-blue-300">--</div>
                  <div className="text-sm text-blue-900 dark:text-blue-200 mt-2">Total API Calls</div>
                </div>
                <div className="flex-1 bg-green-100 dark:bg-navy-700 rounded-xl p-6 text-center">
                  <div className="text-3xl font-bold text-green-700 dark:text-green-300">--</div>
                  <div className="text-sm text-green-900 dark:text-green-200 mt-2">Success Rate</div>
                </div>
                <div className="flex-1 bg-red-100 dark:bg-navy-700 rounded-xl p-6 text-center">
                  <div className="text-3xl font-bold text-red-700 dark:text-red-300">--</div>
                  <div className="text-sm text-red-900 dark:text-red-200 mt-2">Error Rate</div>
                </div>
              </div>
              <div className="mt-10">
                {/* Placeholder for chart */}
                <div className="h-64 bg-grey-100 dark:bg-navy-800 rounded-xl flex items-center justify-center text-grey-400 dark:text-grey-500">
                  [API Usage Chart Coming Soon]
                </div>
              </div>
              <div className="mt-10">
                {/* Placeholder for endpoint table */}
                <div className="bg-white dark:bg-navy-800 rounded-xl p-6 shadow">
                  <div className="font-semibold text-lg mb-3">Endpoint Breakdown</div>
                  <div className="text-grey-500 dark:text-grey-400 text-sm">[Endpoint usage table coming soon]</div>
                </div>
              </div>
              <div className="mt-10">
                {/* Placeholder for best practices */}
                <div className="bg-blue-50 dark:bg-navy-700 rounded-xl p-6">
                  <div className="font-semibold text-lg mb-3 text-blue-900 dark:text-blue-200">API Usage Tips</div>
                  <ul className="list-disc pl-5 text-blue-800 dark:text-blue-300 text-sm space-y-1">
                    <li>Batch requests where possible to reduce latency and rate limit usage.</li>
                    <li>Handle errors gracefully and implement retries for transient failures.</li>
                    <li>Monitor your quota and avoid exceeding rate limits.</li>
                    <li>Use webhooks for real-time updates instead of polling.</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
