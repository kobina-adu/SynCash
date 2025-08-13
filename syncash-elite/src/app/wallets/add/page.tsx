'use client'

import React, { useState } from 'react'
import Image from 'next/image';
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { 
  Smartphone,
  Building2,
  Shield,
  ArrowLeft,
  Plus,
  CheckCircle,
  AlertCircle,
  Phone,
  CreditCard,
  Lock,
  Eye,
  EyeOff,
  RefreshCw
} from 'lucide-react'
import { validatePhone } from '@/lib/utils'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'

// Available wallet providers
const walletProviders = [
  {
    id: 'mtn',
    name: 'MTN Mobile Money',
    type: 'mobile',
    icon: 'mtn.jpg',
    logo: 'mtn.jpg',
    //color: 'bg-yellow-500',
    description: 'Link your MTN MoMo account',
    requirements: ['Phone number', 'PIN'],
    fees: 'Free linking'
    
  },
  {
    id: 'telecel',
    name: 'Telecel Cash',
    type: 'mobile',
    icon: 'telecel.png',
    logo: 'telecel.png',
    //color: 'bg-red-500',
    description: 'Connect your Telecel Cash wallet',
    requirements: ['Phone number', 'PIN'],
    fees: 'Free linking'
  },
  {
    id: 'airteltigo',
    name: 'AirtelTigo Money',
    type: 'mobile',
    icon: 'aitel.jpg',
    logo: 'aitel.jpg',
   // color: 'bg-teal-500',
    description: 'Add your AirtelTigo Money account',
    requirements: ['Phone number', 'PIN'],
    fees: 'Free linking'
  },
  {
    id: 'gcb',
    name: 'GCB Bank',
    type: 'bank',
    icon: 'gcb.jpg',
    logo: 'gcb.jpg',
    //color: 'bg-blue-500',
    description: 'Connect your GCB Bank account',
    requirements: ['Account number', 'Internet banking PIN'],
    fees: 'Free linking'
  },
  {
    id: 'ecobank',
    name: 'Ecobank Ghana',
    type: 'bank',
    icon: 'ecobank.jpg',
    logo: 'ecobank.jpg',
    //color: 'bg-green-500',
    description: 'Link your Ecobank account',
    requirements: ['Account number', 'Internet banking PIN'],
    fees: 'Free linking'
  },
  {
    id: 'absa',
    name: 'Absa Bank Ghana',
    type: 'bank',
   // color: 'bg-purple-500',
    icon: 'absa.jpg',
    logo: 'absa.jpg',
    
    description: 'Connect your Absa account',
    requirements: ['Account number', 'Internet banking PIN'],
    fees: 'Free linking'
  }
]

interface LinkingFormData {
  phoneNumber: string
  accountNumber: string
  pin: string
  confirmPin: string
}

export default function AddWalletPage() {
  const router = useRouter()
  const [step, setStep] = useState(1) // 1: Provider Selection, 2: Account Details, 3: OTP Verification, 4: Success
  const [selectedProvider, setSelectedProvider] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [otpCode, setOtpCode] = useState('')
  const [otpTimer, setOtpTimer] = useState(60)
  const [canResendOtp, setCanResendOtp] = useState(false)
  const [showPin, setShowPin] = useState(false)
  const [formData, setFormData] = useState<LinkingFormData>({
    phoneNumber: '',
    accountNumber: '',
    pin: '',
    confirmPin: ''
  })
  const [errors, setErrors] = useState<Partial<LinkingFormData>>({})

  // Start OTP timer
  React.useEffect(() => {
    if (step === 3 && otpTimer > 0) {
      const timer = setTimeout(() => setOtpTimer(otpTimer - 1), 1000)
      return () => clearTimeout(timer)
    } else if (otpTimer === 0) {
      setCanResendOtp(true)
    }
  }, [step, otpTimer])

  const validateForm = (): boolean => {
    const newErrors: Partial<LinkingFormData> = {}

    if (selectedProvider?.type === 'mobile') {
      if (!formData.phoneNumber) {
        newErrors.phoneNumber = 'Phone number is required'
      } else if (!validatePhone(formData.phoneNumber)) {
        newErrors.phoneNumber = 'Please enter a valid Ghana phone number'
      }
    }

    if (selectedProvider?.type === 'bank') {
      if (!formData.accountNumber) {
        newErrors.accountNumber = 'Account number is required'
      } else if (formData.accountNumber.length < 10) {
        newErrors.accountNumber = 'Account number must be at least 10 digits'
      }
    }

    if (!formData.pin) {
      newErrors.pin = 'PIN is required'
    } else if (formData.pin.length < 4) {
      newErrors.pin = 'PIN must be at least 4 digits'
    }

    if (!formData.confirmPin) {
      newErrors.confirmPin = 'Please confirm your PIN'
    } else if (formData.pin !== formData.confirmPin) {
      newErrors.confirmPin = 'PINs do not match'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleInputChange = (field: keyof LinkingFormData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData(prev => ({ ...prev, [field]: e.target.value }))
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }))
    }
  }

  const handleProviderSelect = (provider: any) => {
    setSelectedProvider(provider)
    setStep(2)
  }

  const handleLinkAccount = async () => {
    if (!validateForm()) {
      toast.error('Please fix the errors below')
      return
    }

    setLoading(true)
    try {
      // Simulate API call to initiate linking
      await new Promise(resolve => setTimeout(resolve, 2000))
      setStep(3)
      setOtpTimer(60)
      setCanResendOtp(false)
      toast.success('OTP sent to your registered number')
    } catch (error) {
      toast.error('Failed to link account. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyOtp = async () => {
    if (!otpCode || otpCode.length !== 6) {
      toast.error('Please enter a valid 6-digit OTP')
      return
    }

    setLoading(true)
    try {
      // Simulate OTP verification
      await new Promise(resolve => setTimeout(resolve, 1500))
      setStep(4)
      toast.success('Account linked successfully!')
      // Redirect to dashboard with new account info
      const accountPayload = {
        name: selectedProvider?.name,
        type: selectedProvider?.type,
        logo: selectedProvider?.logo,
        color: selectedProvider?.color || '#FFA500',
        textColor: 'text-orange-600 dark:text-orange-400',
        // Add user-provided info
        ...formData
      };
      const params = new URLSearchParams({ newAccount: JSON.stringify(accountPayload) });
      router.push(`/dashboard?${params.toString()}`);
    } catch (error) {
      toast.error('Invalid OTP. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleResendOtp = async () => {
    setLoading(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 1000))
      setOtpTimer(60)
      setCanResendOtp(false)
      toast.success('New OTP sent')
    } catch (error) {
      toast.error('Failed to resend OTP')
    } finally {
      setLoading(false)
    }
  }

  const renderStep1 = () => (
    <div className="space-y-8">
      {/* Header */}
      <Card className="bg-gradient-to-br from-blue-500 to-blue-700 text-white border-0">
        <CardContent className="p-8 text-center">
          <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Plus className="text-white" size={32} />
          </div>
          <h2 className="text-2xl font-bold mb-2">Link New Account</h2>
          <p className="text-blue-100">
            Connect your mobile money or bank account to start managing all your finances in one place
          </p>
        </CardContent>
      </Card>

      {/* Mobile Money Providers */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Smartphone size={20} />
            Mobile Money
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-4">
            {walletProviders.filter(p => p.type === 'mobile').map((provider) => {
              const IconComponent = provider.icon
              return (
                <motion.button
                  key={provider.id}
                  onClick={() => handleProviderSelect(provider)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="text-left p-6 rounded-2xl border border-grey-200 dark:border-navy-700 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-500/10 transition-all"
                >
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4">
                    <Image src={`/images/${provider.icon}`} height={65} width={65} alt={provider.name} />
                  </div>
                  <h3 className="font-semibold text-navy-900 dark:text-white mb-2">
                    {provider.name}
                  </h3>
                  <p className="text-sm text-grey-600 dark:text-grey-300 mb-3">
                    {provider.description}
                  </p>
                  <p className="text-xs text-green-600 dark:text-green-400 font-medium">
                    {provider.fees}
                  </p>
                </motion.button>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Bank Accounts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 size={20} />
            Bank Accounts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-4">
            {walletProviders.filter(p => p.type === 'bank').map((provider) => {
              const IconComponent = provider.icon
              return (
                <motion.button
                  key={provider.id}
                  onClick={() => handleProviderSelect(provider)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="text-left p-6 rounded-2xl border border-grey-200 dark:border-navy-700 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-500/10 transition-all"
                >
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4">
                 <Image src={`/images/${provider.logo}`} height={65} width={65} alt={provider.name} className="text-lg" />
                  </div>
                  <h3 className="font-semibold text-navy-900 dark:text-white mb-2">
                    {provider.name}
                  </h3>
                  <p className="text-sm text-grey-600 dark:text-grey-300 mb-3">
                    {provider.description}
                  </p>
                  <p className="text-xs text-green-600 dark:text-green-400 font-medium">
                    {provider.fees}
                  </p>
                </motion.button>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderStep2 = () => (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => setStep(1)}>
            <ArrowLeft size={20} />
          </Button>
          <div>
            <CardTitle>Link {selectedProvider?.name}</CardTitle>
            <p className="text-grey-600 dark:text-grey-300">Enter your account details securely</p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Provider Info */}
          <div className="flex items-center gap-4 p-4 bg-grey-50 dark:bg-navy-700 rounded-xl">
            <div className={`w-12 h-12 ${selectedProvider?.color} rounded-xl flex items-center justify-center`}>
              <selectedProvider.icon className="text-white" size={24} />
            </div>
            <div>
              <p className="font-medium text-navy-900 dark:text-white">{selectedProvider?.name}</p>
              <p className="text-sm text-grey-600 dark:text-grey-300">{selectedProvider?.description}</p>
            </div>
          </div>

          {/* Requirements */}
          <div className="bg-blue-50 dark:bg-blue-500/10 rounded-xl p-4">
            <div className="flex items-start gap-3">
              <Shield className="text-blue-500 mt-1" size={20} />
              <div>
                <p className="font-medium text-blue-900 dark:text-blue-400 mb-2">Required Information:</p>
                <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1">
                  {selectedProvider?.requirements.map((req: string, index: number) => (
                    <li key={index} className="flex items-center gap-2">
                      <CheckCircle size={14} />
                      {req}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Form Fields */}
          <div className="space-y-4">
            {selectedProvider?.type === 'mobile' && (
              <Input
                label="Phone Number"
                icon={<Phone size={20} />}
                placeholder="0XX XXX XXXX"
                value={formData.phoneNumber}
                onChange={handleInputChange('phoneNumber')}
                error={errors.phoneNumber}
              />
            )}

            {selectedProvider?.type === 'bank' && (
              <Input
                label="Account Number"
                icon={<CreditCard size={20} />}
                placeholder="Enter your account number"
                value={formData.accountNumber}
                onChange={handleInputChange('accountNumber')}
                error={errors.accountNumber}
              />
            )}

            <Input
              label={selectedProvider?.type === 'mobile' ? 'Mobile Money PIN' : 'Internet Banking PIN'}
              type={showPin ? 'text' : 'password'}
              icon={<Lock size={20} />}
              placeholder="Enter your PIN"
              value={formData.pin}
              onChange={handleInputChange('pin')}
              error={errors.pin}
              showPasswordToggle
            />

            <Input
              label="Confirm PIN"
              type={showPin ? 'text' : 'password'}
              icon={<Lock size={20} />}
              placeholder="Confirm your PIN"
              value={formData.confirmPin}
              onChange={handleInputChange('confirmPin')}
              error={errors.confirmPin}
              showPasswordToggle
            />
          </div>

          {/* Security Notice */}
          <div className="bg-green-50 dark:bg-green-500/10 rounded-xl p-4 border border-green-200 dark:border-green-500/20">
            <div className="flex items-start gap-3">
              <Shield className="text-green-500 mt-1" size={20} />
              <div>
                <p className="font-medium text-green-900 dark:text-green-400 mb-1">Your data is secure</p>
                <p className="text-sm text-green-800 dark:text-green-300">
                  We use bank-level encryption to protect your information. Your PIN is never stored on our servers.
                </p>
              </div>
            </div>
          </div>

          <Button onClick={handleLinkAccount} loading={loading} className="w-full" size="lg">
            Link Account
          </Button>
        </div>
      </CardContent>
    </Card>
  )

  const renderStep3 = () => (
    <Card>
      <CardHeader>
        <CardTitle className="text-center">Verify Your Identity</CardTitle>
        <p className="text-grey-600 dark:text-grey-300 text-center">
          We've sent a 6-digit code to your registered number
        </p>
      </CardHeader>
      <CardContent>
        <div className="space-y-6 text-center">
          <div className="w-20 h-20 bg-blue-100 dark:bg-blue-500/20 rounded-full flex items-center justify-center mx-auto">
            <Phone className="text-blue-500" size={32} />
          </div>

          <div>
            <Input
              label="Enter OTP Code"
              placeholder="000000"
              value={otpCode}
              onChange={(e) => setOtpCode(e.target.value)}
              className="text-center text-2xl tracking-widest"
              maxLength={6}
            />
          </div>

          <div className="text-sm text-grey-600 dark:text-grey-300">
            {otpTimer > 0 ? (
              <p>Resend code in {otpTimer} seconds</p>
            ) : (
              <button
                onClick={handleResendOtp}
                disabled={loading}
                className="text-blue-500 hover:text-blue-600 font-medium"
              >
                Resend OTP
              </button>
            )}
          </div>

          <Button
            onClick={handleVerifyOtp}
            loading={loading}
            disabled={otpCode.length !== 6}
            className="w-full"
            size="lg"
          >
            Verify & Link Account
          </Button>
        </div>
      </CardContent>
    </Card>
  )

  const renderStep4 = () => (
    <Card className="text-center">
      <CardContent className="p-8">
        <div className="w-20 h-20 bg-green-100 dark:bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircle className="text-green-500" size={40} />
        </div>
        
        <h2 className="text-2xl font-bold text-navy-900 dark:text-white mb-2">
          Account Linked Successfully!
        </h2>
        <p className="text-grey-600 dark:text-grey-300 mb-6">
          Your {selectedProvider?.name} account has been securely linked to SynCash Elite
        </p>

        <div className="bg-grey-50 dark:bg-navy-700 rounded-xl p-4 mb-6">
          <div className="flex items-center justify-center gap-3">
            <div className={`w-10 h-10 ${selectedProvider?.color} rounded-xl flex items-center justify-center`}>
              <selectedProvider.icon className="text-white" size={20} />
            </div>
            <div className="text-left">
              <p className="font-medium text-navy-900 dark:text-white">{selectedProvider?.name}</p>
              <p className="text-sm text-grey-600 dark:text-grey-300">
                {selectedProvider?.type === 'mobile' ? formData.phoneNumber : formData.accountNumber}
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-4">
          <Button variant="secondary" onClick={() => router.push('/dashboard')} className="flex-1">
            Go to Dashboard
          </Button>
          <Button onClick={() => {
            setStep(1)
            setSelectedProvider(null)
            setFormData({
              phoneNumber: '',
              accountNumber: '',
              pin: '',
              confirmPin: ''
            })
            setOtpCode('')
          }} className="flex-1">
            Link Another Account
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
                <h1 className="text-2xl font-bold text-navy-900 dark:text-white">Add Wallet</h1>
                <p className="text-grey-600 dark:text-grey-300">Link your mobile money or bank account</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="section-padding py-8">
        <div className="container-width max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            {step === 1 && renderStep1()}
            {step === 2 && renderStep2()}
            {step === 3 && renderStep3()}
            {step === 4 && renderStep4()}   
          </motion.div>
        </div>
      </main>
    </div>
  )
  return (
    <div className="p-6">
      {/* <TransactionHistory /> */}
    </div>
  );
}
