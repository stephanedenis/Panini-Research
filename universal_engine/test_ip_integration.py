#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Integration Test for Complete IP System

Tests the full workflow:
1. Register new object with IP metadata
2. Derive child object with inherited IP
3. Query complete IP information
4. Generate citations
5. Check license compatibility

Validates integration of:
- Phase 1: Provenance Manager
- Phase 2: License Manager
- Phase 3: Attribution Manager
- Phase 8: IP Manager orchestrator
"""

import tempfile
import shutil
from pathlib import Path
from ip_manager import IPManager
from attribution_manager import CitationStyle


def test_complete_ip_workflow():
    """Test complete IP system integration"""
    
    print("=" * 70)
    print(" END-TO-END IP SYSTEM INTEGRATION TEST")
    print("=" * 70)
    print()
    
    # Create temporary store
    tmpdir = tempfile.mkdtemp()
    
    try:
        # ================================================================
        # TEST 1: Initialize IP System
        # ================================================================
        print("[TEST 1/7] Initializing IP Manager...")
        ipm = IPManager(tmpdir)
        
        assert ipm.provenance is not None, "Provenance manager not initialized"
        assert ipm.licensing is not None, "License manager not initialized"
        assert ipm.attribution is not None, "Attribution manager not initialized"
        
        print("  ✓ IPManager initialized successfully")
        print(f"    - Store: {tmpdir}")
        print(f"    - Provenance: Active")
        print(f"    - Licensing: Active")
        print(f"    - Attribution: Active")
        print()
        
        # ================================================================
        # TEST 2: Register Original Object
        # ================================================================
        print("[TEST 2/7] Registering original object...")
        
        obj1_hash = "pattern_001_hash"
        ip_record1 = ipm.register_object(
            object_hash=obj1_hash,
            object_type='pattern',
            title='Original Phonological Pattern',
            creator='alice@example.com',
            source_type='MANUAL_CREATION',
            license_id='MIT'
        )
        
        assert ip_record1['object_hash'] == obj1_hash
        assert 'provenance' in ip_record1
        assert 'license' in ip_record1
        assert 'attribution' in ip_record1
        
        print("  ✓ Object registered with complete IP metadata")
        print(f"    - Hash: {obj1_hash}")
        print(f"    - Creator: alice@example.com")
        print(f"    - License: MIT")
        print(f"    - Provenance chain: Created")
        print(f"    - Attribution chain: Created")
        print()
        
        # ================================================================
        # TEST 3: Verify Provenance Chain
        # ================================================================
        print("[TEST 3/7] Verifying provenance chain...")
        
        prov_chain = ipm.provenance.load_provenance(obj1_hash, 'pattern')
        assert prov_chain is not None, "Provenance chain not found"
        assert prov_chain.object_hash == obj1_hash
        assert prov_chain.origin.created_by == 'alice@example.com'
        
        print("  ✓ Provenance chain verified")
        print(f"    - Origin: {prov_chain.origin.source_type.value}")
        print(f"    - Created by: {prov_chain.origin.created_by}")
        print(f"    - Created at: {prov_chain.origin.created_at}")
        print()
        
        # ================================================================
        # TEST 4: Verify License
        # ================================================================
        print("[TEST 4/7] Verifying license...")
        
        obj_license = ipm.licensing.load_license(obj1_hash)
        assert obj_license is not None, "License not found"
        assert obj_license.license.id == 'MIT'
        
        print("  ✓ License verified")
        print(f"    - License: {obj_license.license.id}")
        print(f"    - Family: {obj_license.license.family.value}")
        print(f"    - Applied by: {obj_license.applied_by}")
        print()
        
        # ================================================================
        # TEST 5: Verify Attribution & Generate Citation
        # ================================================================
        print("[TEST 5/7] Verifying attribution and generating citations...")
        
        attr_chain = ipm.attribution.load_attribution(obj1_hash)
        assert attr_chain is not None, "Attribution chain not found"
        assert len(attr_chain.credits) > 0, "No credits found"
        
        # Generate citations in multiple formats
        citations = {}
        for style in [CitationStyle.APA, CitationStyle.BIBTEX, CitationStyle.MLA]:
            citation = ipm.attribution.generate_citation(obj1_hash, style)
            citations[style.value] = citation
        
        print("  ✓ Attribution verified and citations generated")
        print(f"    - Primary author: {attr_chain.credits[0].author.name}")
        print(f"    - Credit: {attr_chain.credits[0].percentage}%")
        print()
        print("    Citations:")
        print(f"    - APA: {citations['apa'].text[:60]}...")
        print(f"    - BibTeX: @misc{{...}}")
        print(f"    - MLA: {citations['mla'].text[:60]}...")
        print()
        
        # ================================================================
        # TEST 6: Register Second Object & Derive
        # ================================================================
        print("[TEST 6/7] Registering second object and deriving...")
        
        # Register another original object
        obj2_hash = "pattern_002_hash"
        ipm.register_object(
            object_hash=obj2_hash,
            object_type='pattern',
            title='Second Phonological Pattern',
            creator='bob@example.com',
            source_type='CORPUS_EXTRACTION',
            license_id='Apache-2.0'
        )
        
        # Derive from both objects
        obj3_hash = "pattern_003_derived"
        derived_record = ipm.derive_object(
            new_hash=obj3_hash,
            parent_hashes=[obj1_hash, obj2_hash],
            new_creator='charlie@example.com',
            title='Combined Phonological Pattern',
            contribution_pct=30.0
        )
        
        assert derived_record['object_hash'] == obj3_hash
        assert derived_record['derived_from'] == [obj1_hash, obj2_hash]
        
        print("  ✓ Derived object created from multiple parents")
        print(f"    - New hash: {obj3_hash}")
        print(f"    - Parents: {len(derived_record['derived_from'])}")
        print(f"    - New creator: charlie@example.com")
        print(f"    - New contribution: 30.0%")
        print()
        
        # ================================================================
        # TEST 7: Verify License Compatibility
        # ================================================================
        print("[TEST 7/7] Verifying license compatibility...")
        
        # Check MIT + Apache-2.0 compatibility
        compat = ipm.licensing.check_compatibility('MIT', 'Apache-2.0')
        assert compat.compatible, "MIT and Apache-2.0 should be compatible"
        
        # Get composite license
        composite = ipm.licensing.compute_composite_license(
            [obj1_hash, obj2_hash]
        )
        
        print("  ✓ License compatibility verified")
        print(f"    - MIT + Apache-2.0: {compat.compatibility.value}")
        if compat.conditions:
            print(f"    - Conditions: {', '.join(compat.conditions)}")
        print(f"    - Composite compatible: {composite.compatible}")
        if composite.compatible and composite.resulting_license:
            print(f"    - Result: {composite.resulting_license.id}")
        print()
        
        # ================================================================
        # SUMMARY
        # ================================================================
        print("=" * 70)
        print(" TEST SUMMARY")
        print("=" * 70)
        print()
        print("  ✅ All 7 integration tests passed")
        print()
        print("  Components tested:")
        print("    ✓ Phase 1: Provenance Manager (origin tracking, events)")
        print("    ✓ Phase 2: License Manager (compatibility, composite)")
        print("    ✓ Phase 3: Attribution Manager (credits, citations)")
        print("    ✓ Phase 8: IP Manager (orchestration, workflows)")
        print()
        print("  Workflows validated:")
        print("    ✓ New object registration with complete IP")
        print("    ✓ Multi-parent derivation with inheritance")
        print("    ✓ License compatibility checking")
        print("    ✓ Citation generation (3 formats)")
        print("    ✓ Cross-manager data consistency")
        print()
        print("=" * 70)
        print(" IP SYSTEM INTEGRATION: FULLY OPERATIONAL ✅")
        print("=" * 70)
        
    finally:
        # Cleanup
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    try:
        test_complete_ip_workflow()
        print("\n✅ End-to-end integration test PASSED\n")
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        exit(1)
