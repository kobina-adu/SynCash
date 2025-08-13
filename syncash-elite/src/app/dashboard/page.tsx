'use client'

import React, { useState } from 'react'
import Image from 'next/image';
import { motion } from 'framer-motion'
//import RequestPayment from "./RequestPayment";
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { TransactionDetailsModal } from '@/components/ui/TransactionDetailsModal'
import { 
  Eye, 
  EyeOff,
  Send,
  Download,
  CreditCard,
  Plus,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownLeft,
  Bell,
  Settings,
  User,
  MoreHorizontal,
  Smartphone,
  Building2,
  Wallet
} 

from 'lucide-react'
import { formatCurrency, getInitials } from '@/lib/utils'
import { PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts'

// Mock data
const userData = {
  name: 'Kwame Asante',
  email: 'kwame@example.com',
  avatar: null,
  totalBalance: 15847.50,
  monthlyGrowth: 12.5,
  lastLogin: '2024-01-15T10:30:00Z'
}

const walletData = [
  
{
  name: 'MTN MoMo',
  balance: 8500.0,
  percentage: 53.6,
  color: '#FFD700',
  icon: "mtn.jpg",
  logo: "mtn.jpg",
  textColor: 'text-yellow-600 dark:text-yellow-400'
},

  { 
    name: 'Telecel Cash', 
    balance: 4200.00, 
    percentage: 26.5, 
    color: '#FF6B6B', 
    icon: Smartphone,
    logo: 'telecel.png',
    textColor: 'text-red-600 dark:text-red-400'
  },
  { 
    name: 'AirtelTigo', 
    balance: 1847.50, 
    percentage: 11.7, 
    color: '#4ECDC4', 
    icon: Smartphone,
    logo: 'aitel.jpg',

    textColor: 'text-teal-600 dark:text-teal-400'
  },
  { 
    name: 'GCB Bank', 
    balance: 1300.00, 
    percentage: 8.2, 
    color: '#45B7D1', 
    icon: Building2,
    logo: 'gcb.jpg',
    textColor: 'text-blue-600 dark:text-blue-400'
  }
]

const recentTransactions = [
  {
    id: 'TXN001',
    type: 'received' as const,
    amount: 250.00,
    description: 'Payment from Ama Osei',
    date: '2024-01-15T14:30:00Z',
    status: 'completed' as const,
    avatar: 'AO',
    sender: 'Ama Osei',
    method: 'MTN MoMo',
    reference: 'MP240115001',
    fee: 0.00,
    category: 'Transfer',
    notes: 'Payment for graphic design services'
  },
  {
    id: 'TXN002',
    type: 'sent' as const,
    amount: 150.00,
    description: 'Airtime purchase',
    date: '2024-01-15T12:15:00Z',
    status: 'completed' as const,
    avatar: null,
    recipient: 'MTN Ghana',
    method: 'MTN MoMo',
    reference: 'AT240115002',
    fee: 2.50,
    category: 'Airtime',
    notes: 'Monthly airtime top-up'
  },
  {
    id: 'TXN003',
    type: 'received' as const,
    amount: 500.00,
    description: 'Salary advance',
    date: '2024-01-15T09:45:00Z',
    status: 'completed' as const,
    avatar: 'SA',
    sender: 'Sunrise Analytics Ltd',
    method: 'Bank Transfer',
    reference: 'SA240115003',
    fee: 0.00,
    category: 'Salary',
    notes: 'January salary advance payment'
  },
  {
    id: 'TXN004',
    type: 'sent' as const,
    amount: 75.00,
    description: 'ECG bill payment',
    date: '2024-01-14T16:20:00Z',
    status: 'pending' as const,
    avatar: null,
    recipient: 'Electricity Company of Ghana',
    method: 'MTN MoMo',
    reference: 'ECG240114004',
    fee: 1.25,
    category: 'Bills',
    notes: 'December electricity bill payment'
  }
]

const chartData = [
  { month: 'Jul', balance: 12500 },
  { month: 'Aug', balance: 13200 },
  { month: 'Sep', balance: 14100 },
  { month: 'Oct', balance: 13800 },
  { month: 'Nov', balance: 14900 },
  { month: 'Dec', balance: 15847 }
]

import { useRouter } from 'next/navigation'

export default function DashboardPage() {
  const router = useRouter();
  const [balanceVisible, setBalanceVisible] = useState(true)
  const [selectedTransaction, setSelectedTransaction] = useState<typeof recentTransactions[0] | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  const handleTransactionClick = (transaction: typeof recentTransactions[0]) => {
    setSelectedTransaction(transaction)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setSelectedTransaction(null)
  }

  const quickActions = [
    {
      icon: Send,
      label: 'Send Money',
      description: 'Transfer to contacts',
      color: 'from-blue-500 to-blue-600',
      href: '/send'
    },
    {
      icon: Download,
      label: 'Request Money',
      description: 'Request payment',
      color: 'from-green-500 to-green-600',
      href: '/request'
    },
    {
      icon: CreditCard,
      label: 'Pay Bills',
      description: 'Utilities & services',
      color: 'from-purple-500 to-purple-600',
      href: '/bills'
    },
    {
      icon: Plus,
      label: 'Add Wallet',
      description: 'Link new account',
      color: 'from-orange-500 to-orange-600',
      href: '/wallets/add'
    }
  ]

  return (
    <div className="min-h-screen bg-grey-50 dark:bg-navy-900">
      {/* Header */}
      <header className="bg-white dark:bg-navy-800 border-b border-grey-200 dark:border-navy-700 sticky top-0 z-40">
        <div className="section-padding py-4">
          <div className="container-width">
            <div className="flex items-center justify-between">
              {/* Logo */}
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-700 rounded-xl flex items-center justify-center">
                  <span className="text-white font-bold text-lg">SC</span>
                </div>
                <span className="text-xl font-bold text-navy-900 dark:text-white">SynCash Elite</span>
              </div>

              {/* Header Actions */}
              <div className="flex items-center gap-4">
                <Button variant="ghost" size="sm" onClick={() => window.location.href = '/notifications'}>
                  <Bell size={20} />
                </Button>
                <Button variant="ghost" size="sm" onClick={() => window.location.href = '/settings'}>
                  <Settings size={20} />
                </Button>
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white font-semibold cursor-pointer" onClick={() => window.location.href = '/settings'}>
                  {getInitials(userData.name)}
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="section-padding py-8">
        <div className="container-width">
          {/* Welcome Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mb-8"
          >
            <h1 className="text-3xl font-bold text-navy-900 dark:text-white mb-2">
              Welcome back, {userData.name.split(' ')[0]}! 👋
            </h1>
            <p className="text-grey-600 dark:text-grey-300">
              Here's what's happening with your money today
            </p>
          </motion.div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Left Column */}
            <div className="lg:col-span-2 space-y-8">
              {/* Balance Overview */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 }}
              >
                <Card variant="premium" className="bg-gradient-to-br from-blue-500 to-blue-700 text-white border-0">
                  <CardContent className="p-8">
                    <div className="flex items-center justify-between mb-6">
                      <div>
                        <p className="text-blue-100 mb-2">Total Balance</p>
                        <div className="flex items-center gap-4">
                          <h2 className="text-4xl font-bold">
                            {balanceVisible ? formatCurrency(userData.totalBalance) : '₵ ••••••'}
                          </h2>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setBalanceVisible(!balanceVisible)}
                            className="text-white hover:bg-white/10"
                          >
                            {balanceVisible ? <EyeOff size={20} /> : <Eye size={20} />}
                          </Button>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="flex items-center gap-2 text-green-300 mb-2">
                          <TrendingUp size={16} />
                          <span className="text-sm font-medium">+{userData.monthlyGrowth}%</span>
                        </div>
                        <p className="text-blue-100 text-sm">This month</p>
                      </div>
                    </div>

                    {/* Balance Chart */}
                    <div className="h-24">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData}>
                          <Line 
                            type="monotone" 
                            dataKey="balance" 
                            stroke="#ffffff" 
                            strokeWidth={2}
                            dot={false}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>

              {/* Quick Actions */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
              >
                <h3 className="text-xl font-semibold text-navy-900 dark:text-white mb-4">
                  Quick Actions
                </h3>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  {quickActions.map((action, index) => {
                    const IconComponent = action.icon
                    return (
                      <Card 
                        key={index} 
                        variant="hover" 
                        className="p-6 text-center cursor-pointer transition-transform hover:scale-105"
                        onClick={() => {
  if (action.href) {
    router.push(action.href)
  }
}}
                      >
                        <div className={`w-12 h-12 bg-gradient-to-br ${action.color} rounded-xl flex items-center justify-center mx-auto mb-3 shadow-medium`}>
                          <IconComponent className="text-white" size={24} />
                        </div>
                        <h4 className="font-semibold text-navy-900 dark:text-white mb-1">
                          {action.label}
                        </h4>
                        <p className="text-sm text-grey-600 dark:text-grey-300">
                          {action.description}
                        </p>
                      </Card>
                    )
                  })}
                </div>
              </motion.div>

              {/* Recent Transactions */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.3 }}
              >
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle>Recent Transactions</CardTitle>
                      <Button variant="ghost" size="sm" onClick={() => window.location.href = '/transactions'}>
                        View All
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {recentTransactions.map((transaction) => (
                        <div 
                          key={transaction.id} 
                          className="flex items-center justify-between p-4 rounded-xl hover:bg-grey-50 dark:hover:bg-navy-700 transition-colors cursor-pointer"
                          onClick={() => handleTransactionClick(transaction)}
                        >
                          <div className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-full bg-grey-100 dark:bg-navy-700 flex items-center justify-center">
                              {transaction.avatar ? (
                                <span className="font-semibold text-navy-900 dark:text-white">
                                  {transaction.avatar}
                                </span>
                              ) : (
                                <div className={`w-6 h-6 rounded-full ${
                                  transaction.type === 'received' 
                                    ? 'bg-green-500' 
                                    : 'bg-blue-500'
                                }`}>
                                  {transaction.type === 'received' ? (
                                    <ArrowDownLeft className="text-white" size={16} />
                                  ) : (
                                    <ArrowUpRight className="text-white" size={16} />
                                  )}
                                </div>
                              )}
                            </div>
                            <div>
                              <p className="font-medium text-navy-900 dark:text-white">
                                {transaction.description}
                              </p>
                              <p className="text-sm text-grey-600 dark:text-grey-300">
                                {new Date(transaction.date).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className={`font-semibold ${
                              transaction.type === 'received' 
                                ? 'text-green-600 dark:text-green-400' 
                                : 'text-navy-900 dark:text-white'
                            }`}>
                              {transaction.type === 'received' ? '+' : '-'}
                              {formatCurrency(transaction.amount)}
                            </p>
                            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium ${
                              transaction.status === 'completed'
                                ? 'status-success'
                                : 'status-pending'
                            }`}>
                              {transaction.status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </div>

            {/* Right Column */}
            <div className="space-y-8">
              {/* Wallet Breakdown */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.4 }}
              >
                <Card>
                  <CardHeader>
                    <CardTitle>Wallet Breakdown</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      {/* Pie Chart */}
                      <div className="h-48">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={walletData}
                              cx="50%"
                              cy="50%"
                              innerRadius={40}
                              outerRadius={80}
                              paddingAngle={2}
                              dataKey="balance"
                            >
                              {walletData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                              ))}
                            </Pie>
                            <Tooltip 
                              formatter={(value: number) => [formatCurrency(value), 'Balance']}
                            />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>

                      {/* Wallet List */}
                      <div className="space-y-3">
                        {walletData.map((wallet, index) => {
                          return (
                            <div key={index} className="flex items-center justify-between p-3 rounded-xl hover:bg-grey-50 dark:hover:bg-navy-700 transition-colors">
                              <div className="flex items-center gap-3">
                                <div 
                                  className="w-4 h-4 rounded-full"
                                  style={{ backgroundColor: wallet.color }}
                                />
                                <div className="flex items-center gap-3">
                                  <div className="w-10 h-10 rounded-xl flex items-center justify-center">
                                    <Image src={`/images/${wallet.logo}`} height={45} width={45} alt={wallet.name} className="text-lg" />
                                  </div>
                                  <div>
                                    <span className="font-medium text-navy-900 dark:text-white block">
                                      {wallet.name}
                                    </span>
                                    <span className={`text-xs ${wallet.textColor} font-medium`}>
                                      {wallet.name === 'MTN MoMo' ||
                                       wallet.name === 'Telecel Cash' ||
                                       wallet.name === 'AirtelTigo' ? 'Mobile Money' : 'Bank Account'}
                                    </span>
                                  </div>
                                </div>
                              </div>
                              <div className="text-right">
                                <p className="font-semibold text-navy-900 dark:text-white">
                                  {formatCurrency(wallet.balance)}
                                </p>
                                <p className="text-sm text-grey-600 dark:text-grey-300">
                                  {wallet.percentage}%
                                </p>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>

              {/* Quick Stats */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.5 }}
              >
                <Card>
                  <CardHeader>
                    <CardTitle>This Month</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-green-50 dark:bg-green-500/10 rounded-xl flex items-center justify-center">
                            <ArrowDownLeft className="text-green-500" size={20} />
                          </div>
                          <div>
                            <p className="font-medium text-navy-900 dark:text-white">Money In</p>
                            <p className="text-sm text-grey-600 dark:text-grey-300">15 transactions</p>
                          </div>
                        </div>
                        <p className="font-semibold text-green-600 dark:text-green-400">
                          {formatCurrency(8750)}
                        </p>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-red-50 dark:bg-red-500/10 rounded-xl flex items-center justify-center">
                            <ArrowUpRight className="text-red-500" size={20} />
                          </div>
                          <div>
                            <p className="font-medium text-navy-900 dark:text-white">Money Out</p>
                            <p className="text-sm text-grey-600 dark:text-grey-300">23 transactions</p>
                          </div>
                        </div>
                        <p className="font-semibold text-navy-900 dark:text-white">
                          {formatCurrency(6420)}
                        </p>
                      </div>

                      <div className="pt-4 border-t border-grey-200 dark:border-navy-700">
                        <div className="flex items-center justify-between">
                          <p className="font-medium text-navy-900 dark:text-white">Net Change</p>
                          <p className="font-semibold text-green-600 dark:text-green-400">
                            +{formatCurrency(2330)}
                          </p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </div>
          </div>
        </div>
      </main>

      {/* Transaction Details Modal */}
      <TransactionDetailsModal
        transaction={selectedTransaction}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
    </div>
  )
}
