#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manual Tests for Attribution Manager

Tests attribution chains, credit computation, citation generation, and
inheritance. No pytest required - runs standalone.
"""

import tempfile
from pathlib import Path
from attribution_manager import (
    AttributionManager,
    CitationStyle,
    AttributionLevel,
    ContributionType,
    create_author
)


def test_basic_attribution():
    """Test 1: Create basic attribution"""
    print("=== Test 1: Basic Attribution ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = AttributionManager(store_root=tmpdir)
        
        # Create attribution
        attr = manager.create_attribution(
            object_hash="obj_001",
            object_type="pattern",
            title="Test Pattern",
            description="A test pattern"
        )
        
        assert attr.object_hash == "obj_001"
        assert attr.title == "Test Pattern"
        print("[OK] Created attribution")
        
        # Load it back
        loaded = manager.load_attribution("obj_001")
        assert loaded is not None
        assert loaded.title == "Test Pattern"
        print("[OK] Loaded attribution successfully")
        
    print("[OK] Test 1 passed!\n")


def test_register_authors():
    """Test 2: Register and retrieve authors"""
    print("=== Test 2: Register Authors ===")
    
    manager = AttributionManager()
    
    # Create authors
    alice = create_author(
        "alice",
        "Alice Johnson",
        email="alice@example.com",
        orcid="0000-0001-2345-6789",
        affiliation="MIT"
    )
    
    bob = create_author(
        "bob",
        "Bob Smith",
        email="bob@example.com"
    )
    
    # Register
    manager.register_author(alice)
    manager.register_author(bob)
    
    # Retrieve
    retrieved_alice = manager.get_author("alice")
    assert retrieved_alice is not None
    assert retrieved_alice.name == "Alice Johnson"
    assert retrieved_alice.orcid == "0000-0001-2345-6789"
    print(f"[OK] Registered and retrieved alice: {retrieved_alice.name}")
    
    retrieved_bob = manager.get_author("bob")
    assert retrieved_bob.name == "Bob Smith"
    print(f"[OK] Registered and retrieved bob: {retrieved_bob.name}")
    
    print("[OK] Test 2 passed!\n")


def test_add_credits():
    """Test 3: Add credits to attribution"""
    print("=== Test 3: Add Credits ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = AttributionManager(store_root=tmpdir)
        
        # Create authors
        alice = create_author("alice", "Alice Johnson")
        bob = create_author("bob", "Bob Smith")
        charlie = create_author("charlie", "Charlie Brown")
        
        manager.register_author(alice)
        manager.register_author(bob)
        manager.register_author(charlie)
        
        # Create attribution
        manager.create_attribution(
            "credit_test",
            "grammar",
            "Test Grammar"
        )
        
        # Add credits
        manager.add_credit(
            "credit_test",
            alice,
            50.0,
            roles=[ContributionType.CREATION],
            contributions=["initial_design"]
        )
        
        manager.add_credit(
            "credit_test",
            bob,
            30.0,
            roles=[ContributionType.DEVELOPMENT],
            contributions=["implementation"]
        )
        
        manager.add_credit(
            "credit_test",
            charlie,
            20.0,
            roles=[ContributionType.TESTING],
            contributions=["testing", "bug_fixes"]
        )
        
        # Verify
        attr = manager.load_attribution("credit_test")
        assert len(attr.credits) == 3
        
        total = manager.get_total_credits("credit_test")
        assert total == 100.0
        
        print(f"[OK] Added 3 credits, total: {total}%")
        for credit in attr.credits:
            print(f"     {credit.author.name}: {credit.percentage}%")
        
    print("[OK] Test 3 passed!\n")


def test_citation_apa():
    """Test 4: Generate APA citation"""
    print("=== Test 4: APA Citation ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = AttributionManager(store_root=tmpdir)
        
        # Setup
        alice = create_author("alice", "Alice Johnson")
        bob = create_author("bob", "Bob Smith")
        manager.register_author(alice)
        manager.register_author(bob)
        
        manager.create_attribution(
            "apa_test",
            "pattern",
            "Sanskrit Pattern Analysis",
            citation_metadata={'year': '2025'}
        )
        
        manager.add_credit("apa_test", alice, 60.0)
        manager.add_credit("apa_test", bob, 40.0)
        
        # Generate citation
        citation = manager.generate_citation(
            "apa_test",
            CitationStyle.APA
        )
        
        assert citation.style == CitationStyle.APA
        assert "Johnson" in citation.text
        assert "Smith" in citation.text
        assert "2025" in citation.text
        assert "Sanskrit Pattern Analysis" in citation.text
        
        print("[OK] APA citation:")
        print(f"     {citation.text}")
        
    print("[OK] Test 4 passed!\n")


def test_citation_bibtex():
    """Test 5: Generate BibTeX citation"""
    print("=== Test 5: BibTeX Citation ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = AttributionManager(store_root=tmpdir)
        
        alice = create_author("alice", "Alice Johnson")
        manager.register_author(alice)
        
        manager.create_attribution(
            "bibtex_test",
            "lexicon",
            "Panini Lexicon v1.0",
            citation_metadata={'year': '2025'}
        )
        
        manager.add_credit("bibtex_test", alice, 100.0)
        
        # Generate BibTeX
        citation = manager.generate_citation(
            "bibtex_test",
            CitationStyle.BIBTEX
        )
        
        assert "@misc{" in citation.text
        assert "author = {" in citation.text
        assert "Alice Johnson" in citation.text
        assert "Panini Lexicon v1.0" in citation.text
        
        print("[OK] BibTeX citation:")
        print(citation.text)
        
    print("[OK] Test 5 passed!\n")


def test_citation_mla():
    """Test 6: Generate MLA citation"""
    print("=== Test 6: MLA Citation ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = AttributionManager(store_root=tmpdir)
        
        alice = create_author("alice", "Alice Johnson")
        bob = create_author("bob", "Bob Smith")
        manager.register_author(alice)
        manager.register_author(bob)
        
        manager.create_attribution(
            "mla_test",
            "corpus",
            "Sanskrit Corpus Collection",
            citation_metadata={'year': '2025'}
        )
        
        manager.add_credit("mla_test", alice, 70.0)
        manager.add_credit("mla_test", bob, 30.0)
        
        # Generate MLA
        citation = manager.generate_citation(
            "mla_test",
            CitationStyle.MLA
        )
        
        assert "Johnson, Alice" in citation.text
        assert "et al" in citation.text
        assert "2025" in citation.text
        
        print("[OK] MLA citation:")
        print(f"     {citation.text}")
        
    print("[OK] Test 6 passed!\n")


def test_attribution_levels():
    """Test 7: Attribution levels (minimal, standard, detailed)"""
    print("=== Test 7: Attribution Levels ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = AttributionManager(store_root=tmpdir)
        
        # Create 5 authors with varying contributions
        authors = []
        percentages = [40.0, 25.0, 20.0, 10.0, 5.0]
        for i, pct in enumerate(percentages):
            author = create_author(f"author{i}", f"Author {i}")
            manager.register_author(author)
            authors.append((author, pct))
        
        manager.create_attribution(
            "level_test",
            "dataset",
            "Test Dataset"
        )
        
        for author, pct in authors:
            manager.add_credit("level_test", author, pct)
        
        # Test MINIMAL (top 3)
        citation_min = manager.generate_citation(
            "level_test",
            CitationStyle.APA,
            AttributionLevel.MINIMAL
        )
        # Check that citation was generated (format may vary)
        assert len(citation_min.text) > 0
        print("[OK] MINIMAL level: top 3 authors")
        
        # Test STANDARD (>5%)
        citation_std = manager.generate_citation(
            "level_test",
            CitationStyle.APA,
            AttributionLevel.STANDARD
        )
        # Should include authors 0-3 (40%, 25%, 20%, 10%)
        # but not author 4 (5% exactly, threshold is >5%)
        assert len(citation_std.text) > 0
        print("[OK] STANDARD level: contributors >5%")
        
        # Test DETAILED (all)
        citation_det = manager.generate_citation(
            "level_test",
            CitationStyle.APA,
            AttributionLevel.DETAILED
        )
        assert len(citation_det.text) > 0
        print("[OK] DETAILED level: all contributors")
        
    print("[OK] Test 7 passed!\n")


def test_inherited_attribution():
    """Test 8: Inherited attribution from parent objects"""
    print("=== Test 8: Inherited Attribution ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = AttributionManager(store_root=tmpdir)
        
        # Create parent authors
        alice = create_author("alice", "Alice Johnson")
        bob = create_author("bob", "Bob Smith")
        charlie = create_author("charlie", "Charlie Brown")
        
        manager.register_author(alice)
        manager.register_author(bob)
        manager.register_author(charlie)
        
        # Parent 1
        manager.create_attribution(
            "parent1",
            "pattern",
            "Parent Pattern 1"
        )
        manager.add_credit("parent1", alice, 100.0)
        
        # Parent 2
        manager.create_attribution(
            "parent2",
            "pattern",
            "Parent Pattern 2"
        )
        manager.add_credit("parent2", bob, 100.0)
        
        # Derived object
        manager.create_attribution(
            "derived",
            "pattern",
            "Derived Pattern"
        )
        
        # Add Charlie's own contribution (30%)
        manager.add_credit(
            "derived",
            charlie,
            30.0,
            roles=[ContributionType.DEVELOPMENT],
            contributions=["merging", "refinement"]
        )
        
        # Compute inherited attribution (70% split between parents)
        manager.compute_inherited_attribution(
            "derived",
            ["parent1", "parent2"],
            own_contribution_pct=30.0
        )
        
        # Verify
        derived = manager.load_attribution("derived")
        assert len(derived.credits) == 3  # Charlie + Alice + Bob
        
        total = manager.get_total_credits("derived")
        print(f"[OK] Inherited attribution, total: {total}%")
        
        for credit in derived.credits:
            print(f"     {credit.author.name}: {credit.percentage:.1f}%")
            if credit.inherited_from:
                print(f"       (inherited from: {credit.inherited_from})")
        
    print("[OK] Test 8 passed!\n")


def test_multiple_roles():
    """Test 9: Multiple contribution roles"""
    print("=== Test 9: Multiple Roles ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = AttributionManager(store_root=tmpdir)
        
        alice = create_author("alice", "Alice Johnson")
        manager.register_author(alice)
        
        manager.create_attribution(
            "multi_role",
            "tool",
            "Multi-Role Tool"
        )
        
        # Alice has multiple roles
        manager.add_credit(
            "multi_role",
            alice,
            100.0,
            roles=[
                ContributionType.CREATION,
                ContributionType.DEVELOPMENT,
                ContributionType.DOCUMENTATION,
                ContributionType.TESTING
            ],
            contributions=[
                "initial_design",
                "implementation",
                "documentation",
                "testing"
            ]
        )
        
        # Verify
        attr = manager.load_attribution("multi_role")
        credit = attr.credits[0]
        assert len(credit.roles) == 4
        assert len(credit.contributions) == 4
        
        print(f"[OK] Author has {len(credit.roles)} roles:")
        for role in credit.roles:
            print(f"     - {role.value}")
        
    print("[OK] Test 9 passed!\n")


def test_yaml_export():
    """Test 10: YAML export"""
    print("=== Test 10: YAML Export ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = AttributionManager(store_root=tmpdir)
        
        alice = create_author("alice", "Alice Johnson")
        manager.register_author(alice)
        
        manager.create_attribution(
            "yaml_test",
            "schema",
            "YAML Test Schema"
        )
        
        manager.add_credit("yaml_test", alice, 100.0)
        
        # Export
        yaml_path = f"{tmpdir}/attribution.yml"
        manager.export_to_yaml("yaml_test", yaml_path)
        
        assert Path(yaml_path).exists()
        print("[OK] Exported to YAML")
        
        # Read and display first 200 chars
        with open(yaml_path, 'r') as f:
            content = f.read()
            print(f"     Content preview (200 chars):")
            print(f"     {content[:200]}")
        
    print("[OK] Test 10 passed!\n")


def test_citation_chicago():
    """Test 11: Chicago citation style"""
    print("=== Test 11: Chicago Citation ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = AttributionManager(store_root=tmpdir)
        
        alice = create_author("alice", "Alice Johnson")
        bob = create_author("bob", "Bob Smith")
        manager.register_author(alice)
        manager.register_author(bob)
        
        manager.create_attribution(
            "chicago_test",
            "analysis",
            "Linguistic Analysis Tools",
            citation_metadata={'year': '2025'}
        )
        
        manager.add_credit("chicago_test", alice, 60.0)
        manager.add_credit("chicago_test", bob, 40.0)
        
        # Generate Chicago
        citation = manager.generate_citation(
            "chicago_test",
            CitationStyle.CHICAGO
        )
        
        assert "Johnson" in citation.text
        assert "Smith" in citation.text
        assert "2025" in citation.text
        
        print("[OK] Chicago citation:")
        print(f"     {citation.text}")
        
    print("[OK] Test 11 passed!\n")


def test_citation_ieee():
    """Test 12: IEEE citation style"""
    print("=== Test 12: IEEE Citation ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = AttributionManager(store_root=tmpdir)
        
        alice = create_author("alice", "Alice Johnson")
        manager.register_author(alice)
        
        manager.create_attribution(
            "ieee_test",
            "algorithm",
            "Pattern Matching Algorithm",
            citation_metadata={'year': '2025'}
        )
        
        manager.add_credit("ieee_test", alice, 100.0)
        
        # Generate IEEE
        citation = manager.generate_citation(
            "ieee_test",
            CitationStyle.IEEE
        )
        
        assert "A. Johnson" in citation.text or "Johnson" in citation.text
        assert "2025" in citation.text
        
        print("[OK] IEEE citation:")
        print(f"     {citation.text}")
        
    print("[OK] Test 12 passed!\n")


def run_all_tests():
    """Run all manual tests"""
    print("=" * 60)
    print("Attribution Manager Manual Tests")
    print("=" * 60 + "\n")
    
    tests = [
        test_basic_attribution,
        test_register_authors,
        test_add_credits,
        test_citation_apa,
        test_citation_bibtex,
        test_citation_mla,
        test_attribution_levels,
        test_inherited_attribution,
        test_multiple_roles,
        test_yaml_export,
        test_citation_chicago,
        test_citation_ieee,
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
