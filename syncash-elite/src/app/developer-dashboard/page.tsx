"use client";

import React from "react";
import { motion } from "framer-motion";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import Link from "next/link";

export default function DeveloperDashboard() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-grey-50 via-white to-blue-50 dark:from-navy-900 dark:via-navy-800 dark:to-navy-900 flex items-center justify-center section-padding py-12">
      <div className="w-full max-w-3xl space-y-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <Card variant="premium">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl">Developer Dashboard</CardTitle>
              <p className="text-grey-600 dark:text-grey-300 mt-2">
                Welcome, Developer! Here are your tools and resources.
              </p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Link href="/developer-dashboard/api-docs">
                  <Button className="w-full" variant="secondary">API Documentation</Button>
                </Link>
                <Link href="/developer-dashboard/logs">
                  <Button className="w-full" variant="secondary">System Logs</Button>
                </Link>
                <Link href="/developer-dashboard/users">
                  <Button className="w-full" variant="secondary">User Management</Button>
                </Link>
                <Link href="/developer-dashboard/metrics">
                  <Button className="w-full" variant="secondary">App Metrics</Button>
                </Link>
                <Link href="/developer-dashboard/config">
                  <Button className="w-full" variant="secondary">Configuration</Button>
                </Link>
                <Link href="/developer-dashboard/db-tools">
                  <Button className="w-full" variant="secondary">Database Tools</Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
