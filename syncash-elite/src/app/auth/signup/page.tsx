'use client'

import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { 
  User, 
  Mail, 
  Phone, 
  Lock, 
  Eye, 
  EyeOff, 
  ArrowRight,
  CheckCircle,
  Shield
} from 'lucide-react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import toast from 'react-hot-toast'

interface FormData {
  firstName: string
  lastName: string
  email: string
  phone: string
  password: string
  confirmPassword: string
  acceptTerms: boolean
}

interface FormErrors {
  firstName?: string
  lastName?: string
  email?: string
  phone?: string
  password?: string
  confirmPassword?: string
  acceptTerms?: string
}
export default function SignUpPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const role = searchParams.get("role");

  useEffect(() => {
    if (!role) {
      router.replace("/auth/choose-role");
    }
  }, [role, router]);

  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState<FormData>({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    acceptTerms: false
  });
  const [errors, setErrors] = useState<FormErrors>({});

    const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    // Name validation
    if (!formData.firstName.trim()) {
      newErrors.firstName = 'First name is required'
    }
    if (!formData.lastName.trim()) {
      newErrors.lastName = 'Last name is required'
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!formData.email) {
      newErrors.email = 'Email is required'
    } else if (!emailRegex.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address'
    }

    // Phone validation (Ghana format)
    const phoneRegex = /^(\+233|0)[2-9]\d{8}$/
    if (!formData.phone) {
      newErrors.phone = 'Phone number is required'
    } else if (!phoneRegex.test(formData.phone.replace(/\s/g, ''))) {
      newErrors.phone = 'Please enter a valid Ghana phone number'
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required'
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters'
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
      newErrors.password = 'Password must contain uppercase, lowercase, and number'
    }

    // Confirm password validation
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password'
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match'
    }

    // Terms validation
    if (!formData.acceptTerms) {
      newErrors.acceptTerms = 'You must accept the terms and conditions'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

    const handleInputChange = (field: keyof FormData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setFormData(prev => ({ ...prev, [field]: value }))
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }))
    }
  }

    const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      toast.error('Please fix the errors below')
      return
    }

    setLoading(true)
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      toast.success('Account created successfully!')
      router.push('/auth/verify-otp?phone=' + encodeURIComponent(formData.phone))
    } catch (error) {
      toast.error('Failed to create account. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-grey-50 via-white to-blue-50 dark:from-navy-900 dark:via-navy-800 dark:to-navy-900 flex items-center justify-center section-padding py-12">
      <div className="w-full max-w-md">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-8"
        >
          <Link href="/" className="inline-flex items-center gap-3 mb-6">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-700 rounded-2xl flex items-center justify-center shadow-medium">
              <span className="text-white font-bold text-xl">SC</span>
            </div>
            <span className="text-2xl font-bold text-navy-900 dark:text-white">SynCash Elite</span>
          </Link>
        </motion.div>

        {/* Sign Up Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <Card variant="premium">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl">Create Your Account</CardTitle>
              <CardDescription>
                Join thousands of Ghanaians managing their finances smarter
              </CardDescription>
            </CardHeader>

            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Name Fields */}
                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label="First Name"
                    icon={<User size={20} />}
                    placeholder="Enter first name"
                    value={formData.firstName}
                    onChange={handleInputChange('firstName')}
                    error={errors.firstName}
                  />
                  <Input
                    label="Last Name"
                    icon={<User size={20} />}
                    placeholder="Enter last name"
                    value={formData.lastName}
                    onChange={handleInputChange('lastName')}
                    error={errors.lastName}
                  />
                </div>

                {/* Email */}
                <Input
                  label="Email Address"
                  type="email"
                  icon={<Mail size={20} />}
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={handleInputChange('email')}
                  error={errors.email}
                />

                {/* Phone */}
                <Input
                  label="Phone Number"
                  type="tel"
                  icon={<Phone size={20} />}
                  placeholder="0XX XXX XXXX"
                  value={formData.phone}
                  onChange={handleInputChange('phone')}
                  error={errors.phone}
                />

                {/* Password */}
                <Input
                  label="Password"
                  type="password"
                  icon={<Lock size={20} />}
                  placeholder="Create a strong password"
                  value={formData.password}
                  onChange={handleInputChange('password')}
                  error={errors.password}
                  showPasswordToggle
                />

                {/* Confirm Password */}
                <Input
                  label="Confirm Password"
                  type="password"
                  icon={<Lock size={20} />}
                  placeholder="Confirm your password"
                  value={formData.confirmPassword}
                  onChange={handleInputChange('confirmPassword')}
                  error={errors.confirmPassword}
                  showPasswordToggle
                />

                {/* Terms Checkbox */}
                <div className="space-y-2">
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.acceptTerms}
                      onChange={handleInputChange('acceptTerms')}
                      className="mt-1 w-4 h-4 text-blue-500 border-grey-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-grey-600 dark:text-grey-300 leading-relaxed">
                      I agree to the{' '}
                      <Link href="/terms" className="text-blue-500 hover:text-blue-600 font-medium">
                        Terms of Service
                      </Link>{' '}
                      and{' '}
                      <Link href="/privacy" className="text-blue-500 hover:text-blue-600 font-medium">
                        Privacy Policy
                      </Link>
                    </span>
                  </label>
                  {errors.acceptTerms && (
                    <p className="text-sm text-error-500">{errors.acceptTerms}</p>
                  )}
                </div>

                {/* Submit Button */}
                <Button
                  type="submit"
                  className="w-full"
                  size="lg"
                  loading={loading}
                >
                  Create Account
                  <ArrowRight size={20} />
                </Button>
              </form>

              {/* Security Notice */}
              <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-500/10 rounded-xl border border-blue-200 dark:border-blue-500/20">
                <div className="flex items-center gap-3 text-blue-700 dark:text-blue-400">
                  <Shield size={20} />
                  <div>
                    <p className="font-medium text-sm">Your data is secure</p>
                    <p className="text-xs text-blue-600 dark:text-blue-300">
                      We use bank-level encryption to protect your information
                    </p>
                  </div>
                </div>
              </div>

              {/* Sign In Link */}
              <div className="mt-6 text-center">
                <p className="text-grey-600 dark:text-grey-300">
                  Already have an account?{' '}
                  <Link href="/auth/login" className="text-blue-500 hover:text-blue-600 font-medium">
                    Sign in here
                  </Link>
                </p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}
