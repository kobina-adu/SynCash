"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { User, Code2 } from "lucide-react";

export default function ChooseRolePage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gradient-to-br from-grey-50 via-white to-blue-50 dark:from-navy-900 dark:via-navy-800 dark:to-navy-900 flex items-center justify-center section-padding py-12">
      <div className="w-full max-w-lg mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <Card>
            <CardHeader className="text-center">
              <CardTitle className="text-2xl">Get Started</CardTitle>
              <p className="text-grey-600 dark:text-grey-300 mt-2">
                Choose how you want to use SyncCash Elite
              </p>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col md:flex-row gap-6 mt-6">
                <Button
                  className="flex-1 flex flex-col items-center py-8 bg-gradient-to-br from-blue-500 to-blue-600 text-white hover:from-blue-600 hover:to-blue-700 shadow-lg rounded-xl"
                  onClick={() => router.push("/auth/signup?role=user")}
                >
                  <User size={40} className="mb-2" />
                  <span className="text-lg font-semibold">Regular User</span>
                  <span className="text-xs mt-1">Personal finance, wallets & payments</span>
                </Button>
                <Button
                  className="flex-1 flex flex-col items-center py-8 bg-gradient-to-br from-purple-500 to-purple-600 text-white hover:from-purple-600 hover:to-purple-700 shadow-lg rounded-xl"
                  onClick={() => router.push("/auth/signup?role=developer")}
                >
                  <Code2 size={40} className="mb-2" />
                  <span className="text-lg font-semibold">Developer</span>
                  <span className="text-xs mt-1">Integrate APIs, manage apps, build solutions</span>
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
