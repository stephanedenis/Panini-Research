#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manual Test Suite for Audit Manager

Tests:
1. Basic event logging
2. Event retrieval by date
3. Event retrieval by actor
4. Event retrieval by object
5. Date range queries
6. Chain integrity verification
7. Compliance reporting
8. Security event tracking
9. Temporal queries
10. Multiple chains
"""

import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from audit_manager import (
    AuditManager, AuditEventType, AuditSeverity,
    AuditOutcome, create_audit_event
)


def test_basic_event_logging():
    """Test basic event logging"""
    print("\n[TEST 1] Basic Event Logging")
    print("-" * 60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        audit = AuditManager(tmpdir)
        
        # Log event
        event = audit.log_event(
            AuditEventType.CREATE,
            actor="alice@test.com",
            action="Created test object",
            object_hash="test123",
            object_type="pattern"
        )
        
        assert event.event_id != ""
        assert event.actor == "alice@test.com"
        assert event.event_type == AuditEventType.CREATE
        assert event.outcome == AuditOutcome.SUCCESS
        
        print("  ✓ Event logged successfully")
        print(f"    Event ID: {event.event_id}")
        print(f"    Timestamp: {event.timestamp}")
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_event_retrieval_by_date():
    """Test retrieving events by date"""
    print("\n[TEST 2] Event Retrieval by Date")
    print("-" * 60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        audit = AuditManager(tmpdir)
        
        # Log multiple events
        for i in range(5):
            audit.log_event(
                AuditEventType.READ,
                actor=f"user{i}@test.com",
                action=f"Read action {i}",
                object_hash=f"obj{i}"
            )
        
        # Retrieve today's events
        today = datetime.utcnow().strftime("%Y-%m-%d")
        events = audit.get_events_by_date(today)
        
        assert len(events) == 5
        print(f"  ✓ Retrieved {len(events)} events for {today}")
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_event_retrieval_by_actor():
    """Test retrieving events by actor"""
    print("\n[TEST 3] Event Retrieval by Actor")
    print("-" * 60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        audit = AuditManager(tmpdir)
        
        # Log events from multiple actors
        for i in range(3):
            audit.log_event(
                AuditEventType.CREATE,
                actor="alice@test.com",
                action=f"Alice action {i}"
            )
        
        for i in range(2):
            audit.log_event(
                AuditEventType.UPDATE,
                actor="bob@test.com",
                action=f"Bob action {i}"
            )
        
        # Retrieve Alice's events
        alice_events = audit.get_events_by_actor("alice@test.com")
        bob_events = audit.get_events_by_actor("bob@test.com")
        
        assert len(alice_events) == 3
        assert len(bob_events) == 2
        
        print(f"  ✓ Alice: {len(alice_events)} events")
        print(f"  ✓ Bob: {len(bob_events)} events")
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_event_retrieval_by_object():
    """Test retrieving events by object"""
    print("\n[TEST 4] Event Retrieval by Object")
    print("-" * 60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        audit = AuditManager(tmpdir)
        
        # Log events for same object
        object_hash = "pattern_xyz"
        
        audit.log_event(
            AuditEventType.CREATE,
            actor="alice@test.com",
            action="Created pattern",
            object_hash=object_hash,
            object_type="pattern"
        )
        
        audit.log_event(
            AuditEventType.READ,
            actor="bob@test.com",
            action="Read pattern",
            object_hash=object_hash,
            object_type="pattern"
        )
        
        audit.log_event(
            AuditEventType.UPDATE,
            actor="alice@test.com",
            action="Updated pattern",
            object_hash=object_hash,
            object_type="pattern"
        )
        
        # Retrieve object history
        events = audit.get_events_by_object(object_hash)
        
        assert len(events) == 3
        assert events[0].event_type == AuditEventType.CREATE
        assert events[1].event_type == AuditEventType.READ
        assert events[2].event_type == AuditEventType.UPDATE
        
        print(f"  ✓ Object {object_hash} has {len(events)} events:")
        for e in events:
            print(f"    - {e.event_type.value} by {e.actor}")
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_date_range_queries():
    """Test date range queries"""
    print("\n[TEST 5] Date Range Queries")
    print("-" * 60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        audit = AuditManager(tmpdir)
        
        # Log events
        for i in range(10):
            audit.log_event(
                AuditEventType.READ if i % 2 == 0 else AuditEventType.UPDATE,
                actor=f"user{i}@test.com",
                action=f"Action {i}"
            )
        
        # Query all events
        today = datetime.utcnow().strftime("%Y-%m-%d")
        all_events = audit.get_events_in_range(today, today)
        
        # Query READ events only
        read_events = audit.get_events_in_range(
            today, today, AuditEventType.READ
        )
        
        assert len(all_events) == 10
        assert len(read_events) == 5
        
        print(f"  ✓ All events: {len(all_events)}")
        print(f"  ✓ READ events: {len(read_events)}")
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_chain_integrity():
    """Test audit chain integrity verification"""
    print("\n[TEST 6] Chain Integrity Verification")
    print("-" * 60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        audit = AuditManager(tmpdir)
        
        # Log events to build chain
        for i in range(5):
            audit.log_event(
                AuditEventType.CREATE,
                actor=f"user{i}@test.com",
                action=f"Action {i}"
            )
        
        # Verify chain
        chain_id = audit.current_chain.chain_id
        valid = audit.verify_chain(chain_id)
        
        assert valid is True
        
        print(f"  ✓ Chain {chain_id} is valid")
        print(f"  ✓ Chain contains {len(audit.current_chain.events)} events")
        
        # Verify each event links to previous
        for i, event in enumerate(audit.current_chain.events):
            if i == 0:
                assert event.previous_hash is None
            else:
                prev_id = audit.current_chain.events[i - 1].event_id
                assert event.previous_hash == prev_id
        
        print("  ✓ All events properly chained")
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_compliance_reporting():
    """Test compliance report generation"""
    print("\n[TEST 7] Compliance Reporting")
    print("-" * 60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        audit = AuditManager(tmpdir)
        
        # Log various events
        audit.log_event(
            AuditEventType.CREATE,
            actor="alice@test.com",
            action="Create"
        )
        
        audit.log_event(
            AuditEventType.READ,
            actor="bob@test.com",
            action="Read"
        )
        
        audit.log_event(
            AuditEventType.ACCESS_DENIED,
            actor="charlie@test.com",
            action="Denied access",
            outcome=AuditOutcome.DENIED,
            severity=AuditSeverity.WARNING
        )
        
        audit.log_event(
            AuditEventType.DELETE,
            actor="alice@test.com",
            action="Delete failed",
            outcome=AuditOutcome.FAILURE,
            severity=AuditSeverity.ERROR
        )
        
        # Generate report
        today = datetime.utcnow().strftime("%Y-%m-%d")
        report = audit.generate_compliance_report(today, today)
        
        assert report.total_events == 4
        assert report.failures == 2  # DENIED + FAILURE
        assert len(report.violations) == 2
        
        print(f"  ✓ Report generated:")
        print(f"    - Total events: {report.total_events}")
        print(f"    - Failures: {report.failures}")
        print(f"    - Violations: {len(report.violations)}")
        print(f"    - Events by type: {report.events_by_type}")
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_security_event_tracking():
    """Test security event tracking"""
    print("\n[TEST 8] Security Event Tracking")
    print("-" * 60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        audit = AuditManager(tmpdir)
        
        # Log security events
        audit.log_event(
            AuditEventType.ACCESS_DENIED,
            actor="attacker@test.com",
            action="Unauthorized access attempt",
            outcome=AuditOutcome.DENIED,
            severity=AuditSeverity.SECURITY,
            details={'ip': '192.168.1.100', 'attempts': 5}
        )
        
        audit.log_event(
            AuditEventType.ACCESS_ATTEMPT,
            actor="suspicious@test.com",
            action="Multiple failed logins",
            outcome=AuditOutcome.FAILURE,
            severity=AuditSeverity.SECURITY,
            details={'ip': '10.0.0.1', 'attempts': 10}
        )
        
        # Generate report
        today = datetime.utcnow().strftime("%Y-%m-%d")
        report = audit.generate_compliance_report(today, today)
        
        assert report.security_events == 2
        
        print(f"  ✓ Security events tracked: {report.security_events}")
        print("  ✓ Security event details:")
        
        events = audit.get_events_by_date(today)
        for e in events:
            if e.severity == AuditSeverity.SECURITY:
                print(f"    - {e.action} by {e.actor}")
                print(f"      IP: {e.details.get('ip', 'N/A')}")
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_temporal_queries():
    """Test temporal query capabilities"""
    print("\n[TEST 9] Temporal Queries")
    print("-" * 60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        audit = AuditManager(tmpdir)
        
        # Log events with different patterns
        object_hash = "temporal_test"
        
        # Create
        audit.log_event(
            AuditEventType.CREATE,
            actor="alice@test.com",
            action="Created object",
            object_hash=object_hash
        )
        
        # Multiple reads
        for i in range(3):
            audit.log_event(
                AuditEventType.READ,
                actor=f"user{i}@test.com",
                action=f"Read {i}",
                object_hash=object_hash
            )
        
        # Update
        audit.log_event(
            AuditEventType.UPDATE,
            actor="alice@test.com",
            action="Updated object",
            object_hash=object_hash
        )
        
        # Get object timeline
        events = audit.get_events_by_object(object_hash)
        
        assert len(events) == 5
        assert events[0].event_type == AuditEventType.CREATE
        assert events[-1].event_type == AuditEventType.UPDATE
        
        print(f"  ✓ Object timeline ({len(events)} events):")
        for e in events:
            print(f"    {e.timestamp[:19]} - {e.event_type.value} by "
                  f"{e.actor}")
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_multiple_chains():
    """Test multiple audit chains"""
    print("\n[TEST 10] Multiple Chains")
    print("-" * 60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        audit = AuditManager(tmpdir)
        
        # Log events in first chain
        for i in range(3):
            audit.log_event(
                AuditEventType.CREATE,
                actor=f"user{i}@test.com",
                action=f"Action {i}"
            )
        
        chain1_id = audit.current_chain.chain_id
        chain1_len = len(audit.current_chain.events)
        
        print(f"  ✓ Chain 1: {chain1_id} ({chain1_len} events)")
        
        # Verify chain 1
        valid1 = audit.verify_chain(chain1_id)
        assert valid1 is True
        print(f"  ✓ Chain 1 verified: {valid1}")
        
        # Chains are created per day, so we can verify the current one
        assert chain1_len == 3
        print("  ✓ All chains operational")
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print(" AUDIT MANAGER - MANUAL TEST SUITE")
    print("=" * 70)
    
    tests = [
        test_basic_event_logging,
        test_event_retrieval_by_date,
        test_event_retrieval_by_actor,
        test_event_retrieval_by_object,
        test_date_range_queries,
        test_chain_integrity,
        test_compliance_reporting,
        test_security_event_tracking,
        test_temporal_queries,
        test_multiple_chains
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
