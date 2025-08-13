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
              <div className="flex flex-col md:flex-row gap-6 justify-center items-center mt-6">
                <Link href="/developer-dashboard/api-docs" className="w-full md:w-1/2">
                  <Button className="w-full py-6 text-lg font-semibold shadow-md bg-gradient-to-r from-blue-500 to-blue-600 text-white hover:from-blue-600 hover:to-blue-700 transition-all">
                    API Documentation
                  </Button>
                </Link>
                <Link href="/developer-dashboard/usage-stats" className="w-full md:w-1/2">
                  <Button className="w-full py-6 text-lg font-semibold shadow-md bg-gradient-to-r from-purple-500 to-purple-600 text-white hover:from-purple-600 hover:to-purple-700 transition-all">
                    Usage Statistics
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
