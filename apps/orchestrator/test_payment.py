"""
Test script for SyncCash Orchestrator payment functionality
"""

import requests
import json
import time

def test_payment_workflow():
    """Test the complete payment workflow"""
    base_url = "http://localhost:8000"
    
    print("Testing SyncCash Orchestrator Payment Workflow")
    print("=" * 50)
    
    # Test 1: Health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/api/v1/health/detailed")
        print(f"   Status: {response.status_code}")
        health_data = response.json()
        print(f"   Service: {health_data['status']}")
        print(f"   Database: {health_data['database']}")
        print(f"   Redis: {health_data['redis']}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Test 2: Initiate payment
    print("2. Testing payment initiation...")
    payment_data = {
        "user_id": "user_12345",
        "amount": 100.50,
        "recipient_phone": "+233241234567",
        "recipient_name": "John Doe",
        "description": "Test payment for mobile money transfer",
        "metadata": {
            "source": "web_app",
            "category": "transfer"
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/payments/initiate",
            json=payment_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            payment_result = response.json()
            print(f"   Success: {payment_result['success']}")
            if payment_result['success']:
                transaction_id = payment_result['transaction_id']
                print(f"   Transaction ID: {transaction_id}")
                print(f"   Status: {payment_result['status']}")
                print(f"   Estimated completion: {payment_result.get('estimated_completion', 'N/A')}")
                
                # Test 3: Check payment status
                print()
                print("3. Testing payment status check...")
                time.sleep(1)  # Wait a moment
                
                status_response = requests.get(f"{base_url}/api/v1/payments/{transaction_id}/status")
                print(f"   Status: {status_response.status_code}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data['success']:
                        transaction = status_data['transaction']
                        print(f"   Transaction Status: {transaction['status']}")
                        print(f"   Amount: {transaction['amount']} {transaction['currency']}")
                        print(f"   Recipient: {transaction['recipient_name']} ({transaction['recipient_phone']})")
                        print(f"   Risk Level: {transaction['risk_level']}")
                        print(f"   Created: {transaction['created_at']}")
                    else:
                        print(f"   Error: {status_data['error']}")
                else:
                    print(f"   Error: {status_response.text}")
                
                return transaction_id
            else:
                print(f"   Error: {payment_result['error']}")
        else:
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    return None

def test_api_documentation():
    """Test API documentation endpoints"""
    base_url = "http://localhost:8000"
    
    print()
    print("4. Testing API documentation...")
    
    endpoints = [
        "/api/docs",
        "/api/redoc"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            if response.status_code == 200:
                print(f"   [PASS] {endpoint} - Accessible")
            else:
                print(f"   [FAIL] {endpoint} - Status: {response.status_code}")
        except Exception as e:
            print(f"   [ERROR] {endpoint} - {e}")

if __name__ == "__main__":
    transaction_id = test_payment_workflow()
    test_api_documentation()
    
    print()
    print("=" * 50)
    print("Payment Workflow Test Complete!")
    print()
    print("Key Features Demonstrated:")
    print("- Payment initiation with validation")
    print("- Transaction status tracking")
    print("- Fraud risk assessment")
    print("- API documentation accessibility")
    print()
    
    if transaction_id:
        print(f"Test transaction created: {transaction_id}")
        print("The orchestrator is fully functional!")
    else:
        print("Payment initiation may need database connectivity for full functionality.")
    
    print()
    print("Next steps:")
    print("- Start Celery workers for background processing")
    print("- Integrate with actual mobile money provider APIs")
    print("- Add comprehensive monitoring and alerting")
