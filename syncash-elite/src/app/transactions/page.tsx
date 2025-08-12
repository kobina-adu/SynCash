'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { 
  Search,
  Filter,
  Download,
  ArrowUpRight,
  ArrowDownLeft,
  Calendar,
  ChevronDown,
  MoreHorizontal,
  Receipt,
  RefreshCw
} from 'lucide-react'
import { formatCurrency, formatDate, getInitials } from '@/lib/utils'
import Link from 'next/link'

// Mock transaction data
const allTransactions = [
  {
    id: 'TXN20240115001',
    type: 'received',
    amount: 2500.00,
    description: 'Salary payment',
    counterparty: 'ABC Company Ltd',
    date: '2024-01-15T14:30:00Z',
    status: 'completed',
    category: 'salary',
    reference: 'SAL/2024/001',
    wallet: 'MTN MoMo'
  },
  {
    id: 'TXN20240115002',
    type: 'sent',
    amount: 150.00,
    description: 'Airtime purchase',
    counterparty: 'MTN Ghana',
    date: '2024-01-15T12:15:00Z',
    status: 'completed',
    category: 'airtime',
    reference: 'AIR/2024/001',
    wallet: 'MTN MoMo'
  },
  {
    id: 'TXN20240114001',
    type: 'received',
    amount: 500.00,
    description: 'Payment from Ama Osei',
    counterparty: 'Ama Osei',
    date: '2024-01-14T16:45:00Z',
    status: 'completed',
    category: 'transfer',
    reference: 'P2P/2024/001',
    wallet: 'Telecel Cash'
  },
  {
    id: 'TXN20240114002',
    type: 'sent',
    amount: 75.00,
    description: 'ECG bill payment',
    counterparty: 'Electricity Company of Ghana',
    date: '2024-01-14T14:20:00Z',
    status: 'completed',
    category: 'bills',
    reference: 'BILL/2024/001',
    wallet: 'GCB Bank'
  },
  {
    id: 'TXN20240113001',
    type: 'sent',
    amount: 200.00,
    description: 'Transfer to Kofi Mensah',
    counterparty: 'Kofi Mensah',
    date: '2024-01-13T11:30:00Z',
    status: 'pending',
    category: 'transfer',
    reference: 'P2P/2024/002',
    wallet: 'AirtelTigo Money'
  },
  {
    id: 'TXN20240112001',
    type: 'received',
    amount: 1200.00,
    description: 'Freelance payment',
    counterparty: 'XYZ Digital Agency',
    date: '2024-01-12T09:15:00Z',
    status: 'completed',
    category: 'freelance',
    reference: 'WORK/2024/001',
    wallet: 'MTN MoMo'
  },
  {
    id: 'TXN20240111001',
    type: 'sent',
    amount: 300.00,
    description: 'Grocery shopping',
    counterparty: 'ShopRite Ghana',
    date: '2024-01-11T18:45:00Z',
    status: 'completed',
    category: 'shopping',
    reference: 'SHOP/2024/001',
    wallet: 'MTN MoMo'
  },
  {
    id: 'TXN20240110001',
    type: 'received',
    amount: 50.00,
    description: 'Cashback reward',
    counterparty: 'SynCash Rewards',
    date: '2024-01-10T12:00:00Z',
    status: 'completed',
    category: 'rewards',
    reference: 'REW/2024/001',
    wallet: 'MTN MoMo'
  }
]

const categories = [
  { value: 'all', label: 'All Categories' },
  { value: 'transfer', label: 'Transfers' },
  { value: 'bills', label: 'Bill Payments' },
  { value: 'airtime', label: 'Airtime' },
  { value: 'salary', label: 'Salary' },
  { value: 'shopping', label: 'Shopping' },
  { value: 'freelance', label: 'Freelance' },
  { value: 'rewards', label: 'Rewards' }
]

const statusOptions = [
  { value: 'all', label: 'All Status' },
  { value: 'completed', label: 'Completed' },
  { value: 'pending', label: 'Pending' },
  { value: 'failed', label: 'Failed' }
]

export default function TransactionsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [selectedStatus, setSelectedStatus] = useState('all')
  const [dateRange, setDateRange] = useState('all')
  const [showFilters, setShowFilters] = useState(false)

  // Filter transactions based on search and filters
  const filteredTransactions = allTransactions.filter(transaction => {
    const matchesSearch = transaction.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         transaction.counterparty.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         transaction.reference.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesCategory = selectedCategory === 'all' || transaction.category === selectedCategory
    const matchesStatus = selectedStatus === 'all' || transaction.status === selectedStatus
    
    return matchesSearch && matchesCategory && matchesStatus
  })

  const getTransactionIcon = (type: string, category: string) => {
    if (type === 'received') {
      return <ArrowDownLeft className="text-green-500" size={20} />
    } else {
      return <ArrowUpRight className="text-blue-500" size={20} />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'status-success'
      case 'pending':
        return 'status-pending'
      case 'failed':
        return 'status-failed'
      default:
        return 'status-pending'
    }
  }

  return (
    <div className="min-h-screen bg-grey-50 dark:bg-navy-900">
      {/* Header */}
      <header className="bg-white dark:bg-navy-800 border-b border-grey-200 dark:border-navy-700 sticky top-0 z-40">
        <div className="section-padding py-4">
          <div className="container-width">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Link href="/dashboard">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-700 rounded-xl flex items-center justify-center">
                    <span className="text-white font-bold text-lg">SC</span>
                  </div>
                </Link>
                <div>
                  <h1 className="text-2xl font-bold text-navy-900 dark:text-white">Transaction History</h1>
                  <p className="text-grey-600 dark:text-grey-300">Track all your payments and transfers</p>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <Button variant="secondary" size="sm">
                  <Download size={16} />
                  Export
                </Button>
                <Button variant="ghost" size="sm">
                  <RefreshCw size={16} />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="section-padding py-8">
        <div className="container-width max-w-4xl">
          {/* Search and Filters */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mb-8"
          >
            <Card>
              <CardContent className="p-6">
                <div className="space-y-4">
                  {/* Search Bar */}
                  <div className="flex gap-4">
                    <div className="flex-1">
                      <Input
                        icon={<Search size={20} />}
                        placeholder="Search transactions, references, or contacts..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                      />
                    </div>
                    <Button
                      variant="secondary"
                      onClick={() => setShowFilters(!showFilters)}
                      className="flex items-center gap-2"
                    >
                      <Filter size={16} />
                      Filters
                      <ChevronDown size={16} className={`transition-transform ${showFilters ? 'rotate-180' : ''}`} />
                    </Button>
                  </div>

                  {/* Filter Options */}
                  {showFilters && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="grid md:grid-cols-3 gap-4 pt-4 border-t border-grey-200 dark:border-navy-700"
                    >
                      <div>
                        <label className="block text-sm font-medium text-navy-900 dark:text-white mb-2">
                          Category
                        </label>
                        <select
                          value={selectedCategory}
                          onChange={(e) => setSelectedCategory(e.target.value)}
                          className="input-field"
                        >
                          {categories.map(category => (
                            <option key={category.value} value={category.value}>
                              {category.label}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-navy-900 dark:text-white mb-2">
                          Status
                        </label>
                        <select
                          value={selectedStatus}
                          onChange={(e) => setSelectedStatus(e.target.value)}
                          className="input-field"
                        >
                          {statusOptions.map(status => (
                            <option key={status.value} value={status.value}>
                              {status.label}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-navy-900 dark:text-white mb-2">
                          Date Range
                        </label>
                        <select
                          value={dateRange}
                          onChange={(e) => setDateRange(e.target.value)}
                          className="input-field"
                        >
                          <option value="all">All Time</option>
                          <option value="today">Today</option>
                          <option value="week">This Week</option>
                          <option value="month">This Month</option>
                          <option value="quarter">This Quarter</option>
                        </select>
                      </div>
                    </motion.div>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Transaction Summary */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="grid md:grid-cols-3 gap-6 mb-8"
          >
            <Card className="text-center p-6">
              <div className="w-12 h-12 bg-blue-50 dark:bg-blue-500/10 rounded-xl flex items-center justify-center mx-auto mb-3">
                <Receipt className="text-blue-500" size={24} />
              </div>
              <h3 className="text-2xl font-bold text-navy-900 dark:text-white mb-1">
                {filteredTransactions.length}
              </h3>
              <p className="text-grey-600 dark:text-grey-300">Total Transactions</p>
            </Card>

            <Card className="text-center p-6">
              <div className="w-12 h-12 bg-green-50 dark:bg-green-500/10 rounded-xl flex items-center justify-center mx-auto mb-3">
                <ArrowDownLeft className="text-green-500" size={24} />
              </div>
              <h3 className="text-2xl font-bold text-green-600 dark:text-green-400 mb-1">
                {formatCurrency(filteredTransactions.filter(t => t.type === 'received').reduce((sum, t) => sum + t.amount, 0))}
              </h3>
              <p className="text-grey-600 dark:text-grey-300">Money Received</p>
            </Card>

            <Card className="text-center p-6">
              <div className="w-12 h-12 bg-red-50 dark:bg-red-500/10 rounded-xl flex items-center justify-center mx-auto mb-3">
                <ArrowUpRight className="text-red-500" size={24} />
              </div>
              <h3 className="text-2xl font-bold text-navy-900 dark:text-white mb-1">
                {formatCurrency(filteredTransactions.filter(t => t.type === 'sent').reduce((sum, t) => sum + t.amount, 0))}
              </h3>
              <p className="text-grey-600 dark:text-grey-300">Money Sent</p>
            </Card>
          </motion.div>

          {/* Transactions List */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <Card>
              <CardHeader>
                <CardTitle>
                  {filteredTransactions.length} Transaction{filteredTransactions.length !== 1 ? 's' : ''}
                  {searchTerm && ` matching "${searchTerm}"`}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {filteredTransactions.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="w-16 h-16 bg-grey-100 dark:bg-navy-700 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Search className="text-grey-400" size={24} />
                    </div>
                    <h3 className="text-lg font-semibold text-navy-900 dark:text-white mb-2">
                      No transactions found
                    </h3>
                    <p className="text-grey-600 dark:text-grey-300">
                      Try adjusting your search or filter criteria
                    </p>
                  </div>
                ) : (
                  <div className="space-y-1">
                    {filteredTransactions.map((transaction, index) => (
                      <motion.div
                        key={transaction.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3, delay: index * 0.05 }}
                        className="flex items-center justify-between p-4 rounded-xl hover:bg-grey-50 dark:hover:bg-navy-700 transition-colors cursor-pointer group"
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 rounded-full bg-grey-100 dark:bg-navy-700 flex items-center justify-center">
                            {getTransactionIcon(transaction.type, transaction.category)}
                          </div>
                          <div>
                            <div className="flex items-center gap-3 mb-1">
                              <p className="font-medium text-navy-900 dark:text-white">
                                {transaction.description}
                              </p>
                              <span className={getStatusColor(transaction.status)}>
                                {transaction.status}
                              </span>
                            </div>
                            <div className="flex items-center gap-4 text-sm text-grey-600 dark:text-grey-300">
                              <span>{transaction.counterparty}</span>
                              <span>•</span>
                              <span>{transaction.wallet}</span>
                              <span>•</span>
                              <span>{formatDate(transaction.date)}</span>
                            </div>
                            <p className="text-xs text-grey-500 dark:text-grey-400 mt-1">
                              Ref: {transaction.reference}
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <p className={`text-lg font-semibold ${
                              transaction.type === 'received' 
                                ? 'text-green-600 dark:text-green-400' 
                                : 'text-navy-900 dark:text-white'
                            }`}>
                              {transaction.type === 'received' ? '+' : '-'}
                              {formatCurrency(transaction.amount)}
                            </p>
                            <p className="text-sm text-grey-600 dark:text-grey-300">
                              {new Date(transaction.date).toLocaleTimeString('en-US', { 
                                hour: '2-digit', 
                                minute: '2-digit' 
                              })}
                            </p>
                          </div>
                          <Button 
                            variant="ghost" 
                            size="sm"
                            className="opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <MoreHorizontal size={16} />
                          </Button>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </main>
    </div>
  )
}
