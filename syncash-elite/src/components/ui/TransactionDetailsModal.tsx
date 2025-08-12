'use client'

import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { 
  X, 
  ArrowUpRight, 
  ArrowDownLeft, 
  Copy, 
  Download, 
  Share2,
  CheckCircle,
  Clock,
  AlertCircle,
  Calendar,
  Hash,
  User,
  Building2,
  Smartphone,
  CreditCard,
  ArrowLeft
} from 'lucide-react'
import { formatCurrency } from '@/lib/utils'

interface Transaction {
  id: string
  type: 'sent' | 'received'
  amount: number
  description: string
  date: string
  status: 'completed' | 'pending' | 'failed'
  avatar?: string | null
  recipient?: string
  sender?: string
  reference?: string
  fee?: number
  method?: string
  category?: string
  notes?: string
}

interface TransactionDetailsModalProps {
  transaction: Transaction | null
  isOpen: boolean
  onClose: () => void
}

export function TransactionDetailsModal({ transaction, isOpen, onClose }: TransactionDetailsModalProps) {
  if (!transaction) return null

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    // You could add a toast notification here
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'pending':
        return <Clock className="w-5 h-5 text-yellow-500" />
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />
      default:
        return <Clock className="w-5 h-5 text-grey-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-500/20'
      case 'pending':
        return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-500/20'
      case 'failed':
        return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-500/20'
      default:
        return 'text-grey-600 dark:text-grey-400 bg-grey-50 dark:bg-grey-500/20'
    }
  }

  const getMethodIcon = (method: string) => {
    switch (method?.toLowerCase()) {
      case 'mtn momo':
      case 'momo':
        return <Smartphone className="w-5 h-5 text-yellow-500" />
      case 'bank':
      case 'bank transfer':
        return <Building2 className="w-5 h-5 text-blue-500" />
      case 'card':
      case 'credit card':
        return <CreditCard className="w-5 h-5 text-purple-500" />
      default:
        return <Smartphone className="w-5 h-5 text-grey-500" />
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
            onClick={onClose}
          />
          
          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <Card className="w-full max-w-md bg-white dark:bg-navy-800 shadow-2xl">
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-xl">Transaction Details</CardTitle>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onClose}
                    className="h-8 w-8 p-0"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>

              <CardContent className="space-y-6">
                {/* Transaction Type & Amount */}
                <div className="text-center space-y-2">
                  <div className="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                    {transaction.type === 'received' ? (
                      <ArrowDownLeft className="w-8 h-8 text-white" />
                    ) : (
                      <ArrowUpRight className="w-8 h-8 text-white" />
                    )}
                  </div>
                  <div>
                    <p className={`text-3xl font-bold ${
                      transaction.type === 'received' 
                        ? 'text-green-600 dark:text-green-400' 
                        : 'text-navy-900 dark:text-white'
                    }`}>
                      {transaction.type === 'received' ? '+' : '-'}
                      {formatCurrency(transaction.amount)}
                    </p>
                    <p className="text-grey-600 dark:text-grey-300 capitalize">
                      {transaction.type === 'received' ? 'Money Received' : 'Money Sent'}
                    </p>
                  </div>
                </div>

                {/* Status */}
                <div className="flex items-center justify-center">
                  <div className={`flex items-center gap-2 px-3 py-2 rounded-full ${getStatusColor(transaction.status)}`}>
                    {getStatusIcon(transaction.status)}
                    <span className="font-medium capitalize">{transaction.status}</span>
                  </div>
                </div>

                {/* Transaction Details */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-grey-600 dark:text-grey-300">Description</span>
                    <span className="font-medium text-navy-900 dark:text-white">
                      {transaction.description}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-grey-600 dark:text-grey-300">Date & Time</span>
                    <div className="text-right">
                      <p className="font-medium text-navy-900 dark:text-white">
                        {new Date(transaction.date).toLocaleDateString()}
                      </p>
                      <p className="text-sm text-grey-600 dark:text-grey-300">
                        {new Date(transaction.date).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-grey-600 dark:text-grey-300">Transaction ID</span>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm text-navy-900 dark:text-white">
                        {transaction.id}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(transaction.id)}
                        className="h-6 w-6 p-0"
                      >
                        <Copy className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>

                  {transaction.method && (
                    <div className="flex items-center justify-between">
                      <span className="text-grey-600 dark:text-grey-300">Payment Method</span>
                      <div className="flex items-center gap-2">
                        {getMethodIcon(transaction.method)}
                        <span className="font-medium text-navy-900 dark:text-white">
                          {transaction.method}
                        </span>
                      </div>
                    </div>
                  )}

                  {transaction.fee && (
                    <div className="flex items-center justify-between">
                      <span className="text-grey-600 dark:text-grey-300">Transaction Fee</span>
                      <span className="font-medium text-navy-900 dark:text-white">
                        {formatCurrency(transaction.fee)}
                      </span>
                    </div>
                  )}

                  {(transaction.recipient || transaction.sender) && (
                    <div className="flex items-center justify-between">
                      <span className="text-grey-600 dark:text-grey-300">
                        {transaction.type === 'received' ? 'From' : 'To'}
                      </span>
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4 text-grey-500" />
                        <span className="font-medium text-navy-900 dark:text-white">
                          {transaction.recipient || transaction.sender}
                        </span>
                      </div>
                    </div>
                  )}

                  {transaction.reference && (
                    <div className="flex items-center justify-between">
                      <span className="text-grey-600 dark:text-grey-300">Reference</span>
                      <span className="font-mono text-sm text-navy-900 dark:text-white">
                        {transaction.reference}
                      </span>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="space-y-3 pt-4">
                  {/* Primary Back Button */}
                  <Button
                    variant="primary"
                    className="w-full"
                    onClick={onClose}
                  >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back to Dashboard
                  </Button>
                  
                  {/* Secondary Action Buttons */}
                  <div className="flex gap-2">
                    <Button
                      variant="ghost"
                      className="flex-1"
                      onClick={() => copyToClipboard(transaction.id)}
                    >
                      <Copy className="w-4 h-4 mr-2" />
                      Copy ID
                    </Button>
                    <Button
                      variant="ghost"
                      className="flex-1"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Receipt
                    </Button>
                    <Button
                      variant="ghost"
                      className="flex-1"
                    >
                      <Share2 className="w-4 h-4 mr-2" />
                      Share
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
