'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { 
  User,
  Mail,
  Phone,
  Lock,
  Bell,
  Shield,
  Moon,
  Sun,
  Globe,
  CreditCard,
  ArrowLeft,
  Camera,
  Edit3,
  Save,
  AlertTriangle,
  CheckCircle,
  Smartphone,
  Eye,
  EyeOff,
  LogOut,
  Trash2
} from 'lucide-react'
import { getInitials } from '@/lib/utils'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useTheme } from 'next-themes'
import toast from 'react-hot-toast'

// Mock user data
const userData = {
  firstName: 'Kwame',
  lastName: 'Asante',
  email: 'kwame.asante@example.com',
  phone: '0244123456',
  avatar: null,
  joinDate: '2023-06-15',
  isVerified: true,
  twoFactorEnabled: false
}

const linkedAccounts = [
  { id: 'mtn', name: 'MTN MoMo', phone: '0244123456', status: 'active' },
  { id: 'telecel', name: 'Telecel Cash', phone: '0201987654', status: 'active' },
  { id: 'gcb', name: 'GCB Bank', account: '****5678', status: 'active' }
]

const notificationSettings = [
  { id: 'transactions', label: 'Transaction Notifications', description: 'Get notified of all transactions', enabled: true },
  { id: 'bills', label: 'Bill Reminders', description: 'Reminders for upcoming bill payments', enabled: true },
  { id: 'security', label: 'Security Alerts', description: 'Important security notifications', enabled: true },
  { id: 'marketing', label: 'Marketing Updates', description: 'Product updates and offers', enabled: false }
]

export default function SettingsPage() {
  const router = useRouter()
  const { theme, setTheme } = useTheme()
  const [activeTab, setActiveTab] = useState('profile')
  const [loading, setLoading] = useState(false)
  const [editingProfile, setEditingProfile] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  
  const [profileData, setProfileData] = useState({
    firstName: userData.firstName,
    lastName: userData.lastName,
    email: userData.email,
    phone: userData.phone
  })

  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  })

  const [notifications, setNotifications] = useState(notificationSettings)

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'accounts', label: 'Linked Accounts', icon: CreditCard },
    { id: 'preferences', label: 'Preferences', icon: Globe }
  ]

  const handleProfileSave = async () => {
    setLoading(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 1500))
      setEditingProfile(false)
      toast.success('Profile updated successfully!')
    } catch (error) {
      toast.error('Failed to update profile')
    } finally {
      setLoading(false)
    }
  }

  const handlePasswordChange = async () => {
    if (!passwordData.currentPassword || !passwordData.newPassword) {
      toast.error('Please fill in all password fields')
      return
    }
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      toast.error('New passwords do not match')
      return
    }
    if (passwordData.newPassword.length < 8) {
      toast.error('Password must be at least 8 characters')
      return
    }

    setLoading(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 1500))
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' })
      toast.success('Password changed successfully!')
    } catch (error) {
      toast.error('Failed to change password')
    } finally {
      setLoading(false)
    }
  }

  const handleNotificationToggle = (id: string) => {
    setNotifications(prev => 
      prev.map(notif => 
        notif.id === id ? { ...notif, enabled: !notif.enabled } : notif
      )
    )
    toast.success('Notification settings updated')
  }

  const handleLogout = () => {
    toast.success('Logged out successfully')
    router.push('/auth/login')
  }

  const handleDeleteAccount = async () => {
    setLoading(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 2000))
      toast.success('Account deleted successfully')
      router.push('/')
    } catch (error) {
      toast.error('Failed to delete account')
    } finally {
      setLoading(false)
      setShowDeleteConfirm(false)
    }
  }

  const renderProfileTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Personal Information</CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setEditingProfile(!editingProfile)}
            >
              <Edit3 size={16} />
              {editingProfile ? 'Cancel' : 'Edit'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Avatar */}
            <div className="flex items-center gap-6">
              <div className="relative">
                <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white font-bold text-2xl">
                  {getInitials(`${profileData.firstName} ${profileData.lastName}`)}
                </div>
                {editingProfile && (
                  <button className="absolute -bottom-2 -right-2 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white hover:bg-blue-600 transition-colors">
                    <Camera size={16} />
                  </button>
                )}
              </div>
              <div>
                <h3 className="text-xl font-semibold text-navy-900 dark:text-white">
                  {profileData.firstName} {profileData.lastName}
                </h3>
                <p className="text-grey-600 dark:text-grey-300">
                  Member since {new Date(userData.joinDate).toLocaleDateString()}
                </p>
                {userData.isVerified && (
                  <div className="flex items-center gap-2 mt-2">
                    <CheckCircle className="text-green-500" size={16} />
                    <span className="text-sm text-green-600 dark:text-green-400">Verified Account</span>
                  </div>
                )}
              </div>
            </div>

            {/* Form Fields */}
            <div className="grid md:grid-cols-2 gap-4">
              <Input
                label="First Name"
                value={profileData.firstName}
                onChange={(e) => setProfileData(prev => ({ ...prev, firstName: e.target.value }))}
                disabled={!editingProfile}
              />
              <Input
                label="Last Name"
                value={profileData.lastName}
                onChange={(e) => setProfileData(prev => ({ ...prev, lastName: e.target.value }))}
                disabled={!editingProfile}
              />
            </div>

            <Input
              label="Email Address"
              type="email"
              icon={<Mail size={20} />}
              value={profileData.email}
              onChange={(e) => setProfileData(prev => ({ ...prev, email: e.target.value }))}
              disabled={!editingProfile}
            />

            <Input
              label="Phone Number"
              icon={<Phone size={20} />}
              value={profileData.phone}
              onChange={(e) => setProfileData(prev => ({ ...prev, phone: e.target.value }))}
              disabled={!editingProfile}
            />

            {editingProfile && (
              <div className="flex gap-4">
                <Button onClick={handleProfileSave} loading={loading} className="flex-1">
                  <Save size={16} />
                  Save Changes
                </Button>
                <Button variant="secondary" onClick={() => setEditingProfile(false)} className="flex-1">
                  Cancel
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderSecurityTab = () => (
    <div className="space-y-6">
      {/* Change Password */}
      <Card>
        <CardHeader>
          <CardTitle>Change Password</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Input
              label="Current Password"
              type="password"
              icon={<Lock size={20} />}
              value={passwordData.currentPassword}
              onChange={(e) => setPasswordData(prev => ({ ...prev, currentPassword: e.target.value }))}
              showPasswordToggle
            />
            <Input
              label="New Password"
              type="password"
              icon={<Lock size={20} />}
              value={passwordData.newPassword}
              onChange={(e) => setPasswordData(prev => ({ ...prev, newPassword: e.target.value }))}
              showPasswordToggle
            />
            <Input
              label="Confirm New Password"
              type="password"
              icon={<Lock size={20} />}
              value={passwordData.confirmPassword}
              onChange={(e) => setPasswordData(prev => ({ ...prev, confirmPassword: e.target.value }))}
              showPasswordToggle
            />
            <Button onClick={handlePasswordChange} loading={loading}>
              Update Password
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Two-Factor Authentication */}
      <Card>
        <CardHeader>
          <CardTitle>Two-Factor Authentication</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-navy-900 dark:text-white">SMS Authentication</p>
              <p className="text-sm text-grey-600 dark:text-grey-300">
                Add an extra layer of security to your account
              </p>
            </div>
            <Button variant={userData.twoFactorEnabled ? "danger" : "primary"}>
              {userData.twoFactorEnabled ? 'Disable' : 'Enable'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Login Sessions */}
      <Card>
        <CardHeader>
          <CardTitle>Active Sessions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-grey-50 dark:bg-navy-700 rounded-xl">
              <div className="flex items-center gap-3">
                <Smartphone className="text-blue-500" size={20} />
                <div>
                  <p className="font-medium text-navy-900 dark:text-white">Current Device</p>
                  <p className="text-sm text-grey-600 dark:text-grey-300">Windows • Chrome • Active now</p>
                </div>
              </div>
              <span className="text-sm text-green-600 dark:text-green-400 font-medium">Current</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderNotificationsTab = () => (
    <Card>
      <CardHeader>
        <CardTitle>Notification Preferences</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {notifications.map((notification) => (
            <div key={notification.id} className="flex items-center justify-between">
              <div>
                <p className="font-medium text-navy-900 dark:text-white">{notification.label}</p>
                <p className="text-sm text-grey-600 dark:text-grey-300">{notification.description}</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={notification.enabled}
                  onChange={() => handleNotificationToggle(notification.id)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-grey-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-grey-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-grey-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-grey-600 peer-checked:bg-blue-600"></div>
              </label>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )

  const renderAccountsTab = () => (
    <Card>
      <CardHeader>
        <CardTitle>Linked Accounts</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {linkedAccounts.map((account) => (
            <div key={account.id} className="flex items-center justify-between p-4 border border-grey-200 dark:border-navy-700 rounded-xl">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 dark:bg-blue-500/20 rounded-xl flex items-center justify-center">
                  <CreditCard className="text-blue-500" size={20} />
                </div>
                <div>
                  <p className="font-medium text-navy-900 dark:text-white">{account.name}</p>
                  <p className="text-sm text-grey-600 dark:text-grey-300">
                    {account.phone || account.account}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="status-success">Active</span>
                <Button variant="ghost" size="sm">
                  Manage
                </Button>
              </div>
            </div>
          ))}
          <Link href="/wallets/add">
            <Button variant="secondary" className="w-full">
              Link New Account
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  )

  const renderPreferencesTab = () => (
    <div className="space-y-6">
      {/* Theme */}
      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-navy-900 dark:text-white">Theme</p>
                <p className="text-sm text-grey-600 dark:text-grey-300">Choose your preferred theme</p>
              </div>
              <div className="flex gap-2">
                <Button
                  variant={theme === 'light' ? 'primary' : 'ghost'}
                  size="sm"
                  onClick={() => setTheme('light')}
                >
                  <Sun size={16} />
                  Light
                </Button>
                <Button
                  variant={theme === 'dark' ? 'primary' : 'ghost'}
                  size="sm"
                  onClick={() => setTheme('dark')}
                >
                  <Moon size={16} />
                  Dark
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Language */}
      <Card>
        <CardHeader>
          <CardTitle>Language & Region</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-navy-900 dark:text-white">Language</p>
                <p className="text-sm text-grey-600 dark:text-grey-300">Choose your preferred language</p>
              </div>
              <select className="input-field w-auto">
                <option value="en">English</option>
                <option value="tw">Twi</option>
                <option value="ga">Ga</option>
                <option value="ee">Ewe</option>
              </select>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-navy-900 dark:text-white">Currency</p>
                <p className="text-sm text-grey-600 dark:text-grey-300">Display currency</p>
              </div>
              <select className="input-field w-auto">
                <option value="GHS">Ghana Cedi (₵)</option>
                <option value="USD">US Dollar ($)</option>
                <option value="EUR">Euro (€)</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Danger Zone */}
      <Card className="border-red-200 dark:border-red-500/20">
        <CardHeader>
          <CardTitle className="text-red-600 dark:text-red-400 flex items-center gap-2">
            <AlertTriangle size={20} />
            Danger Zone
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-navy-900 dark:text-white">Log Out</p>
                <p className="text-sm text-grey-600 dark:text-grey-300">Sign out of your account</p>
              </div>
              <Button variant="secondary" onClick={handleLogout}>
                <LogOut size={16} />
                Log Out
              </Button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-red-600 dark:text-red-400">Delete Account</p>
                <p className="text-sm text-grey-600 dark:text-grey-300">Permanently delete your account and all data</p>
              </div>
              <Button variant="danger" onClick={() => setShowDeleteConfirm(true)}>
                <Trash2 size={16} />
                Delete Account
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
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
                <h1 className="text-2xl font-bold text-navy-900 dark:text-white">Settings</h1>
                <p className="text-grey-600 dark:text-grey-300">Manage your account and preferences</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="section-padding py-8">
        <div className="container-width max-w-6xl">
          <div className="grid lg:grid-cols-4 gap-8">
            {/* Sidebar */}
            <div className="lg:col-span-1">
              <Card>
                <CardContent className="p-4">
                  <nav className="space-y-2">
                    {tabs.map((tab) => {
                      const IconComponent = tab.icon
                      return (
                        <button
                          key={tab.id}
                          onClick={() => setActiveTab(tab.id)}
                          className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all ${
                            activeTab === tab.id
                              ? 'bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400'
                              : 'text-grey-600 dark:text-grey-400 hover:bg-grey-50 dark:hover:bg-navy-700'
                          }`}
                        >
                          <IconComponent size={20} />
                          {tab.label}
                        </button>
                      )
                    })}
                  </nav>
                </CardContent>
              </Card>
            </div>

            {/* Content */}
            <div className="lg:col-span-3">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                {activeTab === 'profile' && renderProfileTab()}
                {activeTab === 'security' && renderSecurityTab()}
                {activeTab === 'notifications' && renderNotificationsTab()}
                {activeTab === 'accounts' && renderAccountsTab()}
                {activeTab === 'preferences' && renderPreferencesTab()}
              </motion.div>
            </div>
          </div>
        </div>
      </main>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-md w-full">
            <CardHeader>
              <CardTitle className="text-red-600 dark:text-red-400 flex items-center gap-2">
                <AlertTriangle size={20} />
                Delete Account
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <p className="text-grey-600 dark:text-grey-300">
                  Are you sure you want to delete your account? This action cannot be undone and all your data will be permanently removed.
                </p>
                <div className="flex gap-4">
                  <Button
                    variant="danger"
                    onClick={handleDeleteAccount}
                    loading={loading}
                    className="flex-1"
                  >
                    Delete Account
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => setShowDeleteConfirm(false)}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
