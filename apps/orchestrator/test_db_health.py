#!/usr/bin/env python3
"""
Test script for database health optimization
"""
import asyncio
import sys
sys.path.append('src')

async def test_db_health():
    from src.core.database import test_db_connection, get_connection_pool_stats
    from src.services.db_monitor import db_health_monitor
    
    print('=== Database Health Optimization Test ===')
    
    # Test 1: Enhanced connection test
    print('\n1. Enhanced Database Connection Test:')
    db_result = await test_db_connection()
    print(f'   Healthy: {db_result["healthy"]}')
    print(f'   Response Time: {db_result["response_time_ms"]}ms')
    print(f'   Connection Test: {db_result["connection_test"]}')
    print(f'   Transaction Test: {db_result["transaction_test"]}')
    print(f'   Table Access Test: {db_result["table_access_test"]}')
    if db_result.get('error'):
        print(f'   Error: {db_result["error"]}')
    
    # Test 2: Connection pool stats
    print('\n2. Connection Pool Statistics:')
    pool_stats = await get_connection_pool_stats()
    for key, value in pool_stats.items():
        print(f'   {key}: {value}')
    
    # Test 3: Health summary
    print('\n3. Health Monitor Summary:')
    summary = await db_health_monitor.get_health_summary()
    if 'error' in summary:
        print(f'   Error: {summary["error"]}')
    else:
        current = summary["current_status"]
        print(f'   Current Status: {current["healthy"]}')
        print(f'   Response Time: {current["response_time_ms"]}ms')
        if 'recent_performance' in summary:
            perf = summary['recent_performance']
            print(f'   Health Rate: {perf["health_rate"]:.2%}')
            print(f'   Avg Response: {perf["avg_response_time_ms"]}ms')
    
    # Test 4: Run diagnostics
    print('\n4. Database Diagnostics:')
    diagnostics = await db_health_monitor.run_diagnostics()
    if 'error' in diagnostics:
        print(f'   Error: {diagnostics["error"]}')
    else:
        for test_name, result in diagnostics.get('tests', {}).items():
            if isinstance(result, dict):
                status = 'PASS' if result.get('success', False) else 'FAIL'
                print(f'   {test_name}: {status}')
                if 'duration_ms' in result:
                    print(f'     Duration: {result["duration_ms"]}ms')
                if result.get('error'):
                    print(f'     Error: {result["error"]}')
    
    print('\n=== Database Health Test Complete ===')

if __name__ == "__main__":
    asyncio.run(test_db_health())
