import FraudDetectionTest from '@/components/FraudDetectionTest';

/**
 * Fraud Detection Test Page
 * 
 * Visit /fraud-test to test the ML fraud detection popup system
 * This page demonstrates the different popup types that users will see
 * based on ML model risk assessment results.
 */
export default function FraudTestPage() {
  return (
    <div className="min-h-screen bg-grey-50 dark:bg-navy-900">
      {/* Header */}
      <header className="bg-white dark:bg-navy-800 border-b border-grey-200 dark:border-navy-700">
        <div className="section-padding py-4">
          <div className="container-width">
            <div>
              <h1 className="text-2xl font-bold text-navy-900 dark:text-white">
                🧪 Fraud Detection Test Lab
              </h1>
              <p className="text-grey-600 dark:text-grey-300">
                Test the ML fraud detection popup system - Similar to reCAPTCHA for fraud prevention
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="section-padding py-8">
        <div className="container-width">
          <FraudDetectionTest />
        </div>
      </main>
    </div>
  );
}
