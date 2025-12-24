#!/usr/bin/env python3
"""
Simple security test runner that doesn't require pytest.
Run basic security validation tests.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def test_command_injection_prevention():
    """Test that shell metacharacters are properly quoted."""
    print("Testing command injection prevention...")
    
    try:
        # Import after path is set
        import netreaper_gui
        
        dangerous_inputs = [
            "target; rm -rf /",
            "target && cat /etc/passwd",
            "target || whoami",
        ]
        
        for dangerous in dangerous_inputs:
            quoted = netreaper_gui.quote(dangerous)
            # Should be quoted as single argument
            assert quoted.startswith("'") or quoted.startswith('"'), f"Failed to quote: {dangerous}"
        
        print("✓ Command injection prevention tests passed")
        return True
    except Exception as e:
        print(f"✗ Command injection prevention tests failed: {e}")
        return False

def test_output_sanitization():
    """Test that sensitive data is redacted from output."""
    print("Testing output sanitization...")
    
    try:
        import netreaper_gui
        
        thread = netreaper_gui.CommandThread("dummy", sanitize_output=True)
        
        test_cases = [
            ("password=secret123", "***REDACTED***"),
            ("api_key=sk_live_123", "***REDACTED***"),
            ("token: ghp_abc123", "***REDACTED***"),
        ]
        
        for input_line, expected in test_cases:
            sanitized = thread._sanitize_output(input_line)
            assert expected in sanitized, f"Failed to sanitize: {input_line}"
            # Verify actual secret is not present
            if "secret123" in input_line:
                assert "secret123" not in sanitized
        
        print("✓ Output sanitization tests passed")
        return True
    except Exception as e:
        print(f"✗ Output sanitization tests failed: {e}")
        return False

def test_api_security():
    """Test API security features."""
    print("Testing API security...")
    
    try:
        # Set required environment variables
        os.environ["NETREAPER_SECRET"] = "test_secret_key_at_least_32_chars_long_12345"
        os.environ["NETREAPER_PASSWORD"] = "test_password"
        
        import main
        
        # Test token creation and verification
        token = main.create_token({"user": "test"})
        assert token is not None, "Failed to create token"
        
        payload = main.verify_token(token)
        assert payload is not None, "Failed to verify valid token"
        assert payload["user"] == "test", "Token payload incorrect"
        
        # Test invalid token
        invalid = main.verify_token("invalid_token")
        assert invalid is None, "Invalid token should return None"
        
        # Test rate limiting
        client_id = "test_client"
        for i in range(main.MAX_AUTH_ATTEMPTS):
            assert main.check_rate_limit(client_id) == True
        
        # Should be blocked after max attempts
        assert main.check_rate_limit(client_id) == False, "Rate limiting not working"
        
        print("✓ API security tests passed")
        return True
    except Exception as e:
        print(f"✗ API security tests failed: {e}")
        return False

def test_input_validation():
    """Test input validation."""
    print("Testing input validation...")
    
    try:
        import netreaper_gui
        
        # Test empty input handling
        assert netreaper_gui.quote("") == ""
        assert netreaper_gui.quote(None) == ""
        
        # Test path traversal patterns are quoted
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
        ]
        
        for path in dangerous_paths:
            quoted = netreaper_gui.quote(path)
            # Should be quoted as single argument
            assert quoted.count("'") >= 2 or quoted.count('"') >= 2
        
        print("✓ Input validation tests passed")
        return True
    except Exception as e:
        print(f"✗ Input validation tests failed: {e}")
        return False

def test_windows_security():
    """Test Windows-specific security features."""
    print("Testing Windows security...")
    
    try:
        import netreaper_gui_windows
        
        # Test command thread sanitization
        thread = netreaper_gui_windows.CommandThread("dummy", sanitize_output=True)
        
        test_line = "password=secret123"
        sanitized = thread._sanitize_output(test_line)
        assert "***REDACTED***" in sanitized
        assert "secret123" not in sanitized
        
        print("✓ Windows security tests passed")
        return True
    except Exception as e:
        print(f"✗ Windows security tests failed: {e}")
        return False

def main():
    """Run all security tests."""
    print("=" * 60)
    print("NetReaper Security Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        test_command_injection_prevention,
        test_output_sanitization,
        test_api_security,
        test_input_validation,
        test_windows_security,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test crashed: {e}")
            results.append(False)
        print()
    
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All security tests passed!")
        return 0
    else:
        print(f"✗ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
