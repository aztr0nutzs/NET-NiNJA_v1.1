#!/usr/bin/env python3
"""
Test script for WSL Bridge Mode functionality.

This script demonstrates:
1. WSL diagnostics
2. Provider selection with WSL mode
3. Basic network operations via WSL
"""

from __future__ import annotations

import sys

from capabilities import detect_capabilities
from providers import get_provider
from wsl_diagnostics import format_diagnostics_report, run_wsl_diagnostics


def test_wsl_diagnostics(distro: str = ""):
    """Run and display WSL diagnostics."""
    print("=" * 60)
    print("WSL BRIDGE MODE DIAGNOSTICS")
    print("=" * 60)
    
    diag = run_wsl_diagnostics(distro)
    report = format_diagnostics_report(diag)
    print(report)
    
    return diag.is_ready()


def test_wsl_provider(distro: str = ""):
    """Test WSL provider with basic operations."""
    print("\n" + "=" * 60)
    print("WSL PROVIDER TEST")
    print("=" * 60)
    
    # Detect capabilities in WSL mode
    print("\n[1/5] Detecting capabilities in WSL mode...")
    capabilities = detect_capabilities(backend_mode="wsl", wsl_distro=distro)
    print(f"  ✓ Platform: {capabilities.platform}")
    print(f"  ✓ Admin: {capabilities.is_admin}")
    print(f"  ✓ Tools detected: {sum(capabilities.tools.values())}")
    
    # Get WSL provider
    print("\n[2/5] Initializing WSL provider...")
    provider = get_provider(capabilities, backend_mode="wsl", wsl_distro=distro)
    print(f"  ✓ Provider: {provider.__class__.__name__}")
    
    # Test interface discovery
    print("\n[3/5] Testing interface discovery...")
    try:
        interfaces = provider.get_interfaces()
        print(f"  ✓ Found {len(interfaces)} interfaces")
        for iface in interfaces[:3]:  # Show first 3
            print(f"    - {iface.name}: {iface.state} ({iface.mac})")
            if iface.ipv4:
                print(f"      IPv4: {', '.join(iface.ipv4)}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False
    
    # Test route discovery
    print("\n[4/5] Testing route discovery...")
    try:
        routes = provider.get_routes()
        print(f"  ✓ Found {len(routes)} routes")
        for route in routes[:3]:  # Show first 3
            print(f"    - {route.destination} via {route.gateway} ({route.interface})")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False
    
    # Test neighbor discovery
    print("\n[5/5] Testing neighbor discovery...")
    try:
        neighbors = provider.get_neighbors()
        print(f"  ✓ Found {len(neighbors)} neighbors")
        for neighbor in neighbors[:3]:  # Show first 3
            print(f"    - {neighbor.ip}: {neighbor.mac} ({neighbor.state})")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED")
    print("=" * 60)
    return True


def main():
    """Main test runner."""
    distro = ""
    if len(sys.argv) > 1:
        distro = sys.argv[1]
        print(f"Using distro: {distro}")
    else:
        print("Using default WSL distro")
    
    # Run diagnostics
    if not test_wsl_diagnostics(distro):
        print("\n⚠️  WSL is not ready. Please fix the issues above.")
        print("Continuing with provider test anyway...\n")
    
    # Test provider
    try:
        success = test_wsl_provider(distro)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
