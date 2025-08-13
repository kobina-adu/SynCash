import asyncio
import random
from typing import Dict, Any
from src.models.transaction import PaymentProvider

async def simulate_provider_payment(provider: PaymentProvider, amount: float, recipient_phone: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Simulate a payment call to a mobile money provider.
    Randomly returns success, failure, or timeout to mimic real-world behavior.
    """
    # Simulate network latency
    await asyncio.sleep(random.uniform(0.2, 1.5))
    outcome = random.choices(
        ['success', 'fail', 'timeout'],
        weights=[0.85, 0.1, 0.05]
    )[0]
    if outcome == 'success':
        return {
            'status': 'confirmed',
            'provider_ref': f'MOCK{random.randint(10000,99999)}',
            'message': f'Simulated payment success with {provider.value}'
        }
    elif outcome == 'fail':
        return {
            'status': 'failed',
            'error': f'Simulated provider error: insufficient funds ({provider.value})'
        }
    else:
        # Simulate a timeout by raising
        raise asyncio.TimeoutError(f'Simulated provider timeout for {provider.value}')

async def simulate_provider_status(provider: PaymentProvider, provider_ref: str) -> Dict[str, Any]:
    """
    Simulate a status check call to a provider.
    """
    await asyncio.sleep(random.uniform(0.1, 0.5))
    # Randomly choose between confirmed, pending, or failed
    status = random.choices(
        ['confirmed', 'pending', 'failed'],
        weights=[0.8, 0.15, 0.05]
    )[0]
    return {
        'status': status,
        'provider_ref': provider_ref,
        'message': f'Simulated status for {provider.value}'
    }
