'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { 
  ArrowRight, 
  Shield, 
  Zap, 
  Users, 
  Smartphone,
  Star,
  CheckCircle,
  Globe,
  CreditCard,
  TrendingUp
} from 'lucide-react'
import Link from 'next/link'

const features = [
  {
    icon: Zap,
    title: 'Instant Transfers',
    description: 'Send money across all networks in seconds with real-time processing',
    color: 'from-yellow-400 to-orange-500'
  },
  {
    icon: Shield,
    title: 'Bank-Level Security',
    description: 'Military-grade encryption and biometric authentication protect your funds',
    color: 'from-green-400 to-emerald-500'
  },
  {
    icon: Globe,
    title: 'Universal Access',
    description: 'Connect MTN MoMo, Telecel, AirtelTigo, and all major banks in one app',
    color: 'from-blue-400 to-indigo-500'
  },
  {
    icon: TrendingUp,
    title: 'Smart Analytics',
    description: 'Track spending, analyze patterns, and optimize your financial health',
    color: 'from-purple-400 to-pink-500'
  }
]

const stats = [
  { label: 'Active Users', value: '2M+' },
  { label: 'Daily Transactions', value: '500K+' },
  { label: 'Partner Networks', value: '15+' },
  { label: 'Uptime', value: '99.9%' }
]

const testimonials = [
  {
    name: 'Kwame Asante',
    role: 'Small Business Owner',
    content: 'SynCash Elite transformed how I manage my business payments. Everything is so much easier now.',
    rating: 5
  },
  {
    name: 'Ama Osei',
    role: 'University Student',
    content: 'Finally, one app for all my mobile money needs. The interface is beautiful and so intuitive.',
    rating: 5
  },
  {
    name: 'Kofi Mensah',
    role: 'Freelancer',
    content: 'The instant transfers and low fees make this my go-to payment solution. Highly recommended!',
    rating: 5
  }
]

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-grey-50 via-white to-blue-50 dark:from-navy-900 dark:via-navy-800 dark:to-navy-900">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Background Elements */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5" />
        <div className="absolute top-20 left-10 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse delay-1000" />
        
        <div className="relative section-padding py-20 lg:py-32">
          <div className="container-width">
            <div className="text-center max-w-4xl mx-auto">
              {/* Logo */}
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="flex items-center justify-center gap-4 mb-8"
              >
                <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-700 rounded-3xl flex items-center justify-center shadow-strong">
                  <span className="text-white font-bold text-2xl">SC</span>
                </div>
                <h1 className="text-4xl lg:text-5xl font-bold text-navy-900 dark:text-white">
                  SynCash <span className="gradient-text">Elite</span>
                </h1>
              </motion.div>

              {/* Hero Text */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
                className="space-y-6 mb-12"
              >
                <h2 className="text-5xl lg:text-7xl font-bold text-navy-900 dark:text-white leading-tight">
                  Switch Less,
                  <br />
                  <span className="gradient-text">Do More</span>
                </h2>
                <p className="text-xl lg:text-2xl text-grey-600 dark:text-grey-300 max-w-3xl mx-auto leading-relaxed">
                  The most advanced unified payment ecosystem for Ghana. Manage all your mobile money, 
                  bank accounts, and payments from one premium platform.
                </p>
              </motion.div>

              {/* CTA Buttons */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.4 }}
                className="flex flex-col sm:flex-row gap-4 justify-center mb-16"
              >
                <Link href="/onboarding">
                  <Button size="lg" className="text-lg px-8 py-4 shadow-strong hover:shadow-xl">
                    Get Started Free
                    <ArrowRight size={24} />
                  </Button>
                </Link>
                <Link href="/auth/login">
                  <Button variant="secondary" size="lg" className="text-lg px-8 py-4">
                    Sign In
                  </Button>
                </Link>
              </motion.div>

              {/* Stats */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.6 }}
                className="grid grid-cols-2 lg:grid-cols-4 gap-8"
              >
                {stats.map((stat, index) => (
                  <div key={index} className="text-center">
                    <div className="text-3xl lg:text-4xl font-bold gradient-text mb-2">
                      {stat.value}
                    </div>
                    <div className="text-grey-600 dark:text-grey-400 font-medium">
                      {stat.label}
                    </div>
                  </div>
                ))}
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="section-padding py-20">
        <div className="container-width">
          <div className="text-center mb-16">
            <h3 className="text-4xl font-bold text-navy-900 dark:text-white mb-4">
              Why Choose SynCash Elite?
            </h3>
            <p className="text-xl text-grey-600 dark:text-grey-300 max-w-2xl mx-auto">
              Experience the future of mobile money with features designed for the modern Ghanaian
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => {
              const IconComponent = feature.icon
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  viewport={{ once: true }}
                >
                  <Card variant="hover" className="text-center h-full p-8">
                    <div className={`w-16 h-16 bg-gradient-to-br ${feature.color} rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-medium`}>
                      <IconComponent className="text-white" size={32} />
                    </div>
                    <h4 className="text-xl font-semibold text-navy-900 dark:text-white mb-3">
                      {feature.title}
                    </h4>
                    <p className="text-grey-600 dark:text-grey-300 leading-relaxed">
                      {feature.description}
                    </p>
                  </Card>
                </motion.div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="section-padding py-20 bg-grey-50 dark:bg-navy-800">
        <div className="container-width">
          <div className="text-center mb-16">
            <h3 className="text-4xl font-bold text-navy-900 dark:text-white mb-4">
              Trusted by Thousands
            </h3>
            <p className="text-xl text-grey-600 dark:text-grey-300">
              See what our users are saying about SynCash Elite
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <Card className="p-6 h-full">
                  <div className="flex items-center gap-1 mb-4">
                    {[...Array(testimonial.rating)].map((_, i) => (
                      <Star key={i} className="text-yellow-400 fill-current" size={20} />
                    ))}
                  </div>
                  <p className="text-grey-600 dark:text-grey-300 mb-6 leading-relaxed">
                    "{testimonial.content}"
                  </p>
                  <div>
                    <div className="font-semibold text-navy-900 dark:text-white">
                      {testimonial.name}
                    </div>
                    <div className="text-sm text-grey-500 dark:text-grey-400">
                      {testimonial.role}
                    </div>
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="section-padding py-20">
        <div className="container-width">
          <Card variant="premium" className="text-center bg-gradient-to-br from-blue-500 to-blue-700 text-white border-0">
            <div className="space-y-6">
              <h3 className="text-4xl font-bold">
                Ready to Transform Your Payments?
              </h3>
              <p className="text-xl text-blue-100 max-w-2xl mx-auto">
                Join millions of Ghanaians who have already switched to the smarter way of managing money
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
                <Link href="/onboarding">
                  <Button variant="secondary" size="lg" className="bg-white text-blue-600 hover:bg-grey-50">
                    Start Your Journey
                    <ArrowRight size={24} />
                  </Button>
                </Link>
              </div>
            </div>
          </Card>
        </div>
      </section>
    </div>
  )
}
