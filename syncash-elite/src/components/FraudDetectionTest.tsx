'use client'

import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import FraudDetectionModal from './FraudDetectionModal';
import { Shield, AlertTriangle, XCircle, TestTube } from 'lucide-react';
import toast from 'react-hot-toast';

/**
 * FraudDetectionTest - Test component to demonstrate fraud detection popups
 * 
 * This component simulates different ML model results to test the popup system:
 * - Safe transaction (green popup)
 * - High-risk transaction (red warning + OTP)
 * - Critical transaction (blocked)
 * - System error
 */
export default function FraudDetectionTest() {
  const [showModal, setShowModal] = useState(false);
  const [fraudResult, setFraudResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Simulate different ML model results
  const simulateFraudDetection = (scenario: string) => {
    setLoading(true);
    
    // Simulate API delay
    setTimeout(() => {
      let result;
      
      switch (scenario) {
        case 'safe':
          result = {
            risk_level: 'LOW',
            risk_score: 0.15,
            confidence: 0.95,
            reasons: [],
            ui_response: {
              type: 'safe_transaction',
              title: '✅ Security Check Passed',
              message: 'Your transaction has been verified as safe by our ML security system.',
              color: 'green',
              show_popup: true,
              require_confirmation: false
            },
            transaction_id: 'txn_' + Date.now(),
            is_fraud: false,
            blocked: false
          };
          break;
          
        case 'high_risk':
          result = {
            risk_level: 'HIGH',
            risk_score: 0.65,
            confidence: 0.88,
            reasons: [
              'Unusual transaction amount detected',
              'Transaction pattern differs from user history',
              'High-risk recipient identified'
            ],
            ui_response: {
              type: 'high_risk_transaction',
              title: '⚠️ Security Warning',
              message: 'Our ML model has detected potential security risks with this transaction.',
              warning_text: 'CAUTION MODE ACTIVATED',
              color: 'red',
              show_popup: true,
              require_confirmation: true
            },
            transaction_id: 'txn_' + Date.now(),
            is_fraud: true,
            blocked: false
          };
          break;
          
        case 'critical':
          result = {
            risk_level: 'CRITICAL',
            risk_score: 0.92,
            confidence: 0.96,
            reasons: [
              'Multiple fraud indicators detected',
              'Suspicious recipient account',
              'Transaction amount exceeds safety threshold',
              'Unusual timing pattern detected'
            ],
            ui_response: {
              type: 'transaction_blocked',
              title: '🚫 TRANSACTION BLOCKED',
              message: 'This transaction has been blocked due to critical security concerns.',
              warning_text: 'CRITICAL RISK DETECTED',
              color: 'red',
              show_popup: true,
              require_confirmation: true
            },
            transaction_id: 'txn_' + Date.now(),
            is_fraud: true,
            blocked: true
          };
          break;
          
        case 'system_error':
          result = {
            risk_level: 'UNKNOWN',
            risk_score: 1.0,
            confidence: 0,
            reasons: ['System error during fraud detection'],
            ui_response: {
              type: 'system_error',
              title: '⚠️ SECURITY CHECK REQUIRED',
              message: 'Unable to verify transaction security. Please try again or contact support.',
              warning_text: 'CAUTION: Security verification failed',
              color: 'orange',
              show_popup: true,
              require_confirmation: true
            },
            transaction_id: 'txn_' + Date.now(),
            is_fraud: true,
            blocked: false
          };
          break;
          
        default:
          result = null;
      }
      
      setFraudResult(result);
      setShowModal(true);
      setLoading(false);
    }, 1500); // Simulate API delay
  };

  // Handle popup actions
  const handleProceed = () => {
    toast.success('✅ Transaction proceeding - ML model approved!');
    setShowModal(false);
    setFraudResult(null);
  };

  const handleRequestOTP = async () => {
    // Simulate OTP request
    await new Promise(resolve => setTimeout(resolve, 1000));
    toast.success('📱 OTP sent to your phone');
  };

  const handleVerifyOTP = async (otpCode: string) => {
    // Simulate OTP verification
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    if (otpCode === '123456') {
      toast.success('✅ OTP verified - Transaction approved!');
      setShowModal(false);
      setFraudResult(null);
    } else {
      throw new Error('Invalid OTP code. Try 123456 for demo.');
    }
  };

  const handleCancel = () => {
    toast.error('❌ Transaction cancelled');
    setShowModal(false);
    setFraudResult(null);
  };

  const handleRetry = () => {
    toast.loading('🔄 Retrying transaction...');
    setShowModal(false);
    setFraudResult(null);
    // Could trigger another fraud check here
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TestTube className="text-blue-500" size={24} />
            Fraud Detection Popup Test
          </CardTitle>
          <p className="text-gray-600 dark:text-gray-300">
            Test the ML fraud detection popup system with different scenarios. 
            This simulates what users will see when the ML model analyzes their transactions.
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            
            {/* Safe Transaction Test */}
            <Card className="border-green-200 dark:border-green-800">
              <CardContent className="p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 bg-green-100 dark:bg-green-500/20 rounded-full flex items-center justify-center">
                    <Shield className="text-green-500" size={20} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-green-700 dark:text-green-400">
                      Safe Transaction
                    </h3>
                    <p className="text-sm text-green-600 dark:text-green-300">
                      Risk Score: 15% (Low Risk)
                    </p>
                  </div>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
                  Shows green popup with "PROCEED" button when ML model determines transaction is safe.
                </p>
                <Button
                  onClick={() => simulateFraudDetection('safe')}
                  disabled={loading}
                  className="w-full bg-green-500 hover:bg-green-600 text-white"
                >
                  Test Safe Transaction
                </Button>
              </CardContent>
            </Card>

            {/* High Risk Transaction Test */}
            <Card className="border-yellow-200 dark:border-yellow-800">
              <CardContent className="p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 bg-yellow-100 dark:bg-yellow-500/20 rounded-full flex items-center justify-center">
                    <AlertTriangle className="text-yellow-500" size={20} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-yellow-700 dark:text-yellow-400">
                      High-Risk Transaction
                    </h3>
                    <p className="text-sm text-yellow-600 dark:text-yellow-300">
                      Risk Score: 65% (High Risk)
                    </p>
                  </div>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
                  Shows red warning popup with "CAUTION MODE" and OTP verification requirement.
                </p>
                <Button
                  onClick={() => simulateFraudDetection('high_risk')}
                  disabled={loading}
                  className="w-full bg-yellow-500 hover:bg-yellow-600 text-white"
                >
                  Test High-Risk Transaction
                </Button>
              </CardContent>
            </Card>

            {/* Critical Transaction Test */}
            <Card className="border-red-200 dark:border-red-800">
              <CardContent className="p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 bg-red-100 dark:bg-red-500/20 rounded-full flex items-center justify-center">
                    <XCircle className="text-red-500" size={20} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-red-700 dark:text-red-400">
                      Critical Risk (Blocked)
                    </h3>
                    <p className="text-sm text-red-600 dark:text-red-300">
                      Risk Score: 92% (Critical Risk)
                    </p>
                  </div>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
                  Shows blocked transaction popup when ML model detects critical fraud risk.
                </p>
                <Button
                  onClick={() => simulateFraudDetection('critical')}
                  disabled={loading}
                  className="w-full bg-red-500 hover:bg-red-600 text-white"
                >
                  Test Critical Risk
                </Button>
              </CardContent>
            </Card>

            {/* System Error Test */}
            <Card className="border-orange-200 dark:border-orange-800">
              <CardContent className="p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 bg-orange-100 dark:bg-orange-500/20 rounded-full flex items-center justify-center">
                    <AlertTriangle className="text-orange-500" size={20} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-orange-700 dark:text-orange-400">
                      System Error
                    </h3>
                    <p className="text-sm text-orange-600 dark:text-orange-300">
                      ML Model Unavailable
                    </p>
                  </div>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
                  Shows error popup when ML model or fraud detection system fails.
                </p>
                <Button
                  onClick={() => simulateFraudDetection('system_error')}
                  disabled={loading}
                  className="w-full bg-orange-500 hover:bg-orange-600 text-white"
                >
                  Test System Error
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Instructions */}
          <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-500/10 rounded-lg border border-blue-200 dark:border-blue-500/20">
            <h4 className="font-semibold text-blue-700 dark:text-blue-400 mb-2">
              🧪 Test Instructions:
            </h4>
            <ul className="text-sm text-blue-600 dark:text-blue-300 space-y-1">
              <li>• Click any test button to simulate ML model fraud detection</li>
              <li>• For High-Risk test: Use OTP code <code className="bg-blue-100 dark:bg-blue-900 px-1 rounded">123456</code> to verify</li>
              <li>• Each popup shows different UI based on ML model risk assessment</li>
              <li>• This simulates the exact behavior users will see in production</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Fraud Detection Modal */}
      <FraudDetectionModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        fraudResult={fraudResult}
        onProceed={handleProceed}
        // onRequestOTP={handleRequestOTP}
        // onVerifyOTP={handleVerifyOTP}
        onCancel={handleCancel}
        // onRetry={handleRetry}
        // loading={loading}
      />
    </div>
  );
}
