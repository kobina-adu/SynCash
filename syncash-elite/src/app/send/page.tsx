'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { 
  Send,
  User,
  Phone,
  DollarSign,
  MessageSquare,
  ArrowLeft,
  QrCode,
  Users,
  Clock,
  CheckCircle,
  Smartphone,
  Building2,
  Eye,
  EyeOff
} from 'lucide-react'
import { formatCurrency, validatePhone, generateTransactionId } from '@/lib/utils'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'

// Mock data
const userWallets = [
  { id: 'mtn', name: 'MTN MoMo', balance: 8500.00, icon: Smartphone, color: 'bg-yellow-500' },
  { id: 'telecel', name: 'Telecel Cash', balance: 4200.00, icon: Smartphone, color: 'bg-red-500' },
  { id: 'airteltigo', name: 'AirtelTigo', balance: 1847.50, icon: Smartphone, color: 'bg-teal-500' },
  { id: 'gcb', name: 'GCB Bank', balance: 1300.00, icon: Building2, color: 'bg-blue-500' }
]

const recentContacts = [
  { id: '1', name: 'Ama Osei', phone: '0244123456', avatar: 'AO', lastSent: '2024-01-10' },
  { id: '2', name: 'Kofi Mensah', phone: '0201987654', avatar: 'KM', lastSent: '2024-01-08' },
  { id: '3', name: 'Akosua Frimpong', phone: '0554567890', avatar: 'AF', lastSent: '2024-01-05' },
  { id: '4', name: 'Kwaku Asante', phone: '0277654321', avatar: 'KA', lastSent: '2024-01-03' }
]

interface SendFormData {
  recipientPhone: string
  recipientName: string
  amount: string
  message: string
  selectedWallet: string
}

export default function SendMoneyPage() {
  const router = useRouter()
  const [step, setStep] = useState(1) // 1: Form, 2: Confirmation, 3: Success
  const [loading, setLoading] = useState(false)
  const [showBalance, setShowBalance] = useState(true)
  const [formData, setFormData] = useState<SendFormData>({
    recipientPhone: '',
    recipientName: '',
    amount: '',
    message: '',
    selectedWallet: 'mtn'
  })
  const [errors, setErrors] = useState<Partial<SendFormData>>({})

  const selectedWalletData = userWallets.find(w => w.id === formData.selectedWallet)
  const transactionFee = parseFloat(formData.amount) * 0.01 // 1% fee
  const totalAmount = parseFloat(formData.amount || '0') + transactionFee

  const validateForm = (): boolean => {
    const newErrors: Partial<SendFormData> = {}

    if (!formData.recipientPhone) {
      newErrors.recipientPhone = 'Phone number is required'
    } else if (!validatePhone(formData.recipientPhone)) {
      newErrors.recipientPhone = 'Please enter a valid Ghana phone number'
    }

    if (!formData.recipientName.trim()) {
      newErrors.recipientName = 'Recipient name is required'
    }

    const amount = parseFloat(formData.amount)
    if (!formData.amount) {
      newErrors.amount = 'Amount is required'
    } else if (isNaN(amount) || amount <= 0) {
      newErrors.amount = 'Please enter a valid amount'
    } else if (amount < 1) {
      newErrors.amount = 'Minimum amount is ₵1.00'
    } else if (selectedWalletData && totalAmount > selectedWalletData.balance) {
      newErrors.amount = 'Insufficient balance in selected wallet'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleInputChange = (field: keyof SendFormData) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    setFormData(prev => ({ ...prev, [field]: e.target.value }))
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }))
    }
  }

  const handleContactSelect = (contact: typeof recentContacts[0]) => {
    setFormData(prev => ({
      ...prev,
      recipientPhone: contact.phone,
      recipientName: contact.name
    }))
  }

  const handleContinue = () => {
    if (validateForm()) {
      setStep(2)
    }
  }

  const handleSendMoney = async () => {
    setLoading(true)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000))
      setStep(3)
      toast.success('Money sent successfully!')
    } catch (error) {
      toast.error('Failed to send money. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const renderStep1 = () => (
    <div className="space-y-8">
      {/* Wallet Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign size={20} />
            Select Wallet
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {userWallets.map((wallet) => {
              const IconComponent = wallet.icon
              return (
                <label
                  key={wallet.id}
                  className={`flex items-center justify-between p-4 rounded-xl border-2 cursor-pointer transition-all ${
                    formData.selectedWallet === wallet.id
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-500/10'
                      : 'border-grey-200 dark:border-navy-700 hover:border-grey-300 dark:hover:border-navy-600'
                  }`}
                >
                  <input
                    type="radio"
                    name="wallet"
                    value={wallet.id}
                    checked={formData.selectedWallet === wallet.id}
                    onChange={handleInputChange('selectedWallet')}
                    className="sr-only"
                  />
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 ${wallet.color} rounded-xl flex items-center justify-center`}>
                      <IconComponent className="text-white" size={20} />
                    </div>
                    <div>
                      <p className="font-medium text-navy-900 dark:text-white">{wallet.name}</p>
                      <p className="text-sm text-grey-600 dark:text-grey-300">
                        {showBalance ? formatCurrency(wallet.balance) : '₵ ••••••'}
                      </p>
                    </div>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.preventDefault()
                      setShowBalance(!showBalance)
                    }}
                  >
                    {showBalance ? <EyeOff size={16} /> : <Eye size={16} />}
                  </Button>
                </label>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Recent Contacts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users size={20} />
            Recent Contacts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {recentContacts.map((contact) => (
              <button
                key={contact.id}
                onClick={() => handleContactSelect(contact)}
                className="flex flex-col items-center p-4 rounded-xl border border-grey-200 dark:border-navy-700 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-500/10 transition-all"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white font-semibold mb-2">
                  {contact.avatar}
                </div>
                <p className="font-medium text-navy-900 dark:text-white text-sm text-center">
                  {contact.name}
                </p>
                <p className="text-xs text-grey-600 dark:text-grey-300">
                  {contact.phone}
                </p>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Send Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Send size={20} />
            Send Money
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div className="grid md:grid-cols-2 gap-4">
              <Input
                label="Recipient Phone Number"
                icon={<Phone size={20} />}
                placeholder="0XX XXX XXXX"
                value={formData.recipientPhone}
                onChange={handleInputChange('recipientPhone')}
                error={errors.recipientPhone}
              />
              <Input
                label="Recipient Name"
                icon={<User size={20} />}
                placeholder="Enter recipient name"
                value={formData.recipientName}
                onChange={handleInputChange('recipientName')}
                error={errors.recipientName}
              />
            </div>

            <Input
              label="Amount"
              icon={<DollarSign size={20} />}
              placeholder="0.00"
              value={formData.amount}
              onChange={handleInputChange('amount')}
              error={errors.amount}
            />

            <div>
              <label className="block text-sm font-medium text-navy-900 dark:text-white mb-2">
                Message (Optional)
              </label>
              <textarea
                placeholder="Add a note for the recipient..."
                value={formData.message}
                onChange={handleInputChange('message')}
                rows={3}
                className="input-field resize-none"
              />
            </div>

            {/* Transaction Summary */}
            {formData.amount && parseFloat(formData.amount) > 0 && (
              <div className="bg-grey-50 dark:bg-navy-700 rounded-xl p-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-grey-600 dark:text-grey-300">Amount</span>
                  <span className="font-medium text-navy-900 dark:text-white">
                    {formatCurrency(parseFloat(formData.amount))}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-grey-600 dark:text-grey-300">Transaction Fee</span>
                  <span className="font-medium text-navy-900 dark:text-white">
                    {formatCurrency(transactionFee)}
                  </span>
                </div>
                <div className="border-t border-grey-200 dark:border-navy-600 pt-2">
                  <div className="flex justify-between">
                    <span className="font-medium text-navy-900 dark:text-white">Total</span>
                    <span className="font-bold text-navy-900 dark:text-white">
                      {formatCurrency(totalAmount)}
                    </span>
                  </div>
                </div>
              </div>
            )}

            <Button onClick={handleContinue} className="w-full" size="lg">
              Continue
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderStep2 = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CheckCircle size={20} />
          Confirm Transaction
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Transaction Details */}
          <div className="bg-grey-50 dark:bg-navy-700 rounded-xl p-6 space-y-4">
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white font-bold text-xl mx-auto mb-3">
                {formData.recipientName.split(' ').map(n => n[0]).join('').toUpperCase()}
              </div>
              <h3 className="text-xl font-bold text-navy-900 dark:text-white">
                {formData.recipientName}
              </h3>
              <p className="text-grey-600 dark:text-grey-300">{formData.recipientPhone}</p>
            </div>

            <div className="text-center py-4">
              <p className="text-3xl font-bold text-navy-900 dark:text-white">
                {formatCurrency(parseFloat(formData.amount))}
              </p>
              <p className="text-grey-600 dark:text-grey-300">Amount to send</p>
            </div>

            {formData.message && (
              <div className="bg-white dark:bg-navy-800 rounded-lg p-4">
                <p className="text-sm text-grey-600 dark:text-grey-300 mb-1">Message:</p>
                <p className="text-navy-900 dark:text-white">{formData.message}</p>
              </div>
            )}
          </div>

          {/* Payment Summary */}
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-grey-600 dark:text-grey-300">From</span>
              <span className="font-medium text-navy-900 dark:text-white">
                {selectedWalletData?.name}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-grey-600 dark:text-grey-300">Amount</span>
              <span className="font-medium text-navy-900 dark:text-white">
                {formatCurrency(parseFloat(formData.amount))}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-grey-600 dark:text-grey-300">Fee</span>
              <span className="font-medium text-navy-900 dark:text-white">
                {formatCurrency(transactionFee)}
              </span>
            </div>
            <div className="border-t border-grey-200 dark:border-navy-600 pt-3">
              <div className="flex justify-between">
                <span className="font-semibold text-navy-900 dark:text-white">Total</span>
                <span className="font-bold text-navy-900 dark:text-white">
                  {formatCurrency(totalAmount)}
                </span>
              </div>
            </div>
          </div>

          <div className="flex gap-4">
            <Button variant="secondary" onClick={() => setStep(1)} className="flex-1">
              <ArrowLeft size={20} />
              Back
            </Button>
            <Button onClick={handleSendMoney} loading={loading} className="flex-1">
              Send Money
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )

  const renderStep3 = () => (
    <Card className="text-center">
      <CardContent className="p-8">
        <div className="w-20 h-20 bg-green-100 dark:bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircle className="text-green-500" size={40} />
        </div>
        
        <h2 className="text-2xl font-bold text-navy-900 dark:text-white mb-2">
          Money Sent Successfully!
        </h2>
        <p className="text-grey-600 dark:text-grey-300 mb-6">
          Your payment of {formatCurrency(parseFloat(formData.amount))} has been sent to {formData.recipientName}
        </p>

        <div className="bg-grey-50 dark:bg-navy-700 rounded-xl p-4 mb-6">
          <p className="text-sm text-grey-600 dark:text-grey-300 mb-1">Transaction ID</p>
          <p className="font-mono font-medium text-navy-900 dark:text-white">
            {generateTransactionId()}
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4">
          <Button variant="secondary" onClick={() => router.push('/transactions')} className="flex-1">
            View Transaction
          </Button>
          <Button onClick={() => {
            setStep(1)
            setFormData({
              recipientPhone: '',
              recipientName: '',
              amount: '',
              message: '',
              selectedWallet: 'mtn'
            })
          }} className="flex-1">
            Send Again
          </Button>
        </div>
      </CardContent>
    </Card>
  )

  return (
    <div className="min-h-screen bg-grey-50 dark:bg-navy-900">
      {/* Header */}
      <header className="bg-white dark:bg-navy-800 border-b border-grey-200 dark:border-navy-700 sticky top-0 z-40">
        <div className="section-padding py-4">
          <div className="container-width">
            <div className="flex items-center gap-4">
              <Link href="/dashboard">
                <Button variant="ghost" size="sm">
                  <ArrowLeft size={20} />
                </Button>
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-navy-900 dark:text-white">Send Money</h1>
                <p className="text-grey-600 dark:text-grey-300">Transfer money to friends and family</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="section-padding py-8">
        <div className="container-width max-w-2xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            {step === 1 && renderStep1()}
            {step === 2 && renderStep2()}
            {step === 3 && renderStep3()}
          </motion.div>
        </div>
      </main>
    </div>
  )
}
