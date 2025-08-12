'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { 
  Wallet, 
  Shield, 
  Zap, 
  Users, 
  ArrowRight, 
  ArrowLeft,
  Smartphone,
  CreditCard,
  Globe
} from 'lucide-react'
import Link from 'next/link'

const onboardingSlides = [
  {
    id: 1,
    icon: Wallet,
    title: 'Welcome to SynCash Elite',
    subtitle: 'Your Premium E-Payment Ecosystem',
    description: 'Experience the future of mobile money management in Ghana. Unified, secure, and incredibly simple.',
    color: 'from-blue-500 to-blue-700',
    bgColor: 'bg-blue-50 dark:bg-blue-500/10'
  },
  {
    id: 2,
    icon: Zap,
    title: 'Unified Balance Management',
    subtitle: 'All Your Money, One Place',
    description: 'Connect MTN MoMo, Telecel Cash, AirtelTigo Money, and bank accounts. View and manage everything from a single dashboard.',
    color: 'from-emerald-500 to-emerald-700',
    bgColor: 'bg-emerald-50 dark:bg-emerald-500/10'
  },
  {
    id: 3,
    icon: Shield,
    title: 'Bank-Level Security',
    subtitle: 'Your Money, Protected',
    description: 'Military-grade encryption, biometric authentication, and real-time fraud detection keep your finances secure.',
    color: 'from-purple-500 to-purple-700',
    bgColor: 'bg-purple-50 dark:bg-purple-500/10'
  },
  {
    id: 4,
    icon: Smartphone,
    title: 'Instant Transactions',
    subtitle: 'Send Money in Seconds',
    description: 'Transfer money between accounts, pay bills, buy airtime, and send to friends instantly with just a few taps.',
    color: 'from-orange-500 to-orange-700',
    bgColor: 'bg-orange-50 dark:bg-orange-500/10'
  },
  {
    id: 5,
    icon: Users,
    title: 'Merchant Solutions',
    subtitle: 'Built for Business',
    description: 'Accept payments, manage inventory, track sales, and grow your business with our comprehensive merchant tools.',
    color: 'from-indigo-500 to-indigo-700',
    bgColor: 'bg-indigo-50 dark:bg-indigo-500/10'
  }
]

export default function OnboardingPage() {
  const [currentSlide, setCurrentSlide] = useState(0)

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % onboardingSlides.length)
  }

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + onboardingSlides.length) % onboardingSlides.length)
  }

  const goToSlide = (index: number) => {
    setCurrentSlide(index)
  }

  const currentSlideData = onboardingSlides[currentSlide]
  const IconComponent = currentSlideData.icon

  return (
    <div className="min-h-screen bg-gradient-to-br from-grey-50 to-white dark:from-navy-900 dark:to-navy-800 flex items-center justify-center section-padding">
      <div className="container-width">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex items-center justify-center gap-3 mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-700 rounded-2xl flex items-center justify-center shadow-medium">
                <span className="text-white font-bold text-xl">SC</span>
              </div>
              <h1 className="text-2xl font-bold text-navy-900 dark:text-white">SynCash Elite</h1>
            </div>
          </div>

          {/* Main Carousel */}
          <Card variant="premium" className="relative overflow-hidden">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentSlide}
                initial={{ opacity: 0, x: 300 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -300 }}
                transition={{ duration: 0.3, ease: 'easeInOut' }}
                className="text-center py-12 px-8"
              >
                {/* Icon */}
                <div className={`w-24 h-24 ${currentSlideData.bgColor} rounded-3xl flex items-center justify-center mx-auto mb-8 shadow-soft`}>
                  <div className={`w-16 h-16 bg-gradient-to-br ${currentSlideData.color} rounded-2xl flex items-center justify-center`}>
                    <IconComponent className="text-white" size={32} />
                  </div>
                </div>

                {/* Content */}
                <div className="space-y-4 mb-12">
                  <h2 className="text-4xl font-bold text-navy-900 dark:text-white">
                    {currentSlideData.title}
                  </h2>
                  <p className="text-xl font-semibold bg-gradient-to-r from-blue-500 to-blue-700 bg-clip-text text-transparent">
                    {currentSlideData.subtitle}
                  </p>
                  <p className="text-lg text-grey-600 dark:text-grey-300 max-w-2xl mx-auto leading-relaxed">
                    {currentSlideData.description}
                  </p>
                </div>
              </motion.div>
            </AnimatePresence>

            {/* Navigation Dots */}
            <div className="flex justify-center space-x-3 mb-8">
              {onboardingSlides.map((_, index) => (
                <button
                  key={index}
                  onClick={() => goToSlide(index)}
                  className={`w-3 h-3 rounded-full transition-all duration-200 ${
                    index === currentSlide
                      ? 'bg-blue-500 w-8'
                      : 'bg-grey-300 dark:bg-grey-600 hover:bg-grey-400 dark:hover:bg-grey-500'
                  }`}
                />
              ))}
            </div>

            {/* Navigation Buttons */}
            <div className="flex justify-between items-center">
              <Button
                variant="ghost"
                onClick={prevSlide}
                disabled={currentSlide === 0}
                className="flex items-center gap-2"
              >
                <ArrowLeft size={20} />
                Previous
              </Button>

              <div className="flex gap-4">
                <Link href="/auth/login">
                  <Button variant="secondary">
                    Skip
                  </Button>
                </Link>
                
                {currentSlide === onboardingSlides.length - 1 ? (
                  <Link href="/auth/signup">
                    <Button variant="primary" className="flex items-center gap-2">
                      Get Started
                      <ArrowRight size={20} />
                    </Button>
                  </Link>
                ) : (
                  <Button
                    variant="primary"
                    onClick={nextSlide}
                    className="flex items-center gap-2"
                  >
                    Next
                    <ArrowRight size={20} />
                  </Button>
                )}
              </div>
            </div>
          </Card>

          {/* Features Preview */}
          <div className="grid md:grid-cols-3 gap-6 mt-12">
            <Card variant="hover" className="text-center p-6">
              <div className="w-12 h-12 bg-blue-50 dark:bg-blue-500/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                <CreditCard className="text-blue-500" size={24} />
              </div>
              <h3 className="font-semibold text-navy-900 dark:text-white mb-2">Multi-Provider</h3>
              <p className="text-sm text-grey-600 dark:text-grey-300">Support for all major mobile money and banking services</p>
            </Card>

            <Card variant="hover" className="text-center p-6">
              <div className="w-12 h-12 bg-emerald-50 dark:bg-emerald-500/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Zap className="text-emerald-500" size={24} />
              </div>
              <h3 className="font-semibold text-navy-900 dark:text-white mb-2">Lightning Fast</h3>
              <p className="text-sm text-grey-600 dark:text-grey-300">Instant transactions and real-time balance updates</p>
            </Card>

            <Card variant="hover" className="text-center p-6">
              <div className="w-12 h-12 bg-purple-50 dark:bg-purple-500/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Globe className="text-purple-500" size={24} />
              </div>
              <h3 className="font-semibold text-navy-900 dark:text-white mb-2">24/7 Available</h3>
              <p className="text-sm text-grey-600 dark:text-grey-300">Round-the-clock service with dedicated support</p>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
