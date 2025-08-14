'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { 
  Mail, 
  Lock, 
  ArrowRight,
  Fingerprint,
  Shield
} from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import toast, { Toaster } from 'react-hot-toast'

import { signIn } from '@/lib/auth-client'

interface FormData {
  email: string
  password: string
  rememberMe: boolean
}

interface FormErrors {
  email?: string
  password?: string
}

export default function LoginPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState<FormData>({
    email: '',
    password: '',
    rememberMe: false
  })
  const devDemo = { email: 'dev@syncash.com', password: 'Dev123!' }
  const [errors, setErrors] = useState<FormErrors>({})

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!formData.email) {
      newErrors.email = 'Email is required'
    } else if (!emailRegex.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address'
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required'
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
    if (errors[field as keyof FormErrors]) {
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
      if (formData.email === 'dev@syncash.com' && formData.password === 'Dev123!') {
        router.push('/developer-dashboard');
        toast.success('Welcome, Developer!');
        return;
      }

      //  await signIn.email(
      //     {
      //         email: formData.email,
      //         password: formData.password,
      //         rememberMe: formData.rememberMe,
      //     },
      //     {
      //       onRequest: (ctx) => {
      //         setLoading(true);
      //       },
      //       onResponse: (ctx) => {
      //         setLoading(false);
      //         toast.success('Login successful!');
      //         router.push("/dashboard");
      //       },
      //     },
      //   );

      if (formData.email === 'demo@syncash.com' && formData.password === 'Demo123!') {
        toast.success('Welcome, ' + formData.email + '!');
        router.push('/dashboard');
        return;
      }
      toast.error('Invalid email or password')
    } catch (error) {
      toast.error('Invalid email or password')
      return
    } finally {
      setLoading(false)
    }
  }

  const handleBiometricLogin = async () => {
    toast.success('Biometric login coming soon!')
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

        {/* Login Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <Card variant="premium">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl">Welcome Back</CardTitle>
              <CardDescription>
                Sign in to access your SynCash Elite account
              </CardDescription>
            </CardHeader>

            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
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

                {/* Password */}
                <Input
                  label="Password"
                  type="password"
                  icon={<Lock size={20} />}
                  placeholder="Enter your password"
                  value={formData.password}
                  onChange={handleInputChange('password')}
                  error={errors.password}
                  showPasswordToggle
                />

                {/* Remember Me & Forgot Password */}
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.rememberMe}
                      onChange={handleInputChange('rememberMe')}
                      className="w-4 h-4 text-blue-500 border-grey-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-grey-600 dark:text-grey-300">
                      Remember me
                    </span>
                  </label>
                  <Link 
                    href="/auth/forgot-password" 
                    className="text-sm text-blue-500 hover:text-blue-600 font-medium"
                  >
                    Forgot password?
                  </Link>
                </div>
                
                {/* Submit Button */}
                <Button
                  id="dev-login-btn"
                  type="submit"
                  className="w-full"
                  size="lg"
                  loading={loading}
                >
                  Sign In
                  <ArrowRight size={20} />
                </Button>
              </form>


              {/* Divider */}
              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-grey-200 dark:border-navy-700" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-white dark:bg-navy-800 text-grey-500 dark:text-grey-400">
                    Or continue with
                  </span>
                </div>
              </div>

              {/* Biometric Login */}
              <Button
                type="button"
                variant="secondary"
                className="w-full"
                onClick={handleBiometricLogin}
              >
                <Fingerprint size={20} />
                Biometric Login
              </Button>

              {/* Security Notice */}
              <div className="mt-6 p-4 bg-green-50 dark:bg-green-500/10 rounded-xl border border-green-200 dark:border-green-500/20">
                <div className="flex items-center gap-3 text-green-700 dark:text-green-400">
                  <Shield size={20} />
                  <div>
                    <p className="font-medium text-sm">Secure Login</p>
                    <p className="text-xs text-green-600 dark:text-green-300">
                      Your session is protected with end-to-end encryption
                    </p>
                  </div>
                </div>
              </div>

              {/* Developer/User Toggle Button */}
              <div className="mt-6 flex flex-col items-center">
                {formData.email === devDemo.email && formData.password === devDemo.password ? (
                  <button
                    type="button"
                    className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-gradient-to-br from-purple-500 to-purple-700 text-white font-semibold shadow-lg border-2 border-purple-400 hover:from-purple-600 hover:to-purple-800 transition mb-2"
                    onClick={() => setFormData({ email: '', password: '', rememberMe: false })}
                  >
                    <span className="inline-flex items-center gap-2">
                      <svg width="20" height="20" fill="none" viewBox="0 0 24 24"><path fill="currentColor" d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm0 18a8 8 0 1 1 0-16 8 8 0 0 1 0 16Zm-2-7h4a1 1 0 0 1 0 2h-4a1 1 0 1 1 0-2Zm0-4h4a1 1 0 0 1 0 2h-4a1 1 0 1 1 0-2Z"/></svg>
                      Login as User
                    </span>
                  </button>
                ) : (
                  <button
                    type="button"
                    className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-gradient-to-br from-purple-500 to-purple-700 text-white font-semibold shadow-lg border-2 border-purple-400 hover:from-purple-600 hover:to-purple-800 transition mb-2"
                    onClick={() => setFormData({ email: devDemo.email, password: devDemo.password, rememberMe: false })}
                  >
                    <span className="inline-flex items-center gap-2">
                      <svg width="20" height="20" fill="none" viewBox="0 0 24 24"><path fill="currentColor" d="M4 17v-2a4 4 0 0 1 4-4h8a4 4 0 0 1 4 4v2a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1Zm8-7a3 3 0 1 1 0-6 3 3 0 0 1 0 6Z"/></svg>
                      Login as Developer
                      <span className="ml-2 bg-white text-purple-700 rounded px-2 py-0.5 text-xs font-bold shadow">DEV</span>
                    </span>
                  </button>
                )}
              </div>

              {/* Sign Up Link */}
              <div className="mt-6 text-center">
                <p className="text-grey-600 dark:text-grey-300">
                  Don't have an account?{' '}
                  <Link href="/auth/signup" className="text-blue-500 hover:text-blue-600 font-medium">
                    Create one here
                  </Link>
                </p>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Demo Credentials */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="mt-6"
        >
          <Card className="bg-yellow-50 dark:bg-yellow-500/10 border-yellow-200 dark:border-yellow-500/20">
            <CardContent className="p-4">
              <h4 className="font-medium text-yellow-800 dark:text-yellow-400 mb-2">
                Demo Mode
              </h4>
              <p className="text-sm text-yellow-700 dark:text-yellow-300 mb-3">
                Use these credentials to explore the app:
              </p>
              <div className="space-y-1 text-sm font-mono">
                <div className="text-yellow-800 dark:text-yellow-400">
                  Email: demo@syncash.com
                </div>
                <div className="text-yellow-800 dark:text-yellow-400">
                  Password: Demo123!
                </div>
                <div className="text-yellow-800 dark:text-yellow-400 mt-2">
                  <span className="font-semibold">Developer Demo:</span>
                </div>
                <div className="text-yellow-800 dark:text-yellow-400">
                  Email: dev@syncash.com
                </div>
                <div className="text-yellow-800 dark:text-yellow-400">
                  Password: Dev123!
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}
