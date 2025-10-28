"""
Reputation & Governance Manager for CAS IP System
Phase 7: Community-driven reputation scoring and governance mechanisms

Features:
- Reputation scoring based on contributions and behavior
- Voting mechanisms for community decisions
- Consensus algorithms for validation
- Governance policies and rule enforcement
- Trust metrics and quality assessment
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict, field
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class ReputationLevel(Enum):
    """Reputation tiers based on score"""
    UNKNOWN = "unknown"
    NEWCOMER = "newcomer"        # 0-99
    CONTRIBUTOR = "contributor"  # 100-499
    TRUSTED = "trusted"          # 500-999
    EXPERT = "expert"            # 1000-2499
    AUTHORITY = "authority"      # 2500+


class VoteType(Enum):
    """Types of votes in the system"""
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"
    DELEGATE = "delegate"


class ProposalType(Enum):
    """Types of governance proposals"""
    POLICY_CHANGE = "policy_change"
    USER_MODERATION = "user_moderation"
    CONTENT_VALIDATION = "content_validation"
    RESOURCE_ALLOCATION = "resource_allocation"
    SYSTEM_UPGRADE = "system_upgrade"


class ProposalStatus(Enum):
    """Status of governance proposals"""
    DRAFT = "draft"
    ACTIVE = "active"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    IMPLEMENTED = "implemented"


class ConsensusModel(Enum):
    """Consensus algorithms"""
    SIMPLE_MAJORITY = "simple_majority"      # >50%
    SUPERMAJORITY = "supermajority"          # >66%
    UNANIMOUS = "unanimous"                   # 100%
    WEIGHTED = "weighted"                     # Reputation-weighted
    QUADRATIC = "quadratic"                   # Quadratic voting


class ActionType(Enum):
    """Actions that affect reputation"""
    # Positive actions
    CREATE_OBJECT = "create_object"
    CONTRIBUTE = "contribute"
    REVIEW = "review"
    VALIDATE = "validate"
    MENTOR = "mentor"
    
    # Negative actions
    SPAM = "spam"
    PLAGIARISM = "plagiarism"
    VIOLATION = "violation"
    ABUSE = "abuse"
    
    # Neutral actions
    VOTE = "vote"
    COMMENT = "comment"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ReputationScore:
    """User reputation score with breakdown"""
    user_id: str
    total_score: int
    level: ReputationLevel
    
    # Score components
    contribution_score: int = 0
    quality_score: int = 0
    consistency_score: int = 0
    community_score: int = 0
    
    # Statistics
    actions_count: int = 0
    positive_actions: int = 0
    negative_actions: int = 0
    
    # Time-based
    first_action: Optional[str] = None
    last_action: Optional[str] = None
    active_days: int = 0
    
    # Metadata
    badges: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['level'] = self.level.value
        return data


@dataclass
class Vote:
    """A vote cast by a user"""
    vote_id: str
    proposal_id: str
    voter_id: str
    vote_type: VoteType
    
    # Voting power
    weight: float = 1.0
    reputation_at_vote: int = 0
    
    # Delegation
    delegated_to: Optional[str] = None
    delegated_from: List[str] = field(default_factory=list)
    
    # Rationale
    comment: Optional[str] = None
    reasoning: Optional[str] = None
    
    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    signature: Optional[str] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['vote_type'] = self.vote_type.value
        return data


@dataclass
class Proposal:
    """A governance proposal"""
    proposal_id: str
    proposer_id: str
    proposal_type: ProposalType
    title: str
    description: str
    
    # Status
    status: ProposalStatus
    
    # Voting configuration
    consensus_model: ConsensusModel
    approval_threshold: float  # 0.0 to 1.0
    quorum_required: int  # Minimum number of votes
    
    # Timing
    created_at: str
    voting_start: str
    voting_end: str
    
    # Votes
    votes: List[str] = field(default_factory=list)  # Vote IDs
    vote_counts: Dict[str, int] = field(default_factory=lambda: {
        "approve": 0, "reject": 0, "abstain": 0
    })
    
    # Results
    approved: Optional[bool] = None
    implemented: bool = False
    implementation_date: Optional[str] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    discussion_url: Optional[str] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['proposal_type'] = self.proposal_type.value
        data['status'] = self.status.value
        data['consensus_model'] = self.consensus_model.value
        return data


@dataclass
class GovernancePolicy:
    """A governance policy or rule"""
    policy_id: str
    name: str
    description: str
    
    # Policy content
    rules: List[Dict[str, Any]]
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    
    # Status
    active: bool = True
    version: int = 1
    
    # History
    created_by: str = ""
    approved_by_proposal: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    related_policies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TrustMetric:
    """Trust assessment for a user or object"""
    metric_id: str
    subject_id: str  # User or object ID
    subject_type: str  # "user" or "object"
    
    # Trust scores (0.0 to 1.0)
    overall_trust: float
    authenticity: float  # Is it genuine?
    reliability: float    # Is it consistent?
    competence: float     # Is it high quality?
    benevolence: float    # Is it helpful?
    
    # Evidence
    endorsements: List[str] = field(default_factory=list)
    validations: List[str] = field(default_factory=list)
    reports: List[str] = field(default_factory=list)
    
    # Calculations
    sample_size: int = 0
    confidence: float = 0.0  # Statistical confidence
    
    # Metadata
    calculated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    valid_until: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# REPUTATION MANAGER
# ============================================================================

class ReputationManager:
    """
    Manages reputation scoring, voting, consensus, and governance
    """
    
    def __init__(self, store_path: str = "store/reputation"):
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        # Subdirectories
        self.scores_dir = self.store_path / "scores"
        self.votes_dir = self.store_path / "votes"
        self.proposals_dir = self.store_path / "proposals"
        self.policies_dir = self.store_path / "policies"
        self.trust_dir = self.store_path / "trust"
        
        for dir_path in [self.scores_dir, self.votes_dir, self.proposals_dir,
                        self.policies_dir, self.trust_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.reputation_config = {
            "levels": {
                ReputationLevel.NEWCOMER: (0, 99),
                ReputationLevel.CONTRIBUTOR: (100, 499),
                ReputationLevel.TRUSTED: (500, 999),
                ReputationLevel.EXPERT: (1000, 2499),
                ReputationLevel.AUTHORITY: (2500, float('inf'))
            },
            "action_points": {
                ActionType.CREATE_OBJECT: 10,
                ActionType.CONTRIBUTE: 5,
                ActionType.REVIEW: 3,
                ActionType.VALIDATE: 8,
                ActionType.MENTOR: 15,
                ActionType.SPAM: -20,
                ActionType.PLAGIARISM: -50,
                ActionType.VIOLATION: -30,
                ActionType.ABUSE: -100,
                ActionType.VOTE: 1,
                ActionType.COMMENT: 1
            },
            "decay_rate": 0.95,  # Score decay per month of inactivity
            "quality_bonus": 2.0,  # Multiplier for high-quality contributions
            "consistency_bonus": 1.5  # Multiplier for consistent activity
        }
    
    # ========================================================================
    # REPUTATION SCORING
    # ========================================================================
    
    def get_reputation(self, user_id: str) -> Optional[ReputationScore]:
        """Get user's reputation score"""
        score_file = self.scores_dir / f"{user_id}.json"
        if not score_file.exists():
            return None
        
        with open(score_file, 'r') as f:
            data = json.load(f)
        
        data['level'] = ReputationLevel(data['level'])
        return ReputationScore(**data)
    
    def initialize_reputation(self, user_id: str) -> ReputationScore:
        """Initialize reputation for a new user"""
        score = ReputationScore(
            user_id=user_id,
            total_score=0,
            level=ReputationLevel.NEWCOMER,
            first_action=datetime.utcnow().isoformat()
        )
        
        self._save_reputation(score)
        return score
    
    def record_action(self, user_id: str, action_type: ActionType,
                     quality_multiplier: float = 1.0,
                     metadata: Optional[Dict] = None) -> ReputationScore:
        """Record an action and update reputation"""
        # Get or initialize reputation
        score = self.get_reputation(user_id)
        if score is None:
            score = self.initialize_reputation(user_id)
        
        # Calculate points
        base_points = self.reputation_config["action_points"].get(action_type, 0)
        points = int(base_points * quality_multiplier)
        
        # Update scores
        score.total_score = max(0, score.total_score + points)
        score.actions_count += 1
        
        if points > 0:
            score.positive_actions += 1
            score.contribution_score += points
        elif points < 0:
            score.negative_actions += 1
        
        # Update activity
        score.last_action = datetime.utcnow().isoformat()
        
        # Calculate active days
        if score.first_action:
            first = datetime.fromisoformat(score.first_action)
            now = datetime.utcnow()
            score.active_days = (now - first).days
        
        # Update level
        score.level = self._calculate_level(score.total_score)
        
        # Apply quality bonus
        if quality_multiplier > 1.5:
            score.quality_score += int((quality_multiplier - 1.0) * 10)
        
        # Check for consistency bonus
        if score.actions_count > 10 and score.active_days > 0:
            consistency = score.actions_count / max(1, score.active_days)
            if consistency > 0.5:  # More than one action every 2 days
                score.consistency_score += 5
        
        score.updated_at = datetime.utcnow().isoformat()
        self._save_reputation(score)
        
        return score
    
    def apply_decay(self, user_id: str) -> ReputationScore:
        """Apply time-based decay to reputation"""
        score = self.get_reputation(user_id)
        if not score or not score.last_action:
            return score
        
        last = datetime.fromisoformat(score.last_action)
        now = datetime.utcnow()
        months_inactive = (now - last).days / 30.0
        
        if months_inactive > 1:
            decay_factor = self.reputation_config["decay_rate"] ** months_inactive
            score.total_score = int(score.total_score * decay_factor)
            score.level = self._calculate_level(score.total_score)
            score.updated_at = datetime.utcnow().isoformat()
            self._save_reputation(score)
        
        return score
    
    def award_badge(self, user_id: str, badge: str, reason: str = "") -> ReputationScore:
        """Award a badge to a user"""
        score = self.get_reputation(user_id)
        if not score:
            score = self.initialize_reputation(user_id)
        
        if badge not in score.badges:
            score.badges.append(badge)
            score.community_score += 10
            score.updated_at = datetime.utcnow().isoformat()
            self._save_reputation(score)
        
        return score
    
    def _calculate_level(self, total_score: int) -> ReputationLevel:
        """Calculate reputation level from score"""
        for level, (min_score, max_score) in self.reputation_config["levels"].items():
            if min_score <= total_score <= max_score:
                return level
        return ReputationLevel.UNKNOWN
    
    def _save_reputation(self, score: ReputationScore):
        """Save reputation to disk"""
        score_file = self.scores_dir / f"{score.user_id}.json"
        with open(score_file, 'w') as f:
            json.dump(score.to_dict(), f, indent=2)
    
    # ========================================================================
    # VOTING MECHANISMS
    # ========================================================================
    
    def cast_vote(self, proposal_id: str, voter_id: str, vote_type: VoteType,
                 comment: Optional[str] = None) -> Vote:
        """Cast a vote on a proposal"""
        # Generate vote ID
        vote_id = hashlib.sha256(
            f"{proposal_id}:{voter_id}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Get voter's reputation for weighting
        reputation = self.get_reputation(voter_id)
        reputation_score = reputation.total_score if reputation else 0
        
        # Calculate vote weight (based on reputation for weighted voting)
        weight = 1.0
        if reputation:
            weight = min(5.0, 1.0 + (reputation_score / 1000.0))
        
        # Create vote
        vote = Vote(
            vote_id=vote_id,
            proposal_id=proposal_id,
            voter_id=voter_id,
            vote_type=vote_type,
            weight=weight,
            reputation_at_vote=reputation_score,
            comment=comment
        )
        
        # Save vote
        self._save_vote(vote)
        
        # Update proposal
        self._update_proposal_votes(proposal_id, vote)
        
        # Award reputation for voting
        self.record_action(voter_id, ActionType.VOTE, quality_multiplier=1.0)
        
        return vote
    
    def delegate_vote(self, proposal_id: str, delegator_id: str,
                     delegate_id: str) -> Vote:
        """Delegate voting power to another user"""
        vote = self.cast_vote(proposal_id, delegator_id, VoteType.DELEGATE)
        vote.delegated_to = delegate_id
        self._save_vote(vote)
        
        return vote
    
    def get_vote(self, vote_id: str) -> Optional[Vote]:
        """Retrieve a specific vote"""
        vote_file = self.votes_dir / f"{vote_id}.json"
        if not vote_file.exists():
            return None
        
        with open(vote_file, 'r') as f:
            data = json.load(f)
        
        data['vote_type'] = VoteType(data['vote_type'])
        return Vote(**data)
    
    def get_user_votes(self, user_id: str) -> List[Vote]:
        """Get all votes by a user"""
        votes = []
        for vote_file in self.votes_dir.glob("*.json"):
            with open(vote_file, 'r') as f:
                data = json.load(f)
            if data.get('voter_id') == user_id:
                data['vote_type'] = VoteType(data['vote_type'])
                votes.append(Vote(**data))
        return votes
    
    def _save_vote(self, vote: Vote):
        """Save vote to disk"""
        vote_file = self.votes_dir / f"{vote.vote_id}.json"
        with open(vote_file, 'w') as f:
            json.dump(vote.to_dict(), f, indent=2)
    
    def _update_proposal_votes(self, proposal_id: str, vote: Vote):
        """Update proposal with new vote"""
        proposal = self.get_proposal(proposal_id)
        if not proposal:
            return
        
        # Add vote ID
        if vote.vote_id not in proposal.votes:
            proposal.votes.append(vote.vote_id)
        
        # Update counts
        vote_type_str = vote.vote_type.value
        if vote_type_str in proposal.vote_counts:
            proposal.vote_counts[vote_type_str] += 1
        
        self._save_proposal(proposal)
    
    # ========================================================================
    # PROPOSAL MANAGEMENT
    # ========================================================================
    
    def create_proposal(self, proposer_id: str, proposal_type: ProposalType,
                       title: str, description: str,
                       consensus_model: ConsensusModel = ConsensusModel.SIMPLE_MAJORITY,
                       voting_duration_days: int = 7) -> Proposal:
        """Create a new governance proposal"""
        # Generate proposal ID
        proposal_id = hashlib.sha256(
            f"{proposer_id}:{title}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        now = datetime.utcnow()
        voting_end = now + timedelta(days=voting_duration_days)
        
        # Determine approval threshold based on consensus model
        thresholds = {
            ConsensusModel.SIMPLE_MAJORITY: 0.5,
            ConsensusModel.SUPERMAJORITY: 0.66,
            ConsensusModel.UNANIMOUS: 1.0,
            ConsensusModel.WEIGHTED: 0.5,
            ConsensusModel.QUADRATIC: 0.5
        }
        
        proposal = Proposal(
            proposal_id=proposal_id,
            proposer_id=proposer_id,
            proposal_type=proposal_type,
            title=title,
            description=description,
            status=ProposalStatus.ACTIVE,
            consensus_model=consensus_model,
            approval_threshold=thresholds.get(consensus_model, 0.5),
            quorum_required=10,  # Minimum 10 votes
            created_at=now.isoformat(),
            voting_start=now.isoformat(),
            voting_end=voting_end.isoformat()
        )
        
        self._save_proposal(proposal)
        
        # Award reputation for creating proposal
        self.record_action(proposer_id, ActionType.CONTRIBUTE, quality_multiplier=1.5)
        
        return proposal
    
    def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        """Retrieve a proposal"""
        proposal_file = self.proposals_dir / f"{proposal_id}.json"
        if not proposal_file.exists():
            return None
        
        with open(proposal_file, 'r') as f:
            data = json.load(f)
        
        data['proposal_type'] = ProposalType(data['proposal_type'])
        data['status'] = ProposalStatus(data['status'])
        data['consensus_model'] = ConsensusModel(data['consensus_model'])
        
        return Proposal(**data)
    
    def finalize_proposal(self, proposal_id: str) -> Proposal:
        """Finalize a proposal after voting period ends"""
        proposal = self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")
        
        # Check if voting period has ended
        voting_end = datetime.fromisoformat(proposal.voting_end)
        if datetime.utcnow() < voting_end:
            raise ValueError("Voting period has not ended yet")
        
        # Calculate results based on consensus model
        total_votes = len(proposal.votes)
        
        if total_votes < proposal.quorum_required:
            proposal.status = ProposalStatus.REJECTED
            proposal.approved = False
        else:
            approve_count = proposal.vote_counts.get("approve", 0)
            
            if proposal.consensus_model == ConsensusModel.WEIGHTED:
                # Calculate weighted votes
                weighted_approve = 0.0
                weighted_total = 0.0
                
                for vote_id in proposal.votes:
                    vote = self.get_vote(vote_id)
                    if vote:
                        weighted_total += vote.weight
                        if vote.vote_type == VoteType.APPROVE:
                            weighted_approve += vote.weight
                
                approval_rate = weighted_approve / weighted_total if weighted_total > 0 else 0
            else:
                # Simple counting
                approval_rate = approve_count / total_votes if total_votes > 0 else 0
            
            # Check if threshold is met
            if approval_rate >= proposal.approval_threshold:
                proposal.status = ProposalStatus.APPROVED
                proposal.approved = True
            else:
                proposal.status = ProposalStatus.REJECTED
                proposal.approved = False
        
        self._save_proposal(proposal)
        return proposal
    
    def implement_proposal(self, proposal_id: str) -> Proposal:
        """Mark a proposal as implemented"""
        proposal = self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")
        
        if proposal.status != ProposalStatus.APPROVED:
            raise ValueError("Only approved proposals can be implemented")
        
        proposal.status = ProposalStatus.IMPLEMENTED
        proposal.implemented = True
        proposal.implementation_date = datetime.utcnow().isoformat()
        
        self._save_proposal(proposal)
        return proposal
    
    def get_active_proposals(self) -> List[Proposal]:
        """Get all active proposals"""
        proposals = []
        for proposal_file in self.proposals_dir.glob("*.json"):
            with open(proposal_file, 'r') as f:
                data = json.load(f)
            
            if data.get('status') == 'active':
                data['proposal_type'] = ProposalType(data['proposal_type'])
                data['status'] = ProposalStatus(data['status'])
                data['consensus_model'] = ConsensusModel(data['consensus_model'])
                proposals.append(Proposal(**data))
        
        return proposals
    
    def _save_proposal(self, proposal: Proposal):
        """Save proposal to disk"""
        proposal_file = self.proposals_dir / f"{proposal.proposal_id}.json"
        with open(proposal_file, 'w') as f:
            json.dump(proposal.to_dict(), f, indent=2)
    
    # ========================================================================
    # GOVERNANCE POLICIES
    # ========================================================================
    
    def create_policy(self, name: str, description: str, rules: List[Dict],
                     created_by: str, proposal_id: Optional[str] = None) -> GovernancePolicy:
        """Create a new governance policy"""
        policy_id = hashlib.sha256(
            f"{name}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        policy = GovernancePolicy(
            policy_id=policy_id,
            name=name,
            description=description,
            rules=rules,
            conditions=[],
            actions=[],
            created_by=created_by,
            approved_by_proposal=proposal_id
        )
        
        self._save_policy(policy)
        return policy
    
    def get_policy(self, policy_id: str) -> Optional[GovernancePolicy]:
        """Retrieve a policy"""
        policy_file = self.policies_dir / f"{policy_id}.json"
        if not policy_file.exists():
            return None
        
        with open(policy_file, 'r') as f:
            data = json.load(f)
        
        return GovernancePolicy(**data)
    
    def get_active_policies(self) -> List[GovernancePolicy]:
        """Get all active policies"""
        policies = []
        for policy_file in self.policies_dir.glob("*.json"):
            with open(policy_file, 'r') as f:
                data = json.load(f)
            if data.get('active', False):
                policies.append(GovernancePolicy(**data))
        return policies
    
    def _save_policy(self, policy: GovernancePolicy):
        """Save policy to disk"""
        policy_file = self.policies_dir / f"{policy.policy_id}.json"
        with open(policy_file, 'w') as f:
            json.dump(policy.to_dict(), f, indent=2)
    
    # ========================================================================
    # TRUST METRICS
    # ========================================================================
    
    def calculate_trust(self, subject_id: str, subject_type: str) -> TrustMetric:
        """Calculate trust metrics for a user or object"""
        metric_id = hashlib.sha256(
            f"{subject_id}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Initialize scores
        authenticity = 0.5
        reliability = 0.5
        competence = 0.5
        benevolence = 0.5
        
        if subject_type == "user":
            reputation = self.get_reputation(subject_id)
            if reputation:
                # Higher reputation = higher trust
                competence = min(1.0, reputation.total_score / 2500.0)
                reliability = min(1.0, reputation.consistency_score / 100.0)
                
                # Negative actions reduce trust
                if reputation.actions_count > 0:
                    negative_ratio = reputation.negative_actions / reputation.actions_count
                    benevolence = max(0.0, 1.0 - negative_ratio)
                
                # Long-term users are more authentic
                if reputation.active_days > 30:
                    authenticity = min(1.0, reputation.active_days / 365.0)
        
        overall_trust = (authenticity + reliability + competence + benevolence) / 4.0
        
        metric = TrustMetric(
            metric_id=metric_id,
            subject_id=subject_id,
            subject_type=subject_type,
            overall_trust=overall_trust,
            authenticity=authenticity,
            reliability=reliability,
            competence=competence,
            benevolence=benevolence,
            sample_size=1,
            confidence=0.8
        )
        
        self._save_trust_metric(metric)
        return metric
    
    def get_trust_metric(self, subject_id: str) -> Optional[TrustMetric]:
        """Get most recent trust metric for subject"""
        # Find most recent metric file
        pattern = f"{subject_id}_*.json"
        metric_files = sorted(self.trust_dir.glob(pattern), reverse=True)
        
        if not metric_files:
            return None
        
        with open(metric_files[0], 'r') as f:
            data = json.load(f)
        
        return TrustMetric(**data)
    
    def _save_trust_metric(self, metric: TrustMetric):
        """Save trust metric to disk"""
        metric_file = self.trust_dir / f"{metric.subject_id}_{metric.metric_id}.json"
        with open(metric_file, 'w') as f:
            json.dump(metric.to_dict(), f, indent=2)


# ============================================================================
# DEMO
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Reputation & Governance Manager Demo")
    print("=" * 60)
    
    mgr = ReputationManager()
    
    # Demo 1: Reputation scoring
    print("\n[1] Reputation Scoring")
    score = mgr.record_action("alice@test.com", ActionType.CREATE_OBJECT, quality_multiplier=1.5)
    print(f"  ✓ User: {score.user_id}")
    print(f"  ✓ Total Score: {score.total_score}")
    print(f"  ✓ Level: {score.level.value}")
    print(f"  ✓ Actions: {score.actions_count}")
    
    # Demo 2: Voting
    print("\n[2] Voting Mechanism")
    proposal = mgr.create_proposal(
        "alice@test.com",
        ProposalType.POLICY_CHANGE,
        "Add new content validation rules",
        "We should implement stricter validation for submissions"
    )
    print(f"  ✓ Proposal ID: {proposal.proposal_id}")
    print(f"  ✓ Status: {proposal.status.value}")
    
    vote = mgr.cast_vote(proposal.proposal_id, "bob@test.com", VoteType.APPROVE)
    print(f"  ✓ Vote cast by: {vote.voter_id}")
    print(f"  ✓ Vote weight: {vote.weight}")
    
    # Demo 3: Trust metrics
    print("\n[3] Trust Metrics")
    trust = mgr.calculate_trust("alice@test.com", "user")
    print(f"  ✓ Overall Trust: {trust.overall_trust:.2f}")
    print(f"  ✓ Competence: {trust.competence:.2f}")
    print(f"  ✓ Reliability: {trust.reliability:.2f}")
    
    print("\n" + "=" * 60)
    print("✅ Reputation & Governance Manager operational")
    print("=" * 60)
