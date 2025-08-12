'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { 
  ArrowLeft,
  Bell,
  CheckCircle,
  AlertTriangle,
  Info,
  TrendingUp,
  CreditCard,
  Smartphone,
  Shield,
  Gift,
  Clock,
  MoreHorizontal,
  Trash2,
  Settings
} from 'lucide-react'
import Link from 'next/link'

const notifications = [
  {
    id: 1,
    type: 'transaction',
    title: 'Payment Received',
    message: 'You received ₵250.00 from Ama Osei',
    time: '2 minutes ago',
    icon: TrendingUp,
    color: 'text-green-500',
    bgColor: 'bg-green-50 dark:bg-green-500/10',
    unread: true
  },
  {
    id: 2,
    type: 'security',
    title: 'New Device Login',
    message: 'Login detected from new device in Accra',
    time: '1 hour ago',
    icon: Shield,
    color: 'text-orange-500',
    bgColor: 'bg-orange-50 dark:bg-orange-500/10',
    unread: true
  },
  {
    id: 3,
    type: 'bill',
    title: 'Bill Payment Successful',
    message: 'ECG bill payment of ₵75.00 completed',
    time: '3 hours ago',
    icon: CreditCard,
    color: 'text-blue-500',
    bgColor: 'bg-blue-50 dark:bg-blue-500/10',
    unread: false
  },
  {
    id: 4,
    type: 'promotion',
    title: 'Cashback Reward',
    message: 'You earned ₵12.50 cashback on your last transaction',
    time: '1 day ago',
    icon: Gift,
    color: 'text-purple-500',
    bgColor: 'bg-purple-50 dark:bg-purple-500/10',
    unread: false
  },
  {
    id: 5,
    type: 'wallet',
    title: 'Wallet Linked Successfully',
    message: 'Your MTN MoMo wallet has been linked',
    time: '2 days ago',
    icon: Smartphone,
    color: 'text-green-500',
    bgColor: 'bg-green-50 dark:bg-green-500/10',
    unread: false
  },
  {
    id: 6,
    type: 'info',
    title: 'System Maintenance',
    message: 'Scheduled maintenance on Jan 20, 2024 from 2-4 AM',
    time: '3 days ago',
    icon: Info,
    color: 'text-blue-500',
    bgColor: 'bg-blue-50 dark:bg-blue-500/10',
    unread: false
  }
]

export default function NotificationsPage() {
  const [notificationList, setNotificationList] = useState(notifications)
  const [filter, setFilter] = useState('all')

  const unreadCount = notificationList.filter(n => n.unread).length

  const markAsRead = (id: number) => {
    setNotificationList(prev => 
      prev.map(n => n.id === id ? { ...n, unread: false } : n)
    )
  }

  const markAllAsRead = () => {
    setNotificationList(prev => 
      prev.map(n => ({ ...n, unread: false }))
    )
  }

  const deleteNotification = (id: number) => {
    setNotificationList(prev => prev.filter(n => n.id !== id))
  }

  const filteredNotifications = notificationList.filter(n => {
    if (filter === 'unread') return n.unread
    if (filter === 'read') return !n.unread
    return true
  })

  return (
    <div className="min-h-screen bg-grey-50 dark:bg-navy-900">
      {/* Header */}
      <header className="bg-white dark:bg-navy-800 border-b border-grey-200 dark:border-navy-700 sticky top-0 z-40">
        <div className="section-padding py-4">
          <div className="container-width">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Link href="/dashboard">
                  <Button variant="ghost" size="sm">
                    <ArrowLeft size={20} />
                  </Button>
                </Link>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-700 rounded-xl flex items-center justify-center">
                    <Bell className="text-white" size={20} />
                  </div>
                  <div>
                    <h1 className="text-xl font-bold text-navy-900 dark:text-white">Notifications</h1>
                    {unreadCount > 0 && (
                      <p className="text-sm text-grey-600 dark:text-grey-300">
                        {unreadCount} unread notification{unreadCount !== 1 ? 's' : ''}
                      </p>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {unreadCount > 0 && (
                  <Button variant="ghost" size="sm" onClick={markAllAsRead}>
                    Mark all read
                  </Button>
                )}
                <Button variant="ghost" size="sm">
                  <Settings size={20} />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="section-padding py-8">
        <div className="container-width max-w-4xl">
          {/* Filter Tabs */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mb-6"
          >
            <div className="flex gap-2 p-1 bg-grey-100 dark:bg-navy-800 rounded-xl">
              {[
                { key: 'all', label: 'All' },
                { key: 'unread', label: 'Unread' },
                { key: 'read', label: 'Read' }
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setFilter(tab.key)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    filter === tab.key
                      ? 'bg-white dark:bg-navy-700 text-navy-900 dark:text-white shadow-sm'
                      : 'text-grey-600 dark:text-grey-300 hover:text-navy-900 dark:hover:text-white'
                  }`}
                >
                  {tab.label}
                  {tab.key === 'unread' && unreadCount > 0 && (
                    <span className="ml-2 px-2 py-0.5 bg-blue-500 text-white text-xs rounded-full">
                      {unreadCount}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </motion.div>

          {/* Notifications List */}
          <div className="space-y-4">
            {filteredNotifications.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
              >
                <Card className="p-12 text-center">
                  <Bell className="w-16 h-16 text-grey-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-navy-900 dark:text-white mb-2">
                    No notifications
                  </h3>
                  <p className="text-grey-600 dark:text-grey-300">
                    {filter === 'unread' 
                      ? "You're all caught up! No unread notifications."
                      : "You don't have any notifications yet."
                    }
                  </p>
                </Card>
              </motion.div>
            ) : (
              filteredNotifications.map((notification, index) => {
                const IconComponent = notification.icon
                return (
                  <motion.div
                    key={notification.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: index * 0.1 }}
                  >
                    <Card 
                      variant="hover" 
                      className={`p-4 ${notification.unread ? 'ring-2 ring-blue-500/20 bg-blue-50/50 dark:bg-blue-500/5' : ''}`}
                    >
                      <div className="flex items-start gap-4">
                        <div className={`w-12 h-12 ${notification.bgColor} rounded-xl flex items-center justify-center flex-shrink-0`}>
                          <IconComponent className={notification.color} size={20} />
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <h3 className="font-semibold text-navy-900 dark:text-white">
                                  {notification.title}
                                </h3>
                                {notification.unread && (
                                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                                )}
                              </div>
                              <p className="text-grey-600 dark:text-grey-300 text-sm mb-2">
                                {notification.message}
                              </p>
                              <div className="flex items-center gap-2 text-xs text-grey-500 dark:text-grey-400">
                                <Clock size={12} />
                                <span>{notification.time}</span>
                              </div>
                            </div>
                            
                            <div className="flex items-center gap-2">
                              {notification.unread && (
                                <Button 
                                  variant="ghost" 
                                  size="sm"
                                  onClick={() => markAsRead(notification.id)}
                                  className="text-xs"
                                >
                                  <CheckCircle size={16} />
                                </Button>
                              )}
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => deleteNotification(notification.id)}
                                className="text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-500/10"
                              >
                                <Trash2 size={16} />
                              </Button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </Card>
                  </motion.div>
                )
              })
            )}
          </div>

          {/* Quick Actions */}
          {filteredNotifications.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="mt-8"
            >
              <Card className="p-6 text-center bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-500/10 dark:to-purple-500/10 border-blue-200 dark:border-blue-500/20">
                <h3 className="font-semibold text-navy-900 dark:text-white mb-2">
                  Stay Updated
                </h3>
                <p className="text-grey-600 dark:text-grey-300 text-sm mb-4">
                  Manage your notification preferences to stay informed about what matters most
                </p>
                <Button variant="primary" size="sm">
                  <Settings size={16} />
                  Notification Settings
                </Button>
              </Card>
            </motion.div>
          )}
        </div>
      </main>
    </div>
  )
}
