#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manual test script for ProvenanceManager (no pytest required)
"""

import tempfile
import shutil
from pathlib import Path

from provenance_manager import (
    ProvenanceManager,
    SourceType,
    EventType,
    AgentType,
    ContributorRole,
    create_origin,
    create_event,
    create_contributor
)


def test_basic_provenance():
    """Test basic provenance creation and loading"""
    print("\n=== Test 1: Basic Provenance ===")
    
    # Create temp store
    temp_dir = tempfile.mkdtemp()
    store_path = Path(temp_dir)
    
    try:
        mgr = ProvenanceManager(store_path)
        
        # Create provenance
        origin = create_origin(
            source_type=SourceType.EMPIRICAL_ANALYSIS,
            created_by="panini-research",
            dataset="70_format_extractors",
            confidence=0.95
        )
        
        chain = mgr.create_provenance(
            object_hash="a7f3d912",
            object_type="pattern",
            origin=origin
        )
        
        print(f"✓ Created provenance for {chain.object_hash}")
        print(f"  Origin: {chain.origin.source_type.value}")
        print(f"  Creator: {chain.origin.created_by}")
        print(f"  Dataset: {chain.origin.dataset}")
        
        # Load it back
        loaded = mgr.load_provenance("a7f3d912", "pattern")
        assert loaded is not None
        assert loaded.object_hash == "a7f3d912"
        print(f"✓ Loaded provenance successfully")
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("✓ Test 1 passed!")


def test_evolution_events():
    """Test recording evolution events"""
    print("\n=== Test 2: Evolution Events ===")
    
    temp_dir = tempfile.mkdtemp()
    store_path = Path(temp_dir)
    
    try:
        mgr = ProvenanceManager(store_path)
        
        # Create provenance
        origin = create_origin(
            source_type=SourceType.MANUAL_CREATION,
            created_by="stephane@panini.dev"
        )
        
        chain = mgr.create_provenance(
            object_hash="test123",
            object_type="grammar",
            origin=origin
        )
        
        print(f"✓ Created provenance")
        
        # Add events
        event1 = create_event(
            event_type=EventType.CREATED,
            agent_identity="stephane@panini.dev",
            reason="Initial creation"
        )
        
        chain = mgr.record_event("test123", "grammar", event1)
        print(f"✓ Recorded CREATED event ({len(chain.evolution)} events total)")
        
        event2 = create_event(
            event_type=EventType.REFINED,
            agent_identity="stephane@panini.dev",
            derivation_hash="b8e0fa23",
            capabilities_added=["mask_support"],
            reason="Add mask support"
        )
        
        chain = mgr.record_event("test123", "grammar", event2)
        print(f"✓ Recorded REFINED event ({len(chain.evolution)} events total)")
        
        # Verify
        assert len(chain.evolution) == 2
        assert chain.evolution[1].event_type == EventType.REFINED
        print(f"✓ Evolution timeline correct")
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("✓ Test 2 passed!")


def test_contributors():
    """Test contributor tracking"""
    print("\n=== Test 3: Contributors ===")
    
    temp_dir = tempfile.mkdtemp()
    store_path = Path(temp_dir)
    
    try:
        mgr = ProvenanceManager(store_path)
        
        # Create provenance
        origin = create_origin(
            source_type=SourceType.CONSENSUS,
            created_by="community"
        )
        
        chain = mgr.create_provenance(
            object_hash="multi_contrib",
            object_type="pattern",
            origin=origin
        )
        
        # Add contributors
        contributors_data = [
            ("alice", ContributorRole.PRIMARY_AUTHOR, 40.0),
            ("bob", ContributorRole.CO_AUTHOR, 30.0),
            ("charlie", ContributorRole.MAINTAINER, 15.0),
            ("david", ContributorRole.REVIEWER, 10.0),
            ("eve", ContributorRole.TESTER, 5.0),
        ]
        
        for contrib_id, role, pct in contributors_data:
            contrib = create_contributor(
                contributor_id=contrib_id,
                role=role,
                contributions=["contribution"],
                contribution_pct=pct
            )
            
            mgr.add_contributor("multi_contrib", "pattern", contrib)
        
        chain = mgr.load_provenance("multi_contrib", "pattern")
        
        print(f"✓ Added {len(chain.contributors)} contributors")
        
        # Verify total percentage
        total_pct = sum(c.contribution_pct for c in chain.contributors)
        assert total_pct == 100.0
        print(f"✓ Total contribution: {total_pct}%")
        
        # Print contributors
        for c in chain.contributors:
            print(f"  - {c.id}: {c.role.value} ({c.contribution_pct}%)")
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("✓ Test 3 passed!")


def test_queries():
    """Test query functions"""
    print("\n=== Test 4: Queries ===")
    
    temp_dir = tempfile.mkdtemp()
    store_path = Path(temp_dir)
    
    try:
        mgr = ProvenanceManager(store_path)
        
        # Create multiple objects
        creator = "researcher@panini.dev"
        
        for i in range(3):
            origin = create_origin(
                source_type=SourceType.EMPIRICAL_ANALYSIS,
                created_by=creator,
                dataset=f"dataset_{i}"
            )
            
            mgr.create_provenance(
                object_hash=f"obj_{i}",
                object_type="pattern",
                origin=origin
            )
        
        print(f"✓ Created 3 objects")
        
        # Query by creator
        objects = mgr.find_by_creator(creator)
        assert len(objects) == 3
        print(f"✓ Find by creator: {len(objects)} objects found")
        
        # Query by origin
        empirical = mgr.find_by_origin(SourceType.EMPIRICAL_ANALYSIS)
        assert len(empirical) == 3
        print(f"✓ Find by origin: {len(empirical)} objects found")
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("✓ Test 4 passed!")


def test_yaml_export():
    """Test YAML export/import"""
    print("\n=== Test 5: YAML Export/Import ===")
    
    temp_dir = tempfile.mkdtemp()
    store_path = Path(temp_dir)
    
    try:
        mgr = ProvenanceManager(store_path)
        
        # Create provenance
        origin = create_origin(
            source_type=SourceType.MANUAL_CREATION,
            created_by="exporter"
        )
        
        chain = mgr.create_provenance(
            object_hash="yaml_test",
            object_type="pattern",
            origin=origin
        )
        
        # Add event
        event = create_event(
            event_type=EventType.REFINED,
            agent_identity="exporter",
            capabilities_added=["feature1", "feature2"]
        )
        mgr.record_event("yaml_test", "pattern", event)
        
        print(f"✓ Created provenance with 1 event")
        
        # Export to YAML
        yaml_path = store_path / "exported.yml"
        mgr.export_to_yaml("yaml_test", "pattern", yaml_path)
        assert yaml_path.exists()
        print(f"✓ Exported to YAML: {yaml_path}")
        
        # Show YAML content
        with open(yaml_path) as f:
            content = f.read()
        
        print("\nYAML Content (first 500 chars):")
        print("-" * 60)
        print(content[:500])
        print("-" * 60)
        
        # Import from YAML
        imported = mgr.import_from_yaml(yaml_path)
        assert imported.object_hash == "yaml_test"
        assert len(imported.evolution) == 1
        print(f"✓ Imported from YAML successfully")
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("✓ Test 5 passed!")


def test_full_history():
    """Test full history retrieval"""
    print("\n=== Test 6: Full History ===")
    
    temp_dir = tempfile.mkdtemp()
    store_path = Path(temp_dir)
    
    try:
        mgr = ProvenanceManager(store_path)
        
        # Create complex provenance
        origin = create_origin(
            source_type=SourceType.EMPIRICAL_ANALYSIS,
            created_by="analyzer",
            dataset="test_dataset",
            confidence=0.9
        )
        
        chain = mgr.create_provenance(
            object_hash="history_test",
            object_type="grammar",
            origin=origin
        )
        
        # Add 3 events
        for event_type in [EventType.CREATED, EventType.REFINED, 
                          EventType.CERTIFIED]:
            event = create_event(
                event_type=event_type,
                agent_identity="agent"
            )
            mgr.record_event("history_test", "grammar", event)
        
        # Add contributor
        contrib = create_contributor(
            contributor_id="contributor",
            role=ContributorRole.PRIMARY_AUTHOR,
            contributions=["all"]
        )
        mgr.add_contributor("history_test", "grammar", contrib)
        
        # Get full history
        history = mgr.get_full_history("history_test", "grammar")
        
        print(f"✓ Object: {history['object_hash']}")
        print(f"✓ Type: {history['object_type']}")
        print(f"✓ Events: {history['event_count']}")
        print(f"✓ Contributors: {history['contributor_count']}")
        print(f"✓ Created: {history['created_at']}")
        print(f"✓ Modified: {history['last_modified']}")
        
        assert history['event_count'] == 3
        assert history['contributor_count'] == 1
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("✓ Test 6 passed!")


def main():
    """Run all tests"""
    print("=" * 60)
    print("ProvenanceManager Manual Tests")
    print("=" * 60)
    
    tests = [
        test_basic_provenance,
        test_evolution_events,
        test_contributors,
        test_queries,
        test_yaml_export,
        test_full_history
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
