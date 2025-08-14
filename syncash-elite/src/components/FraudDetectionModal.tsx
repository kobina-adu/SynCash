'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { 
  Shield, 
  AlertTriangle, 
  XCircle, 
  CheckCircle, 
  Phone, 
  X,
  Loader2
} from 'lucide-react'
import { apiService, type FraudDetectionResult } from '@/lib/api'
import toast from 'react-hot-toast'

interface FraudDetectionModalProps {
  isOpen: boolean
  fraudResult: FraudDetectionResult | null
  onClose: () => void
  onProceed: () => void
  onCancel: () => void
}

export default function FraudDetectionModal({
  isOpen,
  fraudResult,
  onClose,
  onProceed,
  onCancel
}: FraudDetectionModalProps) {
  const [otpCode, setOtpCode] = useState('')
  const [otpRequested, setOtpRequested] = useState(false)
  const [otpLoading, setOtpLoading] = useState(false)
  const [verifyingOtp, setVerifyingOtp] = useState(false)

  if (!isOpen || !fraudResult) return null

  const { ui_response, transaction_id, risk_level, risk_score, fraud_check } = fraudResult

  // Handle OTP request
  const handleRequestOTP = async () => {
    if (!transaction_id) return

    setOtpLoading(true)
    try {
      const result = await apiService.requestOTP(transaction_id)
      if (result.success) {
        setOtpRequested(true)
        toast.success('OTP sent to your registered phone number')
      } else {
        toast.error(result.error || 'Failed to send OTP')
      }
    } catch (error) {
      toast.error('Failed to request OTP. Please try again.')
      console.error('OTP request error:', error)
    } finally {
      setOtpLoading(false)
    }
  }

  // Handle OTP verification
  const handleVerifyOTP = async () => {
    if (!transaction_id || !otpCode.trim()) {
      toast.error('Please enter the OTP code')
      return
    }

    setVerifyingOtp(true)
    try {
      const result = await apiService.verifyOTP(transaction_id, otpCode.trim())
      if (result.success) {
        toast.success('OTP verified successfully!')
        onProceed()
      } else {
        toast.error(result.error || 'Invalid OTP. Please try again.')
        setOtpCode('')
      }
    } catch (error) {
      toast.error('OTP verification failed. Please try again.')
      console.error('OTP verification error:', error)
      setOtpCode('')
    } finally {
      setVerifyingOtp(false)
    }
  }

  // Handle transaction cancellation
  const handleCancel = async () => {
    if (transaction_id) {
      try {
        await apiService.cancelTransaction(transaction_id)
        toast.success('Transaction cancelled')
      } catch (error) {
        console.error('Cancel transaction error:', error)
      }
    }
    onCancel()
  }

  // Render different UI based on fraud detection result
  const renderModalContent = () => {
    if (!ui_response) return null

    const { type, title, message, warning_text, color } = ui_response

    // Safe transaction - Green popup
    if (type === 'safe' || risk_level === 'LOW') {
      return (
        <Card className="w-full max-w-md mx-4 border-green-200">
          <CardHeader className="text-center pb-4">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Shield className="text-green-600" size={32} />
            </div>
            <CardTitle className="text-green-700 text-xl">
              {title || '✅ Transaction Verified'}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-gray-600 mb-6">
              {message || 'This transaction appears safe and can proceed normally.'}
            </p>
            
            {fraud_check && (
              <div className="bg-green-50 rounded-lg p-3 mb-6 text-sm">
                <div className="flex justify-between">
                  <span>Risk Score:</span>
                  <span className="font-medium text-green-600">
                    {Math.round((fraud_check.risk_score || 0) * 100)}% (Low Risk)
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Confidence:</span>
                  <span className="font-medium">
                    {Math.round((fraud_check.confidence || 0) * 100)}%
                  </span>
                </div>
              </div>
            )}

            <div className="flex gap-3">
              <Button
                onClick={handleCancel}
                variant="secondary"
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                onClick={onProceed}
                className="flex-1 bg-green-600 hover:bg-green-700"
              >
                PROCEED
              </Button>
            </div>
          </CardContent>
        </Card>
      )
    }

    // High-risk transaction - Yellow/Orange warning with OTP
    if (type === 'high_risk' || risk_level === 'MEDIUM' || risk_level === 'HIGH') {
      return (
        <Card className="w-full max-w-md mx-4 border-orange-200">
          <CardHeader className="text-center pb-4">
            <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="text-orange-600" size={32} />
            </div>
            <CardTitle className="text-orange-700 text-xl">
              {title || '⚠️ CAUTION MODE'}
            </CardTitle>
            {warning_text && (
              <p className="text-red-600 font-semibold text-sm mt-2">
                {warning_text}
              </p>
            )}
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-gray-600 mb-4">
              {message || 'High-risk transaction detected. Additional verification required.'}
            </p>

            {fraud_check && (
              <div className="bg-orange-50 rounded-lg p-3 mb-6 text-sm">
                <div className="flex justify-between">
                  <span>Risk Score:</span>
                  <span className="font-medium text-orange-600">
                    {Math.round((fraud_check.risk_score || 0) * 100)}% (High Risk)
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>ML Model:</span>
                  <span className="font-medium">
                    {fraud_check.ml_model_used ? '✅ Active' : '❌ Inactive'}
                  </span>
                </div>
              </div>
            )}

            {!otpRequested ? (
              <div className="space-y-4">
                <p className="text-sm text-gray-500">
                  We'll send a verification code to your registered phone number
                </p>
                <div className="flex gap-3">
                  <Button
                    onClick={handleCancel}
                    variant="secondary"
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleRequestOTP}
                    loading={otpLoading}
                    className="flex-1 bg-orange-600 hover:bg-orange-700"
                  >
                    <Phone size={16} className="mr-2" />
                    REQUEST OTP
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Enter OTP Code
                  </label>
                  <Input
                    type="text"
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value)}
                    placeholder="Enter 6-digit code"
                    maxLength={6}
                    className="text-center text-lg tracking-widest"
                  />
                </div>
                <div className="flex gap-3">
                  <Button
                    onClick={handleCancel}
                    variant="secondary"
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleVerifyOTP}
                    loading={verifyingOtp}
                    disabled={!otpCode.trim()}
                    className="flex-1 bg-green-600 hover:bg-green-700"
                  >
                    VERIFY & PROCEED
                  </Button>
                </div>
                <Button
                  onClick={handleRequestOTP}
                  variant="ghost"
                  size="sm"
                  loading={otpLoading}
                  className="w-full text-orange-600"
                >
                  Resend OTP
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )
    }

    // Critical/Blocked transaction - Red danger
    if (type === 'critical' || type === 'blocked' || risk_level === 'CRITICAL') {
      return (
        <Card className="w-full max-w-md mx-4 border-red-200">
          <CardHeader className="text-center pb-4">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <XCircle className="text-red-600" size={32} />
            </div>
            <CardTitle className="text-red-700 text-xl">
              {title || '🚫 TRANSACTION BLOCKED'}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-gray-600 mb-4">
              {message || 'This transaction has been blocked due to high fraud risk.'}
            </p>

            {fraud_check && (
              <div className="bg-red-50 rounded-lg p-3 mb-6 text-sm">
                <div className="flex justify-between">
                  <span>Risk Score:</span>
                  <span className="font-medium text-red-600">
                    {Math.round((fraud_check.risk_score || 0) * 100)}% (Critical)
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Status:</span>
                  <span className="font-medium text-red-600">BLOCKED</span>
                </div>
              </div>
            )}

            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-700 text-sm font-medium">
                🛡️ For your security, this transaction cannot proceed.
              </p>
              <p className="text-red-600 text-sm mt-1">
                Please contact customer support if you believe this is an error.
              </p>
            </div>

            <Button
              onClick={handleCancel}
              className="w-full bg-red-600 hover:bg-red-700"
            >
              UNDERSTOOD
            </Button>
          </CardContent>
        </Card>
      )
    }

    // System error - Orange warning
    return (
      <Card className="w-full max-w-md mx-4 border-orange-200">
        <CardHeader className="text-center pb-4">
          <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="text-orange-600" size={32} />
          </div>
          <CardTitle className="text-orange-700 text-xl">
            {title || '⚠️ SECURITY CHECK REQUIRED'}
          </CardTitle>
        </CardHeader>
        <CardContent className="text-center">
          <p className="text-gray-600 mb-6">
            {message || 'Unable to verify transaction security. Please try again.'}
          </p>

          <div className="flex gap-3">
            <Button
              onClick={handleCancel}
              variant="secondary"
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={() => window.location.reload()}
              className="flex-1 bg-orange-600 hover:bg-orange-700"
            >
              RETRY
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        onClick={(e) => e.target === e.currentTarget && handleCancel()}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          transition={{ type: "spring", duration: 0.3 }}
        >
          {renderModalContent()}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
