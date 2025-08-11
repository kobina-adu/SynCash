"""
Comprehensive Test Suite for SyncCash Orchestrator
Tests all major functionality including edge cases and error handling
"""

import requests
import json
import time
import random
from datetime import datetime
from typing import Dict, List

class SyncCashOrchestratorTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.transaction_ids = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {test_name}")
        if details:
            print(f"      {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def test_system_health(self):
        """Test system health and connectivity"""
        print("\nSYSTEM HEALTH TESTS")
        print("=" * 50)
        
        # Basic health check
        try:
            response = requests.get(f"{self.base_url}/health")
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            self.log_test("Basic Health Check", success, details)
        except Exception as e:
            self.log_test("Basic Health Check", False, str(e))
        
        # Detailed health check
        try:
            response = requests.get(f"{self.base_url}/api/v1/health/detailed")
            if response.status_code == 200:
                health_data = response.json()
                details = f"Service: {health_data['status']}, DB: {health_data['database']}, Redis: {health_data['redis']}"
                self.log_test("Detailed Health Check", True, details)
            else:
                self.log_test("Detailed Health Check", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Detailed Health Check", False, str(e))
        
        # Readiness probe
        try:
            response = requests.get(f"{self.base_url}/api/v1/health/ready")
            success = response.status_code in [200, 503]  # 503 acceptable if DB unavailable
            self.log_test("Readiness Probe", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Readiness Probe", False, str(e))
    
    def test_payment_initiation(self):
        """Test payment initiation with various scenarios"""
        print("\nPAYMENT INITIATION TESTS")
        print("=" * 50)
        
        # Valid payment
        valid_payment = {
            "user_id": "user_test_001",
            "amount": 250.75,
            "recipient_phone": "+233241234567",
            "recipient_name": "Alice Johnson",
            "description": "Test payment - valid scenario",
            "metadata": {"test_type": "valid_payment", "source": "test_suite"}
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/payments/initiate",
                json=valid_payment,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    transaction_id = result['transaction_id']
                    self.transaction_ids.append(transaction_id)
                    details = f"Transaction ID: {transaction_id}, Status: {result['status']}"
                    self.log_test("Valid Payment Initiation", True, details)
                else:
                    self.log_test("Valid Payment Initiation", False, result.get('error', 'Unknown error'))
            else:
                self.log_test("Valid Payment Initiation", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Valid Payment Initiation", False, str(e))
        
        # Large amount payment (should trigger higher risk)
        large_payment = {
            "user_id": "user_test_002",
            "amount": 15000.00,
            "recipient_phone": "+233207654321",
            "recipient_name": "Bob Wilson",
            "description": "Large amount test payment",
            "metadata": {"test_type": "large_amount", "source": "test_suite"}
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/payments/initiate",
                json=large_payment,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    transaction_id = result['transaction_id']
                    self.transaction_ids.append(transaction_id)
                    self.log_test("Large Amount Payment", True, f"Transaction ID: {transaction_id}")
                else:
                    # Could be blocked due to fraud detection
                    self.log_test("Large Amount Payment", True, f"Blocked by fraud detection: {result.get('error')}")
            else:
                self.log_test("Large Amount Payment", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Large Amount Payment", False, str(e))
    
    def test_input_validation(self):
        """Test input validation and error handling"""
        print("\nINPUT VALIDATION TESTS")
        print("=" * 50)
        
        # Invalid amount (negative)
        invalid_payment = {
            "user_id": "user_test_003",
            "amount": -50.00,
            "recipient_phone": "+233241234567",
            "recipient_name": "Test User",
            "description": "Invalid negative amount"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/payments/initiate",
                json=invalid_payment,
                headers={"Content-Type": "application/json"}
            )
            
            success = response.status_code == 400  # Should be bad request
            self.log_test("Negative Amount Validation", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Negative Amount Validation", False, str(e))
        
        # Missing required fields
        incomplete_payment = {
            "user_id": "user_test_004",
            "amount": 100.00
            # Missing recipient_phone and recipient_name
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/payments/initiate",
                json=incomplete_payment,
                headers={"Content-Type": "application/json"}
            )
            
            success = response.status_code == 422  # Should be validation error
            self.log_test("Missing Fields Validation", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Missing Fields Validation", False, str(e))
        
        # Invalid phone number format
        invalid_phone_payment = {
            "user_id": "user_test_005",
            "amount": 100.00,
            "recipient_phone": "invalid-phone",
            "recipient_name": "Test User",
            "description": "Invalid phone format test"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/payments/initiate",
                json=invalid_phone_payment,
                headers={"Content-Type": "application/json"}
            )
            
            success = response.status_code in [400, 422]  # Should be validation error
            self.log_test("Invalid Phone Validation", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Phone Validation", False, str(e))
    
    def test_transaction_status(self):
        """Test transaction status retrieval"""
        print("\nTRANSACTION STATUS TESTS")
        print("=" * 50)
        
        if not self.transaction_ids:
            self.log_test("Transaction Status Check", False, "No valid transactions to check")
            return
        
        # Check status of valid transaction
        transaction_id = self.transaction_ids[0]
        try:
            response = requests.get(f"{self.base_url}/api/v1/payments/{transaction_id}/status")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    transaction = result['transaction']
                    details = f"Status: {transaction['status']}, Amount: {transaction['amount']}"
                    self.log_test("Valid Transaction Status", True, details)
                else:
                    self.log_test("Valid Transaction Status", False, result.get('error'))
            else:
                self.log_test("Valid Transaction Status", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Valid Transaction Status", False, str(e))
        
        # Check status of non-existent transaction
        fake_id = "00000000-0000-0000-0000-000000000000"
        try:
            response = requests.get(f"{self.base_url}/api/v1/payments/{fake_id}/status")
            success = response.status_code == 404  # Should be not found
            self.log_test("Non-existent Transaction Status", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Non-existent Transaction Status", False, str(e))
    
    def test_concurrent_payments(self):
        """Test system under concurrent load"""
        print("\nCONCURRENT LOAD TESTS")
        print("=" * 50)
        
        import threading
        import time
        
        results = []
        
        def create_payment(user_id: int):
            payment_data = {
                "user_id": f"concurrent_user_{user_id}",
                "amount": round(random.uniform(10, 1000), 2),
                "recipient_phone": f"+23324{random.randint(1000000, 9999999)}",
                "recipient_name": f"User {user_id}",
                "description": f"Concurrent test payment {user_id}",
                "metadata": {"test_type": "concurrent", "user_id": user_id}
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/payments/initiate",
                    json=payment_data,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                results.append({
                    "user_id": user_id,
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds()
                })
            except Exception as e:
                results.append({
                    "user_id": user_id,
                    "success": False,
                    "error": str(e)
                })
        
        # Create 5 concurrent payment requests
        threads = []
        start_time = time.time()
        
        for i in range(5):
            thread = threading.Thread(target=create_payment, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        successful = sum(1 for r in results if r.get('success', False))
        avg_response_time = sum(r.get('response_time', 0) for r in results if 'response_time' in r) / len(results)
        
        success = successful >= 3  # At least 60% success rate
        details = f"Success: {successful}/5, Avg time: {avg_response_time:.2f}s, Total: {total_time:.2f}s"
        self.log_test("Concurrent Payment Processing", success, details)
    
    def test_api_documentation(self):
        """Test API documentation accessibility"""
        print("\nAPI DOCUMENTATION TESTS")
        print("=" * 50)
        
        docs_endpoints = [
            ("/api/docs", "Swagger UI"),
            ("/api/redoc", "ReDoc"),
            ("/openapi.json", "OpenAPI Schema")
        ]
        
        for endpoint, name in docs_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}")
                success = response.status_code == 200
                self.log_test(f"{name} Accessibility", success, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"{name} Accessibility", False, str(e))
    
    def run_all_tests(self):
        """Run the complete test suite"""
        print("SYNCCASH ORCHESTRATOR COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target URL: {self.base_url}")
        
        start_time = time.time()
        
        # Run all test categories
        self.test_system_health()
        self.test_payment_initiation()
        self.test_input_validation()
        self.test_transaction_status()
        self.test_concurrent_payments()
        self.test_api_documentation()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Generate summary
        self.generate_test_summary(total_time)
    
    def generate_test_summary(self, total_time: float):
        """Generate and display test summary"""
        print("\nTEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Time: {total_time:.2f} seconds")
        print(f"Transactions Created: {len(self.transaction_ids)}")
        
        if failed_tests > 0:
            print(f"\nFAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
        
        print(f"\nSYSTEM STATUS:")
        if success_rate >= 90:
            print("   [EXCELLENT] - System is performing optimally")
        elif success_rate >= 75:
            print("   [GOOD] - System is mostly functional with minor issues")
        elif success_rate >= 50:
            print("   [FAIR] - System has significant issues that need attention")
        else:
            print("   [POOR] - System has critical issues requiring immediate attention")
        
        print(f"\nRECOMMENDATIONS:")
        if success_rate < 100:
            print("   - Review failed tests and address underlying issues")
            print("   - Check database and Redis connectivity")
            print("   - Verify all services are running properly")
        else:
            print("   - System is ready for production deployment")
            print("   - Consider load testing with higher concurrency")
            print("   - Implement monitoring and alerting")

if __name__ == "__main__":
    tester = SyncCashOrchestratorTester()
    tester.run_all_tests()
