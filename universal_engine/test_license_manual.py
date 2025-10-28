#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manual Tests for License Manager

Tests license application, compatibility checking, and composite license
computation. No pytest required - runs standalone.
"""

import tempfile
from pathlib import Path
from license_manager import (
    LicenseManager,
    LicenseFamily,
    Compatibility,
    create_custom_license
)


def test_basic_license_application():
    """Test 1: Apply license to object"""
    print("=== Test 1: Basic License Application ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = LicenseManager(store_root=tmpdir)
        
        # Apply MIT license
        obj_lic = manager.apply_license(
            object_hash="test_obj_001",
            license_id="MIT",
            applied_by="test-user"
        )
        
        assert obj_lic.object_hash == "test_obj_001"
        assert obj_lic.license.id == "MIT"
        assert obj_lic.applied_by == "test-user"
        print("[OK] Applied MIT license")
        
        # Load it back
        loaded = manager.load_license("test_obj_001")
        assert loaded is not None
        assert loaded.license.id == "MIT"
        print("[OK] Loaded license successfully")
        
    print("[OK] Test 1 passed!\n")


def test_dual_licensing():
    """Test 2: Dual licensing (MIT/Apache-2.0)"""
    print("=== Test 2: Dual Licensing ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = LicenseManager(store_root=tmpdir)
        
        # Apply dual license
        obj_lic = manager.apply_license(
            object_hash="dual_obj",
            license_id="MIT",
            secondary_licenses=["Apache-2.0"],
            applied_by="maintainer"
        )
        
        assert len(obj_lic.secondary_licenses) == 1
        assert obj_lic.secondary_licenses[0].id == "Apache-2.0"
        print("[OK] Applied dual license (MIT + Apache-2.0)")
        
        # Verify both licenses
        print(f"  Primary: {obj_lic.license.id}")
        print(f"  Secondary: {obj_lic.secondary_licenses[0].id}")
        
    print("[OK] Test 2 passed!\n")


def test_compatibility_permissive():
    """Test 3: Permissive license compatibility"""
    print("=== Test 3: Permissive License Compatibility ===")
    
    manager = LicenseManager()
    
    # MIT + BSD (should be compatible)
    result = manager.check_compatibility("MIT", "BSD-3-Clause")
    assert result.compatible
    assert result.compatibility == Compatibility.COMPATIBLE
    print("[OK] MIT + BSD-3-Clause: COMPATIBLE")
    
    # MIT + Apache (should be compatible)
    result = manager.check_compatibility("MIT", "Apache-2.0")
    assert result.compatible
    print("[OK] MIT + Apache-2.0: COMPATIBLE")
    
    # Apache + BSD (should be compatible)
    result = manager.check_compatibility("Apache-2.0", "BSD-2-Clause")
    assert result.compatible
    print("[OK] Apache-2.0 + BSD-2-Clause: COMPATIBLE")
    
    print("[OK] Test 3 passed!\n")


def test_compatibility_copyleft():
    """Test 4: Copyleft compatibility"""
    print("=== Test 4: Copyleft Compatibility ===")
    
    manager = LicenseManager()
    
    # MIT + GPL (one-way: MIT can go into GPL)
    result = manager.check_compatibility("MIT", "GPL-3.0")
    assert result.compatible
    assert result.compatibility == Compatibility.ONE_WAY
    assert result.resulting_license.id == "GPL-3.0"
    print("[OK] MIT + GPL-3.0: ONE_WAY (result: GPL-3.0)")
    print(f"     Conditions: {result.conditions}")
    
    # GPL + GPL (same version: compatible)
    result = manager.check_compatibility("GPL-3.0", "GPL-3.0")
    assert result.compatible
    assert result.compatibility == Compatibility.COMPATIBLE
    print("[OK] GPL-3.0 + GPL-3.0: COMPATIBLE")
    
    # LGPL + MIT (compatible)
    result = manager.check_compatibility("LGPL-3.0", "MIT")
    assert result.compatible
    print("[OK] LGPL-3.0 + MIT: COMPATIBLE")
    
    print("[OK] Test 4 passed!\n")


def test_compatibility_conflicts():
    """Test 5: License conflicts"""
    print("=== Test 5: License Conflicts ===")
    
    manager = LicenseManager()
    
    # CC-BY-SA + MIT (incompatible: ShareAlike conflict)
    result = manager.check_compatibility("CC-BY-SA-4.0", "MIT")
    assert not result.compatible
    assert result.compatibility == Compatibility.INCOMPATIBLE
    print("[OK] CC-BY-SA-4.0 + MIT: INCOMPATIBLE")
    print(f"     Conflicts: {result.conflicts}")
    print(f"     Recommendations: {result.recommendations}")
    
    print("[OK] Test 5 passed!\n")


def test_composite_license():
    """Test 6: Composite license computation"""
    print("=== Test 6: Composite License Computation ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = LicenseManager(store_root=tmpdir)
        
        # Create 3 parent objects with different licenses
        manager.apply_license("parent_1", "MIT", applied_by="user1")
        manager.apply_license("parent_2", "BSD-3-Clause", applied_by="user2")
        manager.apply_license("parent_3", "Apache-2.0", applied_by="user3")
        
        print("[OK] Created 3 parent objects:")
        print("     parent_1: MIT")
        print("     parent_2: BSD-3-Clause")
        print("     parent_3: Apache-2.0")
        
        # Compute composite (all permissive → should be compatible)
        result = manager.compute_composite_license([
            "parent_1", "parent_2", "parent_3"
        ])
        
        assert result.compatible
        assert result.resulting_license is not None
        print(f"[OK] Composite license: {result.resulting_license.id}")
        print(f"     Compatible: {result.compatible}")
        
    print("[OK] Test 6 passed!\n")


def test_composite_with_copyleft():
    """Test 7: Composite license with copyleft"""
    print("=== Test 7: Composite License with Copyleft ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = LicenseManager(store_root=tmpdir)
        
        # Mix permissive + copyleft
        manager.apply_license("p1", "MIT", applied_by="user1")
        manager.apply_license("p2", "GPL-3.0", applied_by="user2")
        
        print("[OK] Created 2 parents:")
        print("     p1: MIT")
        print("     p2: GPL-3.0")
        
        # Compute composite (MIT + GPL → GPL)
        result = manager.compute_composite_license(["p1", "p2"])
        
        assert result.compatible
        assert result.resulting_license.id == "GPL-3.0"
        print(f"[OK] Composite: {result.resulting_license.id}")
        print(f"     Conditions: {result.conditions}")
        
    print("[OK] Test 7 passed!\n")


def test_composite_incompatible():
    """Test 8: Composite with incompatible licenses"""
    print("=== Test 8: Composite with Incompatible Licenses ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = LicenseManager(store_root=tmpdir)
        
        # Incompatible: MIT + CC-BY-SA
        manager.apply_license("p1", "MIT", applied_by="user1")
        manager.apply_license("p2", "CC-BY-SA-4.0", applied_by="user2")
        
        print("[OK] Created 2 parents:")
        print("     p1: MIT")
        print("     p2: CC-BY-SA-4.0")
        
        # Compute composite (should fail)
        result = manager.compute_composite_license(["p1", "p2"])
        
        assert not result.compatible
        print(f"[OK] Incompatible (as expected)")
        print(f"     Conflicts: {result.conflicts}")
        print(f"     Recommendations: {result.recommendations}")
        
    print("[OK] Test 8 passed!\n")


def test_license_families():
    """Test 9: List licenses by family"""
    print("=== Test 9: License Families ===")
    
    manager = LicenseManager()
    
    # Permissive
    permissive = manager.list_licenses(LicenseFamily.PERMISSIVE)
    assert len(permissive) > 0
    print(f"[OK] Permissive licenses: {len(permissive)}")
    for lic in permissive[:3]:
        print(f"     - {lic.id}")
    
    # Copyleft Strong
    copyleft = manager.list_licenses(LicenseFamily.COPYLEFT_STRONG)
    assert len(copyleft) > 0
    print(f"[OK] Strong Copyleft: {len(copyleft)}")
    for lic in copyleft:
        print(f"     - {lic.id}")
    
    # Creative Commons
    cc = manager.list_licenses(LicenseFamily.CREATIVE_COMMONS)
    assert len(cc) > 0
    print(f"[OK] Creative Commons: {len(cc)}")
    for lic in cc[:3]:
        print(f"     - {lic.id}")
    
    print("[OK] Test 9 passed!\n")


def test_custom_license():
    """Test 10: Create and register custom license"""
    print("=== Test 10: Custom License ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = LicenseManager(store_root=tmpdir)
        
        # Create custom license
        custom = create_custom_license(
            license_id="PANINI-1.0",
            name="Panini Research License v1.0",
            family=LicenseFamily.CUSTOM,
            attribution_required=True,
            commercial_use=False,
            share_alike=True
        )
        
        # Register it
        manager.register_license(custom)
        
        # Verify registration
        retrieved = manager.get_license("PANINI-1.0")
        assert retrieved is not None
        assert retrieved.name == "Panini Research License v1.0"
        assert not retrieved.commercial_use
        print("[OK] Created custom license: PANINI-1.0")
        print(f"     Commercial use: {retrieved.commercial_use}")
        print(f"     Attribution required: {retrieved.attribution_required}")
        print(f"     ShareAlike: {retrieved.share_alike}")
        
        # Apply it to object
        obj_lic = manager.apply_license(
            "custom_obj",
            "PANINI-1.0",
            applied_by="panini-team"
        )
        
        assert obj_lic.license.id == "PANINI-1.0"
        print("[OK] Applied custom license to object")
        
    print("[OK] Test 10 passed!\n")


def test_yaml_export():
    """Test 11: YAML export"""
    print("=== Test 11: YAML Export ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = LicenseManager(store_root=tmpdir)
        
        # Apply license
        manager.apply_license(
            "yaml_test",
            "MIT",
            applied_by="exporter",
            custom_terms="For academic use only"
        )
        
        # Export to YAML
        yaml_path = f"{tmpdir}/license.yml"
        manager.export_to_yaml("yaml_test", yaml_path)
        
        assert Path(yaml_path).exists()
        print("[OK] Exported to YAML")
        
        # Read and display first 200 chars
        with open(yaml_path, 'r') as f:
            content = f.read()
            print(f"     Content preview (200 chars):")
            print(f"     {content[:200]}")
        
    print("[OK] Test 11 passed!\n")


def test_find_compatible():
    """Test 12: Find compatible licenses"""
    print("=== Test 12: Find Compatible Licenses ===")
    
    manager = LicenseManager()
    
    # Find licenses compatible with MIT
    compatible = manager.find_compatible_licenses("MIT")
    
    print(f"[OK] Found {len(compatible)} licenses compatible with MIT:")
    for lic_id, compat_type in compatible[:5]:
        print(f"     - {lic_id}: {compat_type.value}")
    
    # Find licenses compatible with GPL-3.0
    compatible_gpl = manager.find_compatible_licenses("GPL-3.0")
    print(f"[OK] Found {len(compatible_gpl)} licenses compatible with GPL-3.0")
    
    print("[OK] Test 12 passed!\n")


def run_all_tests():
    """Run all manual tests"""
    print("=" * 60)
    print("License Manager Manual Tests")
    print("=" * 60 + "\n")
    
    tests = [
        test_basic_license_application,
        test_dual_licensing,
        test_compatibility_permissive,
        test_compatibility_copyleft,
        test_compatibility_conflicts,
        test_composite_license,
        test_composite_with_copyleft,
        test_composite_incompatible,
        test_license_families,
        test_custom_license,
        test_yaml_export,
        test_find_compatible,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test_func.__name__}: {e}\n")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test_func.__name__}: {e}\n")
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
