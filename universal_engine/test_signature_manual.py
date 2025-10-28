#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manual Test Suite for Signature Manager

Tests:
1. Key pair generation
2. Certificate creation
3. Object signing
4. Signature verification
5. Certificate validation
6. Certificate chain verification
7. Timestamp validation
8. Certificate revocation
9. Multiple signatures per object
10. Authentication workflow
"""

import tempfile
import shutil
from datetime import datetime, timedelta

from signature_manager import (
    SignatureManager, SignatureAlgorithm, SignatureStatus,
    CertificateStatus, verify_object_authenticity
)


def test_key_pair_generation():
    """Test key pair generation"""
    print("\n[TEST 1] Key Pair Generation")
    print("-" * 60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        sig_mgr = SignatureManager(tmpdir)
        
        # Generate key pair
        key_id, pub_key = sig_mgr.generate_key_pair("alice@test.com")
        
        assert key_id != ""
        assert pub_key != ""
        assert len(key_id) == 16
        
        print(f"  ✓ Key ID: {key_id}")
        print(f"  ✓ Public key: {pub_key[:40]}...")
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_certificate_creation():
    """Test certificate creation"""
    print("\n[TEST 2] Certificate Creation")
    print("-" * 60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        sig_mgr = SignatureManager(tmpdir)
        
        # Generate key and create certificate
        key_id, _ = sig_mgr.generate_key_pair("bob@test.com")
        cert = sig_mgr.create_certificate(
            subject="bob@test.com",
            key_id=key_id,
            issuer="Test CA",
            valid_days=365
        )
        
        assert cert.cert_id != ""
        assert cert.subject == "bob@test.com"
        assert cert.issuer == "Test CA"
        assert cert.status == CertificateStatus.VALID
        assert cert.is_valid()
        
        print(f"  ✓ Certificate created: {cert.cert_id}")
        print(f"  ✓ Subject: {cert.subject}")
        print(f"  ✓ Valid: {cert.is_valid()}")
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_object_signing():
    """Test object signing"""
    print("\n[TEST 3] Object Signing")
    print("-" * 60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        sig_mgr = SignatureManager(tmpdir)
        
        # Setup
        key_id, _ = sig_mgr.generate_key_pair("charlie@test.com")
        cert = sig_mgr.create_certificate(
            subject="charlie@test.com",
            key_id=key_id
        )
        
        # Sign object
        signature = sig_mgr.sign_object(
            object_hash="test_object_123",
            object_type="pattern",
            signer="charlie@test.com",
            key_id=key_id,
            cert_id=cert.cert_id,
            add_timestamp=False
        )
        
        assert signature.signature_id != ""
        assert signature.object_hash == "test_object_123"
        assert signature.signer == "charlie@test.com"
        assert signature.certificate is not None
        assert signature.certificate.cert_id == cert.cert_id
        
        print(f"  ✓ Signature ID: {signature.signature_id}")
        print(f"  ✓ Object: {signature.object_hash}")
        print(f"  ✓ Signer: {signature.signer}")
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_signature_verification():
    """Test signature verification"""
    print("\n[TEST 4] Signature Verification")
    print("-" * 60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        sig_mgr = SignatureManager(tmpdir)
        
        # Setup and sign
        key_id, _ = sig_mgr.generate_key_pair("dave@test.com")
        cert = sig_mgr.create_certificate(
            subject="dave@test.com",
            key_id=key_id
        )
        signature = sig_mgr.sign_object(
            object_hash="verified_object",
            object_type="pattern",
            signer="dave@test.com",
            key_id=key_id,
            cert_id=cert.cert_id
        )
        
        # Verify
        result = sig_mgr.verify_signature(signature)
        
        assert result.valid is True
        assert result.status == SignatureStatus.VALID
        assert result.certificate_valid is True
        assert len(result.errors) == 0
        
        print(f"  ✓ Signature valid: {result.valid}")
        print(f"  ✓ Status: {result.status.value}")
        print(f"  ✓ Certificate valid: {result.certificate_valid}")
        print(f"  ✓ Errors: {len(result.errors)}")
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_certificate_validation():
    """Test certificate validation"""
    print("\n[TEST 5] Certificate Validation")
    print("-" * 60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        sig_mgr = SignatureManager(tmpdir)
        
        # Create valid certificate
        key_id, _ = sig_mgr.generate_key_pair("eve@test.com")
        cert = sig_mgr.create_certificate(
            subject="eve@test.com",
            key_id=key_id,
            valid_days=365
        )
        
        assert cert.is_valid()
        assert cert.status == CertificateStatus.VALID
        
        # Check dates
        now = datetime.utcnow()
        valid_from = datetime.fromisoformat(cert.valid_from.rstrip('Z'))
        valid_until = datetime.fromisoformat(cert.valid_until.rstrip('Z'))
        
        assert valid_from <= now <= valid_until
        
        print(f"  ✓ Certificate valid: {cert.is_valid()}")
        print(f"  ✓ Valid from: {cert.valid_from}")
        print(f"  ✓ Valid until: {cert.valid_until}")
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_certificate_chain():
    """Test certificate chain verification"""
    print("\n[TEST 6] Certificate Chain Verification")
    print("-" * 60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        sig_mgr = SignatureManager(tmpdir)
        
        # Create root certificate
        root_key_id, _ = sig_mgr.generate_key_pair("root-ca@test.com")
        root_cert = sig_mgr.create_certificate(
            subject="Root CA",
            key_id=root_key_id,
            issuer="self-signed"
        )
        
        # Create intermediate certificate
        int_key_id, _ = sig_mgr.generate_key_pair("intermediate@test.com")
        int_cert = sig_mgr.create_certificate(
            subject="Intermediate CA",
            key_id=int_key_id,
            issuer="Root CA",
            parent_cert_id=root_cert.cert_id
        )
        
        # Verify chain
        assert len(int_cert.chain) == 1
        assert int_cert.chain[0] == root_cert.cert_id
        
        chain_valid = sig_mgr._verify_certificate_chain(int_cert)
        assert chain_valid is True
        
        print(f"  ✓ Root cert: {root_cert.cert_id}")
        print(f"  ✓ Intermediate cert: {int_cert.cert_id}")
        print(f"  ✓ Chain length: {len(int_cert.chain)}")
        print(f"  ✓ Chain valid: {chain_valid}")
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_timestamp_validation():
    """Test timestamp validation"""
    print("\n[TEST 7] Timestamp Validation")
    print("-" * 60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        sig_mgr = SignatureManager(tmpdir)
        
        # Setup and sign with timestamp
        key_id, _ = sig_mgr.generate_key_pair("frank@test.com")
        cert = sig_mgr.create_certificate(
            subject="frank@test.com",
            key_id=key_id
        )
        signature = sig_mgr.sign_object(
            object_hash="timestamped_object",
            object_type="pattern",
            signer="frank@test.com",
            key_id=key_id,
            cert_id=cert.cert_id,
            add_timestamp=True
        )
        
        # Verify with timestamp
        assert signature.timestamp is not None
        
        result = sig_mgr.verify_signature(signature)
        assert result.timestamp_valid is True
        
        print(f"  ✓ Timestamp ID: {signature.timestamp.timestamp_id}")
        print(f"  ✓ Timestamp: {signature.timestamp.timestamp}")
        print(f"  ✓ Authority: {signature.timestamp.authority}")
        print(f"  ✓ Valid: {result.timestamp_valid}")
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_certificate_revocation():
    """Test certificate revocation"""
    print("\n[TEST 8] Certificate Revocation")
    print("-" * 60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        sig_mgr = SignatureManager(tmpdir)
        
        # Create and revoke certificate
        key_id, _ = sig_mgr.generate_key_pair("grace@test.com")
        cert = sig_mgr.create_certificate(
            subject="grace@test.com",
            key_id=key_id
        )
        
        assert cert.status == CertificateStatus.VALID
        
        # Revoke
        revoked = sig_mgr.revoke_certificate(
            cert.cert_id,
            reason="Key compromised"
        )
        assert revoked is True
        
        # Load and check status
        from pathlib import Path
        import json
        cert_path = Path(tmpdir) / "signatures" / "certificates"
        cert_path = cert_path / f"{cert.cert_id}.json"
        
        with open(cert_path) as f:
            cert_data = json.load(f)
        
        assert cert_data['status'] == CertificateStatus.REVOKED.value
        
        print(f"  ✓ Certificate revoked: {revoked}")
        print(f"  ✓ Status: {cert_data['status']}")
        print(f"  ✓ Reason: {cert_data['metadata']['revocation_reason']}")
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_multiple_signatures():
    """Test multiple signatures per object"""
    print("\n[TEST 9] Multiple Signatures per Object")
    print("-" * 60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        sig_mgr = SignatureManager(tmpdir)
        
        object_hash = "multi_signed_object"
        
        # Sign by multiple users
        signers = ["alice@test.com", "bob@test.com", "charlie@test.com"]
        
        for signer in signers:
            key_id, _ = sig_mgr.generate_key_pair(signer)
            cert = sig_mgr.create_certificate(
                subject=signer,
                key_id=key_id
            )
            sig_mgr.sign_object(
                object_hash=object_hash,
                object_type="pattern",
                signer=signer,
                key_id=key_id,
                cert_id=cert.cert_id
            )
        
        # Get all signatures
        signatures = sig_mgr.get_signatures(object_hash)
        
        assert len(signatures) == 3
        
        signers_found = {sig.signer for sig in signatures}
        assert signers_found == set(signers)
        
        print(f"  ✓ Object: {object_hash}")
        print(f"  ✓ Signatures: {len(signatures)}")
        print(f"  ✓ Signers:")
        for sig in signatures:
            print(f"    - {sig.signer}")
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_authentication_workflow():
    """Test complete authentication workflow"""
    print("\n[TEST 10] Authentication Workflow")
    print("-" * 60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        sig_mgr = SignatureManager(tmpdir)
        
        # Create and sign object
        object_hash = "auth_test_object"
        
        key_id, _ = sig_mgr.generate_key_pair("henry@test.com")
        cert = sig_mgr.create_certificate(
            subject="henry@test.com",
            key_id=key_id
        )
        sig_mgr.sign_object(
            object_hash=object_hash,
            object_type="pattern",
            signer="henry@test.com",
            key_id=key_id,
            cert_id=cert.cert_id,
            add_timestamp=True
        )
        
        # Verify authenticity
        authentic, results = verify_object_authenticity(
            sig_mgr,
            object_hash
        )
        
        assert authentic is True
        assert len(results) == 1
        assert results[0].valid is True
        assert results[0].certificate_valid is True
        assert results[0].timestamp_valid is True
        
        print(f"  ✓ Object authenticated: {authentic}")
        print(f"  ✓ Signatures verified: {len(results)}")
        print(f"  ✓ All valid: {all(r.valid for r in results)}")
        print(f"  ✓ Certificate valid: {results[0].certificate_valid}")
        print(f"  ✓ Timestamp valid: {results[0].timestamp_valid}")
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print(" SIGNATURE MANAGER - MANUAL TEST SUITE")
    print("=" * 70)
    
    tests = [
        test_key_pair_generation,
        test_certificate_creation,
        test_object_signing,
        test_signature_verification,
        test_certificate_validation,
        test_certificate_chain,
        test_timestamp_validation,
        test_certificate_revocation,
        test_multiple_signatures,
        test_authentication_workflow
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n  ❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n  ❌ ERROR: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print(" TEST RESULTS")
    print("=" * 70)
    print(f"  Total: {len(tests)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    
    if failed == 0:
        print("\n  ✅ ALL TESTS PASSED")
    else:
        print(f"\n  ❌ {failed} TEST(S) FAILED")
    
    print("=" * 70)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
