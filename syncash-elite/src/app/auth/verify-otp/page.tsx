'use client'

import React, { useState, useEffect, Suspense } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { 
  Phone,
  ArrowLeft,
  CheckCircle,
  RefreshCw
} from 'lucide-react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import toast from 'react-hot-toast'

function VerifyOtpForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const phoneNumber = searchParams.get('phone') || ''
  
  const [otpCode, setOtpCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [resendLoading, setResendLoading] = useState(false)
  const [timer, setTimer] = useState(60)
  const [canResend, setCanResend] = useState(false)

  // Timer countdown
  useEffect(() => {
    if (timer > 0) {
      const interval = setTimeout(() => setTimer(timer - 1), 1000)
      return () => clearTimeout(interval)
    } else {
      setCanResend(true)
    }
  }, [timer])

  const handleVerifyOtp = async () => {
    if (!otpCode || otpCode.length !== 6) {
      toast.error('Please enter a valid 6-digit OTP')
      return
    }

    setLoading(true)
    try {
      // Simulate OTP verification
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      toast.success('Account verified successfully!')
      router.push('/dashboard')
    } catch (error) {
      toast.error('Invalid OTP. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleResendOtp = async () => {
    setResendLoading(true)
    try {
      // Simulate resend OTP
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      setTimer(60)
      setCanResend(false)
      toast.success('New OTP sent successfully!')
    } catch (error) {
      toast.error('Failed to resend OTP')
    } finally {
      setResendLoading(false)
    }
  }

  const handleOtpChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, 6)
    setOtpCode(value)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-grey-50 via-white to-blue-50 dark:from-navy-900 dark:via-navy-800 dark:to-navy-900 flex items-center justify-center section-padding py-12">
      <div className="w-full max-w-md">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-8"
        >
          <Link href="/" className="inline-flex items-center gap-3 mb-6">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-700 rounded-2xl flex items-center justify-center shadow-medium">
              <span className="text-white font-bold text-xl">SC</span>
            </div>
            <span className="text-2xl font-bold text-navy-900 dark:text-white">SynCash Elite</span>
          </Link>
        </motion.div>

        {/* OTP Verification Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <Card variant="premium">
            <CardHeader className="text-center">
              <div className="w-16 h-16 bg-blue-100 dark:bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <Phone className="text-blue-500" size={32} />
              </div>
              <CardTitle className="text-2xl">Verify Your Phone</CardTitle>
              <CardDescription>
                We've sent a 6-digit verification code to<br />
                <strong className="text-navy-900 dark:text-white">{phoneNumber}</strong>
              </CardDescription>
            </CardHeader>

            <CardContent>
              <div className="space-y-6">
                {/* OTP Input */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-navy-900 dark:text-white text-center">
                    Enter Verification Code
                  </label>
                  <Input
                    type="text"
                    placeholder="000000"
                    value={otpCode}
                    onChange={handleOtpChange}
                    className="text-center text-2xl tracking-widest font-mono"
                    maxLength={6}
                  />
                </div>

                {/* Timer */}
                <div className="text-center">
                  {timer > 0 ? (
                    <p className="text-sm text-grey-600 dark:text-grey-300">
                      Resend code in <span className="font-medium text-blue-500">{timer}s</span>
                    </p>
                  ) : (
                    <button
                      onClick={handleResendOtp}
                      disabled={resendLoading}
                      className="text-sm text-blue-500 hover:text-blue-600 font-medium flex items-center gap-2 mx-auto"
                    >
                      {resendLoading && <RefreshCw size={14} className="animate-spin" />}
                      Resend OTP
                    </button>
                  )}
                </div>

                {/* Verify Button */}
                <Button
                  onClick={handleVerifyOtp}
                  loading={loading}
                  disabled={otpCode.length !== 6}
                  className="w-full"
                  size="lg"
                >
                  <CheckCircle size={20} />
                  Verify & Continue
                </Button>

                {/* Back Link */}
                <div className="text-center">
                  <Link href="/auth/signup" className="text-sm text-grey-600 dark:text-grey-300 hover:text-blue-500 flex items-center gap-2 justify-center">
                    <ArrowLeft size={16} />
                    Back to Sign Up
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Demo Instructions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="mt-6"
        >
          <Card className="bg-blue-50 dark:bg-blue-500/10 border-blue-200 dark:border-blue-500/20">
            <CardContent className="p-4 text-center">
              <h4 className="font-medium text-blue-800 dark:text-blue-400 mb-2">
                Demo Mode
              </h4>
              <p className="text-sm text-blue-700 dark:text-blue-300">
                Enter any 6-digit code to continue to your dashboard
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}

export default function VerifyOtpPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <VerifyOtpForm />
    </Suspense>
  )
}