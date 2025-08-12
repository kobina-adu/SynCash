'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { 
  CreditCard,
  Zap,
  Wifi,
  Tv,
  Car,
  GraduationCap,
  Home,
  Phone,
  ArrowLeft,
  Search,
  Clock,
  CheckCircle,
  AlertCircle,
  DollarSign,
  Calendar,
  Star
} from 'lucide-react'
import { formatCurrency } from '@/lib/utils'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'

// Bill categories and providers
const billCategories = [
  {
    id: 'utilities',
    name: 'Utilities',
    icon: Zap,
    color: 'from-yellow-500 to-orange-500',
    providers: [
      { id: 'ecg', name: 'ECG (Electricity Company of Ghana)', logo: '⚡', type: 'electricity' },
      { id: 'gwcl', name: 'Ghana Water Company Limited', logo: '💧', type: 'water' },
      { id: 'ngl', name: 'National Gas Limited', logo: '🔥', type: 'gas' }
    ]
  },
  {
    id: 'telecom',
    name: 'Telecom & Internet',
    icon: Phone,
    color: 'from-blue-500 to-indigo-500',
    providers: [
      { id: 'mtn', name: 'MTN Ghana', logo: '📱', type: 'mobile' },
      { id: 'telecel', name: 'Telecel Ghana', logo: '📱', type: 'mobile' },
      { id: 'airteltigo', name: 'AirtelTigo', logo: '📱', type: 'mobile' },
      { id: 'surfline', name: 'Surfline Communications', logo: '🌐', type: 'internet' }
    ]
  },
  {
    id: 'entertainment',
    name: 'Entertainment',
    icon: Tv,
    color: 'from-purple-500 to-pink-500',
    providers: [
      { id: 'dstv', name: 'DStv Ghana', logo: '📺', type: 'tv' },
      { id: 'gotv', name: 'GOtv Ghana', logo: '📺', type: 'tv' },
      { id: 'startimes', name: 'StarTimes Ghana', logo: '📺', type: 'tv' },
      { id: 'netflix', name: 'Netflix', logo: '🎬', type: 'streaming' }
    ]
  },
  {
    id: 'education',
    name: 'Education',
    icon: GraduationCap,
    color: 'from-green-500 to-emerald-500',
    providers: [
      { id: 'ucc', name: 'University of Cape Coast', logo: '🎓', type: 'university' },
      { id: 'ug', name: 'University of Ghana', logo: '🎓', type: 'university' },
      { id: 'knust', name: 'KNUST', logo: '🎓', type: 'university' }
    ]
  }
]

const recentBills = [
  {
    id: '1',
    provider: 'ECG (Electricity Company of Ghana)',
    accountNumber: '1234567890',
    amount: 85.50,
    dueDate: '2024-01-20',
    status: 'pending',
    category: 'utilities'
  },
  {
    id: '2',
    provider: 'MTN Ghana',
    accountNumber: '0244123456',
    amount: 25.00,
    dueDate: '2024-01-18',
    status: 'paid',
    category: 'telecom'
  },
  {
    id: '3',
    provider: 'DStv Ghana',
    accountNumber: '1023456789',
    amount: 120.00,
    dueDate: '2024-01-25',
    status: 'overdue',
    category: 'entertainment'
  }
]

const savedBillers = [
  {
    id: '1',
    name: 'Home Electricity',
    provider: 'ECG (Electricity Company of Ghana)',
    accountNumber: '1234567890',
    category: 'utilities',
    lastPaid: '2023-12-15'
  },
  {
    id: '2',
    name: 'Mobile Line',
    provider: 'MTN Ghana',
    accountNumber: '0244123456',
    category: 'telecom',
    lastPaid: '2024-01-01'
  }
]

export default function BillPaymentsPage() {
  const router = useRouter()
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [selectedProvider, setSelectedProvider] = useState<any>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [step, setStep] = useState(1) // 1: Categories, 2: Provider Selection, 3: Bill Details, 4: Payment
  const [billForm, setBillForm] = useState({
    accountNumber: '',
    amount: '',
    customerName: '',
    reference: ''
  })
  const [loading, setLoading] = useState(false)

  const filteredCategories = billCategories.filter(category =>
    category.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    category.providers.some(provider => 
      provider.name.toLowerCase().includes(searchTerm.toLowerCase())
    )
  )

  const handleCategorySelect = (categoryId: string) => {
    setSelectedCategory(categoryId)
    setStep(2)
  }

  const handleProviderSelect = (provider: any) => {
    setSelectedProvider(provider)
    setStep(3)
  }

  const handleBillFormChange = (field: string) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setBillForm(prev => ({ ...prev, [field]: e.target.value }))
  }

  const handlePayBill = async () => {
    setLoading(true)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000))
      toast.success('Bill payment successful!')
      router.push('/transactions')
    } catch (error) {
      toast.error('Payment failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid':
        return 'status-success'
      case 'pending':
        return 'status-pending'
      case 'overdue':
        return 'status-failed'
      default:
        return 'status-pending'
    }
  }

  const renderStep1 = () => (
    <div className="space-y-8">
      {/* Search */}
      <Card>
        <CardContent className="p-6">
          <Input
            icon={<Search size={20} />}
            placeholder="Search for bills, providers, or services..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </CardContent>
      </Card>

      {/* Recent Bills */}
      {recentBills.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock size={20} />
              Recent Bills
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentBills.map((bill) => (
                <div key={bill.id} className="flex items-center justify-between p-4 rounded-xl border border-grey-200 dark:border-navy-700 hover:bg-grey-50 dark:hover:bg-navy-700 transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-grey-100 dark:bg-navy-700 rounded-xl flex items-center justify-center">
                      <CreditCard className="text-grey-600 dark:text-grey-400" size={20} />
                    </div>
                    <div>
                      <p className="font-medium text-navy-900 dark:text-white">{bill.provider}</p>
                      <p className="text-sm text-grey-600 dark:text-grey-300">
                        Account: {bill.accountNumber}
                      </p>
                      <p className="text-sm text-grey-600 dark:text-grey-300">
                        Due: {new Date(bill.dueDate).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-navy-900 dark:text-white">
                      {formatCurrency(bill.amount)}
                    </p>
                    <span className={getStatusColor(bill.status)}>
                      {bill.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Saved Billers */}
      {savedBillers.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Star size={20} />
              Saved Billers
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4">
              {savedBillers.map((biller) => (
                <button
                  key={biller.id}
                  onClick={() => {
                    const category = billCategories.find(c => c.id === biller.category)
                    const provider = category?.providers.find(p => p.name === biller.provider)
                    if (provider) {
                      setSelectedProvider(provider)
                      setBillForm(prev => ({ ...prev, accountNumber: biller.accountNumber }))
                      setStep(3)
                    }
                  }}
                  className="text-left p-4 rounded-xl border border-grey-200 dark:border-navy-700 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-500/10 transition-all"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-8 h-8 bg-blue-100 dark:bg-blue-500/20 rounded-lg flex items-center justify-center">
                      <Star className="text-blue-500" size={16} />
                    </div>
                    <p className="font-medium text-navy-900 dark:text-white">{biller.name}</p>
                  </div>
                  <p className="text-sm text-grey-600 dark:text-grey-300">{biller.provider}</p>
                  <p className="text-xs text-grey-500 dark:text-grey-400">
                    Last paid: {new Date(biller.lastPaid).toLocaleDateString()}
                  </p>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Bill Categories */}
      <Card>
        <CardHeader>
          <CardTitle>Bill Categories</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {filteredCategories.map((category) => {
              const IconComponent = category.icon
              return (
                <motion.button
                  key={category.id}
                  onClick={() => handleCategorySelect(category.id)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="text-center p-6 rounded-2xl border border-grey-200 dark:border-navy-700 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-500/10 transition-all"
                >
                  <div className={`w-16 h-16 bg-gradient-to-br ${category.color} rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-medium`}>
                    <IconComponent className="text-white" size={32} />
                  </div>
                  <h3 className="font-semibold text-navy-900 dark:text-white mb-2">
                    {category.name}
                  </h3>
                  <p className="text-sm text-grey-600 dark:text-grey-300">
                    {category.providers.length} providers
                  </p>
                </motion.button>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderStep2 = () => {
    const category = billCategories.find(c => c.id === selectedCategory)
    if (!category) return null

    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => setStep(1)}>
              <ArrowLeft size={20} />
            </Button>
            <div>
              <CardTitle>{category.name} Providers</CardTitle>
              <p className="text-grey-600 dark:text-grey-300">Select your service provider</p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4">
            {category.providers.map((provider) => (
              <button
                key={provider.id}
                onClick={() => handleProviderSelect(provider)}
                className="flex items-center gap-4 p-4 rounded-xl border border-grey-200 dark:border-navy-700 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-500/10 transition-all text-left"
              >
                <div className="text-3xl">{provider.logo}</div>
                <div>
                  <p className="font-medium text-navy-900 dark:text-white">{provider.name}</p>
                  <p className="text-sm text-grey-600 dark:text-grey-300 capitalize">{provider.type}</p>
                </div>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  const renderStep3 = () => (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => setStep(2)}>
            <ArrowLeft size={20} />
          </Button>
          <div>
            <CardTitle>Pay {selectedProvider?.name}</CardTitle>
            <p className="text-grey-600 dark:text-grey-300">Enter your bill details</p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <div className="flex items-center gap-4 p-4 bg-grey-50 dark:bg-navy-700 rounded-xl">
            <div className="text-3xl">{selectedProvider?.logo}</div>
            <div>
              <p className="font-medium text-navy-900 dark:text-white">{selectedProvider?.name}</p>
              <p className="text-sm text-grey-600 dark:text-grey-300 capitalize">{selectedProvider?.type} bill payment</p>
            </div>
          </div>

          <Input
            label="Account Number / Customer ID"
            placeholder="Enter your account number"
            value={billForm.accountNumber}
            onChange={handleBillFormChange('accountNumber')}
          />

          <Input
            label="Amount"
            icon={<DollarSign size={20} />}
            placeholder="0.00"
            value={billForm.amount}
            onChange={handleBillFormChange('amount')}
          />

          <Input
            label="Customer Name (Optional)"
            placeholder="Enter customer name"
            value={billForm.customerName}
            onChange={handleBillFormChange('customerName')}
          />

          <Input
            label="Reference (Optional)"
            placeholder="Add a reference note"
            value={billForm.reference}
            onChange={handleBillFormChange('reference')}
          />

          <Button
            onClick={handlePayBill}
            loading={loading}
            className="w-full"
            size="lg"
            disabled={!billForm.accountNumber || !billForm.amount}
          >
            Pay Bill
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
                <h1 className="text-2xl font-bold text-navy-900 dark:text-white">Bill Payments</h1>
                <p className="text-grey-600 dark:text-grey-300">Pay your utilities, telecom, and other bills</p>
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
          </motion.div>
        </div>
      </main>
    </div>
  )
}
