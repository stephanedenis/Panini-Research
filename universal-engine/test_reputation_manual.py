"""
Manual Test Suite for Reputation & Governance Manager
Comprehensive tests for all reputation, voting, and governance features
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Import the manager
from reputation_manager import (
    ReputationManager,
    ReputationLevel,
    VoteType,
    ProposalType,
    ProposalStatus,
    ConsensusModel,
    ActionType
)


def test_reputation_initialization():
    """Test 1: Initialize reputation for new user"""
    print("[TEST 1] Reputation Initialization")
    
    mgr = ReputationManager("store/test_reputation/test1")
    score = mgr.initialize_reputation("user1@test.com")
    
    assert score.user_id == "user1@test.com"
    assert score.total_score == 0
    assert score.level == ReputationLevel.NEWCOMER
    assert score.actions_count == 0
    
    print(f"  ✓ User initialized: {score.user_id}")
    print(f"  ✓ Initial score: {score.total_score}")
    print(f"  ✓ Level: {score.level.value}")


def test_reputation_scoring():
    """Test 2: Record actions and update scores"""
    print("\n[TEST 2] Reputation Scoring")
    
    mgr = ReputationManager("store/test_reputation/test2")
    
    # Positive actions
    score = mgr.record_action("user2@test.com", ActionType.CREATE_OBJECT)
    assert score.total_score == 10
    
    score = mgr.record_action("user2@test.com", ActionType.CONTRIBUTE)
    assert score.total_score == 15
    
    score = mgr.record_action("user2@test.com", ActionType.VALIDATE)
    assert score.total_score == 23
    
    # Negative action
    score = mgr.record_action("user2@test.com", ActionType.SPAM)
    assert score.total_score == 3  # 23 - 20
    
    print(f"  ✓ Actions recorded: {score.actions_count}")
    print(f"  ✓ Total score: {score.total_score}")
    print(f"  ✓ Positive actions: {score.positive_actions}")
    print(f"  ✓ Negative actions: {score.negative_actions}")


def test_reputation_levels():
    """Test 3: Reputation level progression"""
    print("\n[TEST 3] Reputation Level Progression")
    
    mgr = ReputationManager("store/test_reputation/test3")
    
    # NEWCOMER (0-99)
    score = mgr.record_action("user3@test.com", ActionType.CREATE_OBJECT)
    assert score.level == ReputationLevel.NEWCOMER
    
    # CONTRIBUTOR (100-499)
    for _ in range(10):
        score = mgr.record_action("user3@test.com", ActionType.CREATE_OBJECT)
    assert score.level == ReputationLevel.CONTRIBUTOR
    assert 100 <= score.total_score < 500
    
    # TRUSTED (500-999)
    for _ in range(50):
        score = mgr.record_action("user3@test.com", ActionType.CREATE_OBJECT)
    assert score.level == ReputationLevel.TRUSTED
    assert 500 <= score.total_score < 1000
    
    # EXPERT (1000-2499)
    for _ in range(60):
        score = mgr.record_action("user3@test.com", ActionType.CREATE_OBJECT)
    assert score.level == ReputationLevel.EXPERT
    assert 1000 <= score.total_score < 2500
    
    print(f"  ✓ Final level: {score.level.value}")
    print(f"  ✓ Final score: {score.total_score}")
    print(f"  ✓ Total actions: {score.actions_count}")


def test_quality_multiplier():
    """Test 4: Quality multiplier affects scoring"""
    print("\n[TEST 4] Quality Multiplier")
    
    mgr = ReputationManager("store/test_reputation/test4")
    
    # Standard quality (1.0x)
    score = mgr.record_action("user4@test.com", ActionType.CREATE_OBJECT, quality_multiplier=1.0)
    standard_score = score.total_score
    
    # High quality (2.0x)
    score = mgr.record_action("user4@test.com", ActionType.CREATE_OBJECT, quality_multiplier=2.0)
    high_quality_score = score.total_score - standard_score
    
    assert high_quality_score == 20  # 10 * 2.0
    assert score.quality_score > 0  # Quality bonus applied
    
    print(f"  ✓ Standard score: {standard_score}")
    print(f"  ✓ High quality score: {high_quality_score}")
    print(f"  ✓ Quality bonus: {score.quality_score}")


def test_badge_awards():
    """Test 5: Award badges to users"""
    print("\n[TEST 5] Badge Awards")
    
    mgr = ReputationManager("store/test_reputation/test5")
    
    score = mgr.award_badge("user5@test.com", "First Contribution", "Created first object")
    assert "First Contribution" in score.badges
    assert score.community_score == 10
    
    score = mgr.award_badge("user5@test.com", "Active Contributor", "10+ contributions")
    assert len(score.badges) == 2
    assert score.community_score == 20
    
    # Duplicate badge should not increase score again
    score = mgr.award_badge("user5@test.com", "First Contribution", "Duplicate")
    assert len(score.badges) == 2
    assert score.community_score == 20
    
    print(f"  ✓ Badges awarded: {len(score.badges)}")
    print(f"  ✓ Badge names: {', '.join(score.badges)}")
    print(f"  ✓ Community score: {score.community_score}")


def test_proposal_creation():
    """Test 6: Create governance proposals"""
    print("\n[TEST 6] Proposal Creation")
    
    mgr = ReputationManager("store/test_reputation/test6")
    
    proposal = mgr.create_proposal(
        proposer_id="proposer@test.com",
        proposal_type=ProposalType.POLICY_CHANGE,
        title="Update content validation rules",
        description="We should require peer review for all submissions",
        consensus_model=ConsensusModel.SUPERMAJORITY,
        voting_duration_days=7
    )
    
    assert proposal.proposal_id is not None
    assert proposal.status == ProposalStatus.ACTIVE
    assert proposal.proposal_type == ProposalType.POLICY_CHANGE
    assert proposal.approval_threshold == 0.66  # Supermajority
    
    print(f"  ✓ Proposal ID: {proposal.proposal_id}")
    print(f"  ✓ Status: {proposal.status.value}")
    print(f"  ✓ Consensus model: {proposal.consensus_model.value}")
    print(f"  ✓ Approval threshold: {proposal.approval_threshold}")


def test_voting_mechanism():
    """Test 7: Cast votes on proposals"""
    print("\n[TEST 7] Voting Mechanism")
    
    mgr = ReputationManager("store/test_reputation/test7")
    
    # Create proposal
    proposal = mgr.create_proposal(
        "proposer@test.com",
        ProposalType.CONTENT_VALIDATION,
        "Add quality standards",
        "Implement minimum quality threshold"
    )
    
    # Cast votes
    vote1 = mgr.cast_vote(proposal.proposal_id, "voter1@test.com", VoteType.APPROVE)
    vote2 = mgr.cast_vote(proposal.proposal_id, "voter2@test.com", VoteType.APPROVE)
    vote3 = mgr.cast_vote(proposal.proposal_id, "voter3@test.com", VoteType.REJECT)
    vote4 = mgr.cast_vote(proposal.proposal_id, "voter4@test.com", VoteType.ABSTAIN)
    
    # Verify votes were recorded
    updated_proposal = mgr.get_proposal(proposal.proposal_id)
    assert len(updated_proposal.votes) == 4
    assert updated_proposal.vote_counts["approve"] == 2
    assert updated_proposal.vote_counts["reject"] == 1
    assert updated_proposal.vote_counts["abstain"] == 1
    
    print(f"  ✓ Total votes: {len(updated_proposal.votes)}")
    print(f"  ✓ Approve: {updated_proposal.vote_counts['approve']}")
    print(f"  ✓ Reject: {updated_proposal.vote_counts['reject']}")
    print(f"  ✓ Abstain: {updated_proposal.vote_counts['abstain']}")


def test_weighted_voting():
    """Test 8: Weighted voting based on reputation"""
    print("\n[TEST 8] Weighted Voting")
    
    mgr = ReputationManager("store/test_reputation/test8")
    
    # Build reputation for voters
    for _ in range(100):
        mgr.record_action("expert@test.com", ActionType.CREATE_OBJECT)
    
    # Create proposal with weighted voting
    proposal = mgr.create_proposal(
        "proposer@test.com",
        ProposalType.POLICY_CHANGE,
        "Test weighted voting",
        "Description",
        consensus_model=ConsensusModel.WEIGHTED
    )
    
    # Expert vote (high reputation)
    expert_vote = mgr.cast_vote(proposal.proposal_id, "expert@test.com", VoteType.APPROVE)
    
    # Newcomer vote (low reputation)
    newcomer_vote = mgr.cast_vote(proposal.proposal_id, "newcomer@test.com", VoteType.APPROVE)
    
    # Expert should have higher weight
    assert expert_vote.weight > newcomer_vote.weight
    assert expert_vote.reputation_at_vote >= 1000  # Changed from > to >=
    assert newcomer_vote.reputation_at_vote == 0
    
    print(f"  ✓ Expert vote weight: {expert_vote.weight:.2f}")
    print(f"  ✓ Newcomer vote weight: {newcomer_vote.weight:.2f}")
    print(f"  ✓ Expert reputation: {expert_vote.reputation_at_vote}")


def test_proposal_finalization():
    """Test 9: Finalize proposals after voting"""
    print("\n[TEST 9] Proposal Finalization")
    
    mgr = ReputationManager("store/test_reputation/test9")
    
    # Create proposal with short duration (for testing)
    proposal = mgr.create_proposal(
        "proposer@test.com",
        ProposalType.POLICY_CHANGE,
        "Test proposal",
        "Description",
        voting_duration_days=0  # Expires immediately
    )
    
    # Cast votes (majority approve)
    for i in range(15):
        vote_type = VoteType.APPROVE if i < 10 else VoteType.REJECT
        mgr.cast_vote(proposal.proposal_id, f"voter{i}@test.com", vote_type)
    
    # Finalize proposal
    finalized = mgr.finalize_proposal(proposal.proposal_id)
    
    assert finalized.status == ProposalStatus.APPROVED
    assert finalized.approved == True
    
    print(f"  ✓ Status: {finalized.status.value}")
    print(f"  ✓ Approved: {finalized.approved}")
    print(f"  ✓ Votes: {len(finalized.votes)}")


def test_consensus_models():
    """Test 10: Different consensus models"""
    print("\n[TEST 10] Consensus Models")
    
    mgr = ReputationManager("store/test_reputation/test10")
    
    # Simple majority (>50%)
    p1 = mgr.create_proposal(
        "proposer@test.com",
        ProposalType.POLICY_CHANGE,
        "Simple majority test",
        "Description",
        consensus_model=ConsensusModel.SIMPLE_MAJORITY,
        voting_duration_days=0
    )
    for i in range(10):
        mgr.cast_vote(p1.proposal_id, f"v{i}@test.com", VoteType.APPROVE if i < 6 else VoteType.REJECT)
    f1 = mgr.finalize_proposal(p1.proposal_id)
    assert f1.approved == True  # 60% > 50%
    
    # Supermajority (>66%)
    p2 = mgr.create_proposal(
        "proposer@test.com",
        ProposalType.POLICY_CHANGE,
        "Supermajority test",
        "Description",
        consensus_model=ConsensusModel.SUPERMAJORITY,
        voting_duration_days=0
    )
    for i in range(10):
        mgr.cast_vote(p2.proposal_id, f"x{i}@test.com", VoteType.APPROVE if i < 6 else VoteType.REJECT)
    f2 = mgr.finalize_proposal(p2.proposal_id)
    assert f2.approved == False  # 60% < 66%
    
    print(f"  ✓ Simple majority (60%): {f1.status.value}")
    print(f"  ✓ Supermajority (60%): {f2.status.value}")


def test_governance_policies():
    """Test 11: Create and manage governance policies"""
    print("\n[TEST 11] Governance Policies")
    
    mgr = ReputationManager("store/test_reputation/test11")
    
    # Create proposal
    proposal = mgr.create_proposal(
        "proposer@test.com",
        ProposalType.POLICY_CHANGE,
        "Create moderation policy",
        "Establish content moderation guidelines"
    )
    
    # Create policy
    rules = [
        {"type": "content_validation", "threshold": 0.8},
        {"type": "peer_review_required", "min_reviewers": 2}
    ]
    
    policy = mgr.create_policy(
        name="Content Moderation Policy",
        description="Guidelines for content validation and moderation",
        rules=rules,
        created_by="admin@test.com",
        proposal_id=proposal.proposal_id
    )
    
    assert policy.policy_id is not None
    assert policy.active == True
    assert len(policy.rules) == 2
    assert policy.approved_by_proposal == proposal.proposal_id
    
    print(f"  ✓ Policy ID: {policy.policy_id}")
    print(f"  ✓ Active: {policy.active}")
    print(f"  ✓ Rules: {len(policy.rules)}")


def test_trust_metrics():
    """Test 12: Calculate trust metrics"""
    print("\n[TEST 12] Trust Metrics")
    
    mgr = ReputationManager("store/test_reputation/test12")
    
    # Build reputation
    for _ in range(50):
        mgr.record_action("trusted_user@test.com", ActionType.CREATE_OBJECT, quality_multiplier=1.5)
    
    # Calculate trust
    trust = mgr.calculate_trust("trusted_user@test.com", "user")
    
    assert 0.0 <= trust.overall_trust <= 1.0
    assert 0.0 <= trust.authenticity <= 1.0
    assert 0.0 <= trust.reliability <= 1.0
    assert 0.0 <= trust.competence <= 1.0
    assert 0.0 <= trust.benevolence <= 1.0
    assert trust.competence > 0.1  # Should have some competence with 50 actions
    
    print(f"  ✓ Overall trust: {trust.overall_trust:.3f}")
    print(f"  ✓ Authenticity: {trust.authenticity:.3f}")
    print(f"  ✓ Reliability: {trust.reliability:.3f}")
    print(f"  ✓ Competence: {trust.competence:.3f}")
    print(f"  ✓ Benevolence: {trust.benevolence:.3f}")


def test_vote_delegation():
    """Test 13: Vote delegation"""
    print("\n[TEST 13] Vote Delegation")
    
    mgr = ReputationManager("store/test_reputation/test13")
    
    # Create proposal
    proposal = mgr.create_proposal(
        "proposer@test.com",
        ProposalType.POLICY_CHANGE,
        "Test delegation",
        "Description"
    )
    
    # Delegate vote
    delegated_vote = mgr.delegate_vote(
        proposal.proposal_id,
        "delegator@test.com",
        "delegate@test.com"
    )
    
    assert delegated_vote.vote_type == VoteType.DELEGATE
    assert delegated_vote.delegated_to == "delegate@test.com"
    
    print(f"  ✓ Vote delegated from: {delegated_vote.voter_id}")
    print(f"  ✓ Vote delegated to: {delegated_vote.delegated_to}")
    print(f"  ✓ Vote type: {delegated_vote.vote_type.value}")


def test_active_proposals():
    """Test 14: Retrieve active proposals"""
    print("\n[TEST 14] Active Proposals")
    
    mgr = ReputationManager("store/test_reputation/test14")
    
    # Create multiple proposals
    p1 = mgr.create_proposal("u1@test.com", ProposalType.POLICY_CHANGE, "P1", "D1")
    p2 = mgr.create_proposal("u2@test.com", ProposalType.CONTENT_VALIDATION, "P2", "D2")
    p3 = mgr.create_proposal("u3@test.com", ProposalType.USER_MODERATION, "P3", "D3")
    
    # Get active proposals
    active = mgr.get_active_proposals()
    
    assert len(active) == 3
    assert all(p.status == ProposalStatus.ACTIVE for p in active)
    
    print(f"  ✓ Active proposals: {len(active)}")
    print(f"  ✓ Proposal types: {[p.proposal_type.value for p in active]}")


def test_full_governance_workflow():
    """Test 15: Complete governance workflow"""
    print("\n[TEST 15] Complete Governance Workflow")
    
    mgr = ReputationManager("store/test_reputation/test15")
    
    # 1. Create proposal
    proposal = mgr.create_proposal(
        "creator@test.com",
        ProposalType.POLICY_CHANGE,
        "Implement peer review system",
        "All submissions require 2 peer reviews",
        voting_duration_days=0
    )
    assert proposal.status == ProposalStatus.ACTIVE
    
    # 2. Community votes
    for i in range(15):
        vote_type = VoteType.APPROVE if i < 12 else VoteType.REJECT
        mgr.cast_vote(proposal.proposal_id, f"voter{i}@test.com", vote_type)
    
    # 3. Finalize proposal
    finalized = mgr.finalize_proposal(proposal.proposal_id)
    assert finalized.approved == True
    
    # 4. Implement proposal
    implemented = mgr.implement_proposal(proposal.proposal_id)
    assert implemented.status == ProposalStatus.IMPLEMENTED
    assert implemented.implemented == True
    assert implemented.implementation_date is not None
    
    # 5. Create policy based on proposal
    policy = mgr.create_policy(
        name="Peer Review Policy",
        description="All submissions require peer review",
        rules=[{"min_reviews": 2, "reviewer_level": "trusted"}],
        created_by="admin@test.com",
        proposal_id=proposal.proposal_id
    )
    assert policy.active == True
    
    print(f"  ✓ Proposal created: {proposal.proposal_id}")
    print(f"  ✓ Votes cast: {len(finalized.votes)}")
    print(f"  ✓ Proposal approved: {finalized.approved}")
    print(f"  ✓ Proposal implemented: {implemented.implemented}")
    print(f"  ✓ Policy created: {policy.policy_id}")


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all tests and report results"""
    print("=" * 70)
    print(" REPUTATION & GOVERNANCE MANAGER - MANUAL TEST SUITE")
    print("=" * 70)
    
    tests = [
        test_reputation_initialization,
        test_reputation_scoring,
        test_reputation_levels,
        test_quality_multiplier,
        test_badge_awards,
        test_proposal_creation,
        test_voting_mechanism,
        test_weighted_voting,
        test_proposal_finalization,
        test_consensus_models,
        test_governance_policies,
        test_trust_metrics,
        test_vote_delegation,
        test_active_proposals,
        test_full_governance_workflow
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(" TEST RESULTS")
    print("=" * 70)
    print(f"  Total: {len(tests)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print()
    
    if failed == 0:
        print("  ✅ ALL TESTS PASSED")
    else:
        print(f"  ❌ {failed} TEST(S) FAILED")
    
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
