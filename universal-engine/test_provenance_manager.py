"""
Tests for ProvenanceManager

Tests:
1. Create provenance chain with origin
2. Record evolution events
3. Add contributors
4. Query by creator
5. Query by origin type
6. Timeline view
7. Multiple contributors tracking
8. Full history retrieval
9. YAML export/import
10. Index updates
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from provenance_manager import (
    ProvenanceManager,
    Origin,
    EvolutionEvent,
    Agent,
    Contributor,
    SourceType,
    EventType,
    AgentType,
    ContributorRole,
    create_origin,
    create_event,
    create_contributor
)


@pytest.fixture
def temp_store():
    """Create temporary store directory"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def provenance_mgr(temp_store):
    """Create ProvenanceManager instance"""
    return ProvenanceManager(temp_store)


def test_create_provenance_chain(provenance_mgr):
    """Test 1: Create provenance chain with origin"""
    # Create origin
    origin = create_origin(
        source_type=SourceType.EMPIRICAL_ANALYSIS,
        created_by="panini-research",
        dataset="70_format_extractors",
        analysis_hash="b62a2d8f",
        confidence=0.95
    )
    
    # Create provenance chain
    chain = provenance_mgr.create_provenance(
        object_hash="a7f3d912",
        object_type="pattern",
        origin=origin
    )
    
    # Verify
    assert chain.object_hash == "a7f3d912"
    assert chain.object_type == "pattern"
    assert chain.origin.source_type == SourceType.EMPIRICAL_ANALYSIS
    assert chain.origin.created_by == "panini-research"
    assert chain.origin.dataset == "70_format_extractors"
    assert chain.origin.confidence == 0.95
    assert len(chain.evolution) == 0
    assert len(chain.contributors) == 0
    
    # Verify saved to file
    loaded = provenance_mgr.load_provenance("a7f3d912", "pattern")
    assert loaded is not None
    assert loaded.object_hash == "a7f3d912"
    assert loaded.origin.created_by == "panini-research"


def test_record_evolution_events(provenance_mgr):
    """Test 2: Record evolution events"""
    # Create provenance
    origin = create_origin(
        source_type=SourceType.MANUAL_CREATION,
        created_by="stephane@panini.dev"
    )
    
    chain = provenance_mgr.create_provenance(
        object_hash="test123",
        object_type="grammar",
        origin=origin
    )
    
    # Record creation event
    event1 = create_event(
        event_type=EventType.CREATED,
        agent_identity="stephane@panini.dev",
        agent_type=AgentType.HUMAN,
        reason="Initial creation"
    )
    
    chain = provenance_mgr.record_event("test123", "grammar", event1)
    assert len(chain.evolution) == 1
    assert chain.evolution[0].event_type == EventType.CREATED
    
    # Record refinement event
    event2 = create_event(
        event_type=EventType.REFINED,
        agent_identity="stephane@panini.dev",
        derivation_hash="b8e0fa23",
        capabilities_added=["mask_support"],
        reason="Add mask support"
    )
    
    chain = provenance_mgr.record_event("test123", "grammar", event2)
    assert len(chain.evolution) == 2
    assert chain.evolution[1].event_type == EventType.REFINED
    assert "mask_support" in chain.evolution[1].capabilities_added
    
    # Verify persistence
    loaded = provenance_mgr.load_provenance("test123", "grammar")
    assert len(loaded.evolution) == 2


def test_add_contributors(provenance_mgr):
    """Test 3: Add contributors"""
    # Create provenance
    origin = create_origin(
        source_type=SourceType.MANUAL_CREATION,
        created_by="alice@example.com"
    )
    
    chain = provenance_mgr.create_provenance(
        object_hash="contrib_test",
        object_type="pattern",
        origin=origin
    )
    
    # Add primary author
    contrib1 = create_contributor(
        contributor_id="alice@example.com",
        role=ContributorRole.PRIMARY_AUTHOR,
        contributions=["design", "implementation"],
        contribution_pct=75.0
    )
    
    chain = provenance_mgr.add_contributor(
        "contrib_test", "pattern", contrib1
    )
    assert len(chain.contributors) == 1
    assert chain.contributors[0].id == "alice@example.com"
    assert chain.contributors[0].role == ContributorRole.PRIMARY_AUTHOR
    
    # Add co-author
    contrib2 = create_contributor(
        contributor_id="bob@example.com",
        role=ContributorRole.CO_AUTHOR,
        contributions=["testing", "documentation"],
        contribution_pct=25.0
    )
    
    chain = provenance_mgr.add_contributor(
        "contrib_test", "pattern", contrib2
    )
    assert len(chain.contributors) == 2
    
    # Update existing contributor
    contrib1_update = create_contributor(
        contributor_id="alice@example.com",
        role=ContributorRole.PRIMARY_AUTHOR,
        contributions=["refinement"],
        contribution_pct=80.0
    )
    
    chain = provenance_mgr.add_contributor(
        "contrib_test", "pattern", contrib1_update
    )
    
    # Should still have 2 contributors (updated, not added)
    assert len(chain.contributors) == 2
    
    # Alice should have combined contributions
    alice = next(c for c in chain.contributors 
                 if c.id == "alice@example.com")
    assert "design" in alice.contributions
    assert "refinement" in alice.contributions
    assert alice.contribution_pct == 80.0


def test_find_by_creator(provenance_mgr):
    """Test 4: Query by creator"""
    # Create multiple objects by same creator
    creator = "researcher@panini.dev"
    
    for i in range(3):
        origin = create_origin(
            source_type=SourceType.EMPIRICAL_ANALYSIS,
            created_by=creator,
            dataset=f"dataset_{i}"
        )
        
        provenance_mgr.create_provenance(
            object_hash=f"obj_{i}",
            object_type="pattern",
            origin=origin
        )
    
    # Query
    objects = provenance_mgr.find_by_creator(creator)
    assert len(objects) == 3
    
    # Verify all have correct creator
    for obj in objects:
        loaded = provenance_mgr.load_provenance(
            obj['object_hash'], obj['object_type']
        )
        assert loaded.origin.created_by == creator


def test_find_by_origin_type(provenance_mgr):
    """Test 5: Query by origin type"""
    # Create objects with different origin types
    origins = [
        (SourceType.EMPIRICAL_ANALYSIS, "auto1"),
        (SourceType.EMPIRICAL_ANALYSIS, "auto2"),
        (SourceType.MANUAL_CREATION, "manual1"),
        (SourceType.DERIVED, "derived1"),
    ]
    
    for source_type, hash_suffix in origins:
        origin = create_origin(
            source_type=source_type,
            created_by="creator"
        )
        
        provenance_mgr.create_provenance(
            object_hash=f"test_{hash_suffix}",
            object_type="pattern",
            origin=origin
        )
    
    # Query empirical analysis
    empirical = provenance_mgr.find_by_origin(SourceType.EMPIRICAL_ANALYSIS)
    assert len(empirical) == 2
    
    # Query manual creation
    manual = provenance_mgr.find_by_origin(SourceType.MANUAL_CREATION)
    assert len(manual) == 1
    
    # Query derived
    derived = provenance_mgr.find_by_origin(SourceType.DERIVED)
    assert len(derived) == 1


def test_timeline_view(provenance_mgr):
    """Test 6: Timeline view"""
    # Create provenance with specific date
    fixed_date = "2025-10-28T10:00:00Z"
    
    origin = Origin(
        source_type=SourceType.MANUAL_CREATION,
        created_at=fixed_date,
        created_by="tester"
    )
    
    chain = provenance_mgr.create_provenance(
        object_hash="timeline_test",
        object_type="pattern",
        origin=origin
    )
    
    # Add event on same date
    event = EvolutionEvent(
        timestamp=fixed_date,
        event_type=EventType.REFINED,
        agent=Agent(
            agent_type=AgentType.HUMAN,
            identity="tester"
        )
    )
    
    provenance_mgr.record_event("timeline_test", "pattern", event)
    
    # Query timeline
    date_str = fixed_date[:10]  # "2025-10-28"
    events = provenance_mgr.timeline_view(date_str)
    
    assert len(events) >= 1
    
    # Verify event details
    timeline_event = next(
        e for e in events 
        if e['object_hash'] == 'timeline_test'
    )
    assert timeline_event['event_type'] == 'refined'
    assert timeline_event['agent'] == 'tester'


def test_multiple_contributors_tracking(provenance_mgr):
    """Test 7: Multiple contributors tracking"""
    # Create object
    origin = create_origin(
        source_type=SourceType.CONSENSUS,
        created_by="community"
    )
    
    chain = provenance_mgr.create_provenance(
        object_hash="multi_contrib",
        object_type="pattern",
        origin=origin
    )
    
    # Add 5 contributors with different roles
    contributors = [
        ("alice", ContributorRole.PRIMARY_AUTHOR, 40.0),
        ("bob", ContributorRole.CO_AUTHOR, 30.0),
        ("charlie", ContributorRole.MAINTAINER, 15.0),
        ("david", ContributorRole.REVIEWER, 10.0),
        ("eve", ContributorRole.TESTER, 5.0),
    ]
    
    for contrib_id, role, pct in contributors:
        contrib = create_contributor(
            contributor_id=contrib_id,
            role=role,
            contributions=["contribution"],
            contribution_pct=pct
        )
        
        provenance_mgr.add_contributor(
            "multi_contrib", "pattern", contrib
        )
    
    # Verify
    chain = provenance_mgr.load_provenance("multi_contrib", "pattern")
    assert len(chain.contributors) == 5
    
    # Verify percentages sum to 100
    total_pct = sum(c.contribution_pct for c in chain.contributors)
    assert total_pct == 100.0
    
    # Verify roles
    roles = {c.role for c in chain.contributors}
    assert ContributorRole.PRIMARY_AUTHOR in roles
    assert ContributorRole.REVIEWER in roles


def test_full_history_retrieval(provenance_mgr):
    """Test 8: Full history retrieval"""
    # Create complex provenance
    origin = create_origin(
        source_type=SourceType.EMPIRICAL_ANALYSIS,
        created_by="analyzer",
        dataset="test_dataset",
        confidence=0.9
    )
    
    chain = provenance_mgr.create_provenance(
        object_hash="history_test",
        object_type="grammar",
        origin=origin
    )
    
    # Add events
    events = [
        EventType.CREATED,
        EventType.REFINED,
        EventType.CERTIFIED
    ]
    
    for event_type in events:
        event = create_event(
            event_type=event_type,
            agent_identity="agent"
        )
        provenance_mgr.record_event("history_test", "grammar", event)
    
    # Add contributors
    contrib = create_contributor(
        contributor_id="contributor",
        role=ContributorRole.PRIMARY_AUTHOR,
        contributions=["all"]
    )
    provenance_mgr.add_contributor("history_test", "grammar", contrib)
    
    # Get full history
    history = provenance_mgr.get_full_history("history_test", "grammar")
    
    assert history['object_hash'] == "history_test"
    assert history['object_type'] == "grammar"
    assert history['origin']['created_by'] == "analyzer"
    assert history['event_count'] == 3
    assert history['contributor_count'] == 1
    assert 'created_at' in history
    assert 'last_modified' in history


def test_yaml_export_import(provenance_mgr, temp_store):
    """Test 9: YAML export/import"""
    # Create provenance
    origin = create_origin(
        source_type=SourceType.MANUAL_CREATION,
        created_by="exporter"
    )
    
    chain = provenance_mgr.create_provenance(
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
    provenance_mgr.record_event("yaml_test", "pattern", event)
    
    # Export to YAML
    yaml_path = temp_store / "exported.yml"
    provenance_mgr.export_to_yaml("yaml_test", "pattern", yaml_path)
    
    assert yaml_path.exists()
    
    # Verify YAML content
    with open(yaml_path) as f:
        content = f.read()
    
    assert "yaml_test" in content
    assert "exporter" in content
    assert "feature1" in content
    
    # Import from YAML
    imported = provenance_mgr.import_from_yaml(yaml_path)
    
    assert imported.object_hash == "yaml_test"
    assert imported.origin.created_by == "exporter"
    assert len(imported.evolution) == 1
    assert "feature1" in imported.evolution[0].capabilities_added


def test_index_updates(provenance_mgr):
    """Test 10: Index updates"""
    # Create provenance
    creator = "index_tester"
    origin = create_origin(
        source_type=SourceType.MANUAL_CREATION,
        created_by=creator
    )
    
    provenance_mgr.create_provenance(
        object_hash="index_obj",
        object_type="pattern",
        origin=origin
    )
    
    # Verify creator index
    creator_index = (
        provenance_mgr.provenance_path / 
        "by_creator" / 
        f"{creator}.json"
    )
    assert creator_index.exists()
    
    # Verify origin index
    origin_index = (
        provenance_mgr.provenance_path / 
        "by_origin" / 
        "manual_creation.json"
    )
    assert origin_index.exists()
    
    # Add event to trigger timeline index
    event = create_event(
        event_type=EventType.REFINED,
        agent_identity=creator
    )
    provenance_mgr.record_event("index_obj", "pattern", event)
    
    # Verify timeline index created
    timeline_files = list(
        (provenance_mgr.provenance_path / "timeline").glob("*.json")
    )
    assert len(timeline_files) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
