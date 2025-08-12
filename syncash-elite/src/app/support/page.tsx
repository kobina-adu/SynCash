'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { 
  HelpCircle,
  MessageCircle,
  Phone,
  Mail,
  Search,
  ChevronDown,
  ChevronUp,
  ArrowLeft,
  Send,
  Clock,
  CheckCircle,
  AlertCircle,
  Star,
  ThumbsUp,
  ThumbsDown,
  Book,
  Video,
  FileText,
  Headphones
} from 'lucide-react'
import Link from 'next/link'
import toast from 'react-hot-toast'

// FAQ Data
const faqCategories = [
  {
    id: 'getting-started',
    name: 'Getting Started',
    icon: Book,
    questions: [
      {
        id: 1,
        question: 'How do I create a SynCash Elite account?',
        answer: 'Creating an account is simple! Download the app, tap "Sign Up", enter your details including phone number and email, verify your phone with the OTP code sent to you, and you\'re ready to start using SynCash Elite.'
      },
      {
        id: 2,
        question: 'How do I link my mobile money accounts?',
        answer: 'Go to Settings > Linked Accounts > Add New Account. Select your mobile money provider (MTN MoMo, Telecel Cash, or AirtelTigo Money), enter your phone number and PIN, then verify with the OTP sent to your registered number.'
      },
      {
        id: 3,
        question: 'Is SynCash Elite free to use?',
        answer: 'Yes! Creating an account and linking your wallets is completely free. We only charge small transaction fees when you send money or pay bills, which are clearly displayed before you confirm any transaction.'
      }
    ]
  },
  {
    id: 'transactions',
    name: 'Transactions',
    icon: FileText,
    questions: [
      {
        id: 4,
        question: 'How do I send money to someone?',
        answer: 'Tap "Send Money" from your dashboard, select the wallet to send from, enter the recipient\'s phone number and amount, add an optional message, review the details, and confirm. The money will be sent instantly.'
      },
      {
        id: 5,
        question: 'What are the transaction limits?',
        answer: 'Daily limits vary by wallet type: Mobile Money accounts have a ₵5,000 daily limit, while bank accounts have a ₵20,000 daily limit. Monthly limits are ₵50,000 for mobile money and ₵200,000 for bank accounts.'
      },
      {
        id: 6,
        question: 'How long do transactions take?',
        answer: 'Most transactions are processed instantly. Bank transfers may take 1-3 business days depending on the receiving bank. You\'ll get real-time notifications for all transaction updates.'
      }
    ]
  },
  {
    id: 'security',
    name: 'Security',
    icon: AlertCircle,
    questions: [
      {
        id: 7,
        question: 'How secure is my money and data?',
        answer: 'We use bank-level security including 256-bit SSL encryption, two-factor authentication, and biometric login. Your PINs are never stored on our servers, and all transactions require your authorization.'
      },
      {
        id: 8,
        question: 'What should I do if I suspect fraud?',
        answer: 'Immediately contact our support team at +233 30 123 4567 or email security@syncash.com. We\'ll freeze your account temporarily while we investigate and help recover any lost funds.'
      },
      {
        id: 9,
        question: 'Can I set spending limits?',
        answer: 'Yes! Go to Settings > Security > Spending Limits to set daily, weekly, or monthly limits for different types of transactions. This helps you stay in control of your spending.'
      }
    ]
  }
]

const supportChannels = [
  {
    id: 'chat',
    name: 'Live Chat',
    description: 'Chat with our support team',
    icon: MessageCircle,
    availability: '24/7',
    responseTime: 'Usually within 2 minutes',
    color: 'from-blue-500 to-blue-600'
  },
  {
    id: 'phone',
    name: 'Phone Support',
    description: 'Call us directly',
    icon: Phone,
    availability: 'Mon-Fri, 8AM-6PM',
    responseTime: 'Immediate',
    color: 'from-green-500 to-green-600',
    contact: '+233 30 123 4567'
  },
  {
    id: 'email',
    name: 'Email Support',
    description: 'Send us an email',
    icon: Mail,
    availability: '24/7',
    responseTime: 'Within 4 hours',
    color: 'from-purple-500 to-purple-600',
    contact: 'support@syncash.com'
  }
]

const helpResources = [
  {
    id: 'video-tutorials',
    name: 'Video Tutorials',
    description: 'Step-by-step video guides',
    icon: Video,
    count: '25+ videos',
    color: 'bg-red-500'
  },
  {
    id: 'user-guide',
    name: 'User Guide',
    description: 'Complete app documentation',
    icon: Book,
    count: '50+ articles',
    color: 'bg-blue-500'
  },
  {
    id: 'webinars',
    name: 'Webinars',
    description: 'Live training sessions',
    icon: Headphones,
    count: 'Weekly sessions',
    color: 'bg-green-500'
  }
]

export default function SupportPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null)
  const [selectedCategory, setSelectedCategory] = useState('getting-started')
  const [chatMessage, setChatMessage] = useState('')
  const [showChat, setShowChat] = useState(false)
  const [loading, setLoading] = useState(false)

  const filteredFaqs = faqCategories
    .find(cat => cat.id === selectedCategory)
    ?.questions.filter(faq =>
      faq.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
      faq.answer.toLowerCase().includes(searchTerm.toLowerCase())
    ) || []

  const handleFaqToggle = (id: number) => {
    setExpandedFaq(expandedFaq === id ? null : id)
  }

  const handleStartChat = () => {
    setShowChat(true)
    toast.success('Connected to support chat!')
  }

  const handleSendMessage = async () => {
    if (!chatMessage.trim()) return

    setLoading(true)
    try {
      // Simulate sending message
      await new Promise(resolve => setTimeout(resolve, 1000))
      setChatMessage('')
      toast.success('Message sent! Our team will respond shortly.')
    } catch (error) {
      toast.error('Failed to send message')
    } finally {
      setLoading(false)
    }
  }

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
                <h1 className="text-2xl font-bold text-navy-900 dark:text-white">Help & Support</h1>
                <p className="text-grey-600 dark:text-grey-300">Get help and find answers to your questions</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="section-padding py-8">
        <div className="container-width max-w-6xl">
          {/* Hero Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-12"
          >
            <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center mx-auto mb-6">
              <HelpCircle className="text-white" size={40} />
            </div>
            <h2 className="text-4xl font-bold text-navy-900 dark:text-white mb-4">
              How can we help you?
            </h2>
            <p className="text-xl text-grey-600 dark:text-grey-300 max-w-2xl mx-auto mb-8">
              Search our knowledge base or get in touch with our support team
            </p>

            {/* Search Bar */}
            <div className="max-w-2xl mx-auto">
              <Input
                icon={<Search size={20} />}
                placeholder="Search for help articles, guides, or common questions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="text-lg py-4"
              />
            </div>
          </motion.div>

          {/* Support Channels */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="mb-12"
          >
            <h3 className="text-2xl font-bold text-navy-900 dark:text-white mb-6 text-center">
              Get Support
            </h3>
            <div className="grid md:grid-cols-3 gap-6">
              {supportChannels.map((channel) => {
                const IconComponent = channel.icon
                return (
                  <Card key={channel.id} variant="hover" className="text-center">
                    <CardContent className="p-8">
                      <div className={`w-16 h-16 bg-gradient-to-br ${channel.color} rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-medium`}>
                        <IconComponent className="text-white" size={32} />
                      </div>
                      <h4 className="text-xl font-semibold text-navy-900 dark:text-white mb-2">
                        {channel.name}
                      </h4>
                      <p className="text-grey-600 dark:text-grey-300 mb-4">
                        {channel.description}
                      </p>
                      <div className="space-y-2 mb-6">
                        <div className="flex items-center justify-center gap-2 text-sm">
                          <Clock size={14} />
                          <span className="text-grey-600 dark:text-grey-300">{channel.availability}</span>
                        </div>
                        <p className="text-sm text-grey-600 dark:text-grey-300">
                          {channel.responseTime}
                        </p>
                        {channel.contact && (
                          <p className="text-sm font-medium text-navy-900 dark:text-white">
                            {channel.contact}
                          </p>
                        )}
                      </div>
                      <Button
                        onClick={channel.id === 'chat' ? handleStartChat : undefined}
                        className="w-full"
                      >
                        {channel.id === 'chat' ? 'Start Chat' : 
                         channel.id === 'phone' ? 'Call Now' : 'Send Email'}
                      </Button>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </motion.div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* FAQ Section */}
            <div className="lg:col-span-2">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
              >
                <Card>
                  <CardHeader>
                    <CardTitle>Frequently Asked Questions</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {/* Category Tabs */}
                    <div className="flex flex-wrap gap-2 mb-6">
                      {faqCategories.map((category) => {
                        const IconComponent = category.icon
                        return (
                          <button
                            key={category.id}
                            onClick={() => setSelectedCategory(category.id)}
                            className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-all ${
                              selectedCategory === category.id
                                ? 'bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400'
                                : 'text-grey-600 dark:text-grey-400 hover:bg-grey-50 dark:hover:bg-navy-700'
                            }`}
                          >
                            <IconComponent size={16} />
                            {category.name}
                          </button>
                        )
                      })}
                    </div>

                    {/* FAQ Items */}
                    <div className="space-y-4">
                      {filteredFaqs.map((faq) => (
                        <div key={faq.id} className="border border-grey-200 dark:border-navy-700 rounded-xl">
                          <button
                            onClick={() => handleFaqToggle(faq.id)}
                            className="w-full flex items-center justify-between p-4 text-left hover:bg-grey-50 dark:hover:bg-navy-700 transition-colors"
                          >
                            <span className="font-medium text-navy-900 dark:text-white pr-4">
                              {faq.question}
                            </span>
                            {expandedFaq === faq.id ? (
                              <ChevronUp className="text-grey-400 flex-shrink-0" size={20} />
                            ) : (
                              <ChevronDown className="text-grey-400 flex-shrink-0" size={20} />
                            )}
                          </button>
                          {expandedFaq === faq.id && (
                            <motion.div
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: 'auto' }}
                              exit={{ opacity: 0, height: 0 }}
                              className="px-4 pb-4"
                            >
                              <p className="text-grey-600 dark:text-grey-300 leading-relaxed">
                                {faq.answer}
                              </p>
                              <div className="flex items-center gap-4 mt-4 pt-4 border-t border-grey-200 dark:border-navy-700">
                                <span className="text-sm text-grey-600 dark:text-grey-300">Was this helpful?</span>
                                <div className="flex gap-2">
                                  <Button variant="ghost" size="sm">
                                    <ThumbsUp size={16} />
                                  </Button>
                                  <Button variant="ghost" size="sm">
                                    <ThumbsDown size={16} />
                                  </Button>
                                </div>
                              </div>
                            </motion.div>
                          )}
                        </div>
                      ))}
                    </div>

                    {filteredFaqs.length === 0 && (
                      <div className="text-center py-8">
                        <Search className="text-grey-400 mx-auto mb-4" size={48} />
                        <h3 className="text-lg font-semibold text-navy-900 dark:text-white mb-2">
                          No results found
                        </h3>
                        <p className="text-grey-600 dark:text-grey-300">
                          Try adjusting your search terms or browse different categories
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Help Resources */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.3 }}
              >
                <Card>
                  <CardHeader>
                    <CardTitle>Help Resources</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {helpResources.map((resource) => {
                        const IconComponent = resource.icon
                        return (
                          <button
                            key={resource.id}
                            className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-grey-50 dark:hover:bg-navy-700 transition-colors text-left"
                          >
                            <div className={`w-10 h-10 ${resource.color} rounded-xl flex items-center justify-center`}>
                              <IconComponent className="text-white" size={20} />
                            </div>
                            <div>
                              <p className="font-medium text-navy-900 dark:text-white">{resource.name}</p>
                              <p className="text-sm text-grey-600 dark:text-grey-300">{resource.description}</p>
                              <p className="text-xs text-blue-600 dark:text-blue-400">{resource.count}</p>
                            </div>
                          </button>
                        )
                      })}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>

              {/* Quick Contact */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.4 }}
              >
                <Card className="bg-gradient-to-br from-blue-500 to-blue-700 text-white border-0">
                  <CardContent className="p-6 text-center">
                    <MessageCircle className="mx-auto mb-4" size={32} />
                    <h3 className="text-lg font-semibold mb-2">Still need help?</h3>
                    <p className="text-blue-100 mb-4 text-sm">
                      Our support team is here to help you 24/7
                    </p>
                    <Button variant="secondary" onClick={handleStartChat} className="w-full">
                      Contact Support
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            </div>
          </div>
        </div>
      </main>

      {/* Chat Widget */}
      {showChat && (
        <div className="fixed bottom-4 right-4 w-80 bg-white dark:bg-navy-800 rounded-2xl shadow-strong border border-grey-200 dark:border-navy-700 z-50">
          <div className="flex items-center justify-between p-4 border-b border-grey-200 dark:border-navy-700">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                <CheckCircle className="text-white" size={16} />
              </div>
              <div>
                <p className="font-medium text-navy-900 dark:text-white">Support Chat</p>
                <p className="text-xs text-green-600 dark:text-green-400">Online</p>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setShowChat(false)}>
              ×
            </Button>
          </div>
          
          <div className="p-4 h-64 overflow-y-auto">
            <div className="bg-grey-100 dark:bg-navy-700 rounded-xl p-3 mb-4">
              <p className="text-sm text-navy-900 dark:text-white">
                Hi! I'm here to help. What can I assist you with today?
              </p>
            </div>
          </div>
          
          <div className="p-4 border-t border-grey-200 dark:border-navy-700">
            <div className="flex gap-2">
              <Input
                placeholder="Type your message..."
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              />
              <Button onClick={handleSendMessage} loading={loading} size="sm">
                <Send size={16} />
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
