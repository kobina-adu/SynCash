/**
 * API Service Layer for SyncCash
 * Connects Next.js frontend to FastAPI backend with fraud detection
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface PaymentRequest {
  user_id: string;
  amount: number;
  recipient_phone: string;
  recipient_name: string;
  description?: string;
  metadata?: Record<string, any>;
}

interface FraudDetectionResult {
  success: boolean;
  transaction_id: string;
  fraud_detected?: boolean;
  blocked?: boolean;
  risk_level?: string;
  risk_score?: number;
  reasons?: string[];
  ui_response?: {
    type: string;
    title: string;
    message: string;
    warning_text?: string;
    color: string;
    show_popup: boolean;
    require_confirmation: boolean;
  };
  fraud_check?: {
    risk_level: string;
    risk_score: number;
    confidence: number;
    ml_model_used: boolean;
  };
  status?: string;
  provider?: string;
  estimated_completion?: string;
  error?: string;
}

class ApiService {
  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
      // Add authentication headers if needed
      // 'Authorization': `Bearer ${getAuthToken()}`,
    };

    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Initiate payment with ML fraud detection
   * This calls your backend fraud detection service
   */
  async initiatePayment(paymentData: PaymentRequest): Promise<FraudDetectionResult> {
    console.log('🔄 Calling backend fraud detection API...', paymentData);
    
    try {
      const result = await this.makeRequest<FraudDetectionResult>(
        '/api/v1/payments/initiate',
        {
          method: 'POST',
          body: JSON.stringify(paymentData),
        }
      );

      console.log('🤖 Backend fraud detection response:', result);
      return result;
    } catch (error) {
      console.error('❌ Payment API error:', error);
      
      // Return system error response for UI
      return {
        success: false,
        transaction_id: '',
        fraud_detected: true,
        blocked: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        ui_response: {
          type: 'system_error',
          title: '⚠️ SECURITY CHECK REQUIRED',
          message: 'Unable to verify transaction security. Please try again or contact support.',
          warning_text: 'CAUTION: Security verification failed',
          color: 'orange',
          show_popup: true,
          require_confirmation: true
        }
      };
    }
  }

  /**
   * Request OTP for high-risk transactions
   */
  async requestOTP(transactionId: string): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
      return await this.makeRequest(`/api/v1/payments/${transactionId}/request-otp`, {
        method: 'POST',
      });
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Failed to request OTP');
    }
  }

  /**
   * Verify OTP and complete transaction
   */
  async verifyOTP(transactionId: string, otpCode: string): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
      return await this.makeRequest(`/api/v1/payments/${transactionId}/verify-otp`, {
        method: 'POST',
        body: JSON.stringify({ otp_code: otpCode }),
      });
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'OTP verification failed');
    }
  }

  /**
   * Cancel transaction
   */
  async cancelTransaction(transactionId: string): Promise<{ success: boolean; message?: string }> {
    try {
      return await this.makeRequest(`/api/v1/payments/${transactionId}/cancel`, {
        method: 'POST',
      });
    } catch (error) {
      console.error('Cancel transaction error:', error);
      return { success: false, message: 'Failed to cancel transaction' };
    }
  }

  /**
   * Get transaction status
   */
  async getTransactionStatus(transactionId: string): Promise<any> {
    return this.makeRequest(`/api/v1/payments/${transactionId}/status`);
  }
}

// Export singleton instance
export const apiService = new ApiService();
export type { PaymentRequest, FraudDetectionResult };
