#!/usr/bin/env python3
import unittest
import asyncio
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test modules
from test_conversation_reset import TestConversationReset

def run_async_test(test_case):
    """Run an async test case in the event loop"""
    loop = asyncio.get_event_loop()
    for method_name in dir(test_case):
        if method_name.startswith('test_'):
            method = getattr(test_case, method_name)
            if asyncio.iscoroutinefunction(method):
                loop.run_until_complete(method())
            else:
                method()

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestConversationReset))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    
    # For regular tests, we can use the standard runner
    regular_result = runner.run(test_suite)
    
    # For async tests, we need to run them in the event loop
    for test_class in [TestConversationReset]:
        test_case = test_class()
        test_case.setUp()
        print(f"\nRunning async tests for {test_class.__name__}")
        run_async_test(test_case)
        test_case.tearDown()
    
    print("\nTest run completed") 