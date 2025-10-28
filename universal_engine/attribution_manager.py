#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Attribution Manager for CAS (Content-Addressable Storage)

Manages attribution chains, automatic credit computation, and citation
generation for objects in the CAS. Integrates with ProvenanceManager to
compute fair attribution based on contribution history.

Part of the Intellectual Property (IP) Management System - Phase 3.
"""

import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

# Import from Phase 1 (Provenance)
try:
    from provenance_manager import ProvenanceManager, ContributorRole
except ImportError:
    ProvenanceManager = None
    ContributorRole = None


# ============================================================================
# Enums
# ============================================================================

class CitationStyle(str, Enum):
    """Citation format styles"""
    APA = "apa"  # American Psychological Association
    MLA = "mla"  # Modern Language Association
    CHICAGO = "chicago"  # Chicago Manual of Style
    BIBTEX = "bibtex"  # BibTeX format
    IEEE = "ieee"  # IEEE format
    HARVARD = "harvard"  # Harvard referencing
    VANCOUVER = "vancouver"  # Vancouver system
    CUSTOM = "custom"  # Custom format


class ContributionType(str, Enum):
    """Types of contributions for attribution"""
    CREATION = "creation"  # Initial creation
    DEVELOPMENT = "development"  # Ongoing development
    MAINTENANCE = "maintenance"  # Maintenance work
    DOCUMENTATION = "documentation"  # Documentation
    TESTING = "testing"  # Testing and QA
    REVIEW = "review"  # Code/content review
    TRANSLATION = "translation"  # Translation work
    FUNDING = "funding"  # Financial support
    INFRASTRUCTURE = "infrastructure"  # Infrastructure support
    MENTORING = "mentoring"  # Mentorship


class AttributionLevel(str, Enum):
    """Level of attribution detail"""
    MINIMAL = "minimal"  # Primary authors only
    STANDARD = "standard"  # All significant contributors
    DETAILED = "detailed"  # All contributors with details
    COMPLETE = "complete"  # Full provenance chain


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class Author:
    """
    Represents an author/contributor with contact information.
    
    Attributes:
        id: Unique identifier
        name: Full name
        email: Email address
        orcid: ORCID identifier (optional)
        affiliation: Institutional affiliation
        url: Personal/institutional URL
        roles: Contribution roles
    """
    id: str
    name: str
    email: Optional[str] = None
    orcid: Optional[str] = None
    affiliation: Optional[str] = None
    url: Optional[str] = None
    roles: List[ContributionType] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'orcid': self.orcid,
            'affiliation': self.affiliation,
            'url': self.url,
            'roles': [r.value for r in self.roles]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Author':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            name=data['name'],
            email=data.get('email'),
            orcid=data.get('orcid'),
            affiliation=data.get('affiliation'),
            url=data.get('url'),
            roles=[ContributionType(r) for r in data.get('roles', [])]
        )


@dataclass
class Credit:
    """
    Represents a credit allocation to an author.
    
    Attributes:
        author: Author receiving credit
        percentage: Percentage of credit (0-100)
        roles: Contribution roles
        contributions: Specific contributions
        inherited_from: Parent objects if credit was inherited
    """
    author: Author
    percentage: float
    roles: List[ContributionType] = field(default_factory=list)
    contributions: List[str] = field(default_factory=list)
    inherited_from: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'author': self.author.to_dict(),
            'percentage': self.percentage,
            'roles': [r.value for r in self.roles],
            'contributions': self.contributions,
            'inherited_from': self.inherited_from
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Credit':
        """Create from dictionary"""
        return cls(
            author=Author.from_dict(data['author']),
            percentage=data['percentage'],
            roles=[ContributionType(r) for r in data.get('roles', [])],
            contributions=data.get('contributions', []),
            inherited_from=data.get('inherited_from', [])
        )


@dataclass
class AttributionChain:
    """
    Complete attribution chain for an object.
    
    Attributes:
        object_hash: Hash of attributed object
        object_type: Type of object
        title: Object title/name
        description: Brief description
        created_at: Creation timestamp
        last_modified: Last modification timestamp
        credits: List of credit allocations
        parent_attributions: Parent object attributions
        citation_metadata: Additional metadata for citations
    """
    object_hash: str
    object_type: str
    title: str
    description: Optional[str] = None
    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat() + 'Z'
    )
    last_modified: str = field(
        default_factory=lambda: datetime.utcnow().isoformat() + 'Z'
    )
    credits: List[Credit] = field(default_factory=list)
    parent_attributions: List[str] = field(default_factory=list)
    citation_metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'object_hash': self.object_hash,
            'object_type': self.object_type,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at,
            'last_modified': self.last_modified,
            'credits': [c.to_dict() for c in self.credits],
            'parent_attributions': self.parent_attributions,
            'citation_metadata': self.citation_metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AttributionChain':
        """Create from dictionary"""
        return cls(
            object_hash=data['object_hash'],
            object_type=data['object_type'],
            title=data['title'],
            description=data.get('description'),
            created_at=data['created_at'],
            last_modified=data['last_modified'],
            credits=[Credit.from_dict(c) for c in data.get('credits', [])],
            parent_attributions=data.get('parent_attributions', []),
            citation_metadata=data.get('citation_metadata', {})
        )


@dataclass
class Citation:
    """
    Generated citation in specific format.
    
    Attributes:
        style: Citation style used
        text: Formatted citation text
        bibtex_key: BibTeX key (if applicable)
        metadata: Additional citation metadata
    """
    style: CitationStyle
    text: str
    bibtex_key: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'style': self.style.value,
            'text': self.text,
            'bibtex_key': self.bibtex_key,
            'metadata': self.metadata
        }


# ============================================================================
# Attribution Manager
# ============================================================================

class AttributionManager:
    """
    Manages attribution chains and citation generation.
    
    Features:
    - Create attribution chains from provenance
    - Compute fair credit allocation
    - Generate citations in multiple formats
    - Handle inherited attribution from parent objects
    - Track contribution types and roles
    """
    
    def __init__(
        self,
        store_root: str = "store",
        provenance_manager: Optional[ProvenanceManager] = None
    ):
        """
        Initialize AttributionManager.
        
        Args:
            store_root: Root directory of CAS storage
            provenance_manager: Optional ProvenanceManager for integration
        """
        self.store_root = Path(store_root)
        self.attributions_dir = self.store_root / "attributions"
        self.attributions_dir.mkdir(parents=True, exist_ok=True)
        
        self.provenance_manager = provenance_manager
        
        # Author registry
        self.authors: Dict[str, Author] = {}
    
    def register_author(self, author: Author):
        """Register an author in the system"""
        self.authors[author.id] = author
    
    def get_author(self, author_id: str) -> Optional[Author]:
        """Get author by ID"""
        return self.authors.get(author_id)
    
    def create_attribution(
        self,
        object_hash: str,
        object_type: str,
        title: str,
        description: Optional[str] = None,
        citation_metadata: Optional[Dict] = None
    ) -> AttributionChain:
        """
        Create attribution chain for an object.
        
        Args:
            object_hash: Hash of object
            object_type: Type of object
            title: Object title
            description: Brief description
            citation_metadata: Additional metadata (year, publisher, etc.)
        
        Returns:
            AttributionChain instance
        """
        attribution = AttributionChain(
            object_hash=object_hash,
            object_type=object_type,
            title=title,
            description=description,
            citation_metadata=citation_metadata or {}
        )
        
        # If ProvenanceManager available, compute credits from provenance
        if self.provenance_manager:
            self._compute_credits_from_provenance(attribution)
        
        self._save_attribution(attribution)
        return attribution
    
    def load_attribution(self, object_hash: str) -> Optional[AttributionChain]:
        """Load attribution chain for an object"""
        attr_path = self._attribution_path(object_hash)
        if not attr_path.exists():
            return None
        
        with open(attr_path, 'r') as f:
            data = json.load(f)
        
        return AttributionChain.from_dict(data)
    
    def add_credit(
        self,
        object_hash: str,
        author: Author,
        percentage: float,
        roles: Optional[List[ContributionType]] = None,
        contributions: Optional[List[str]] = None
    ):
        """
        Add credit allocation to attribution chain.
        
        Args:
            object_hash: Object to attribute
            author: Author to credit
            percentage: Credit percentage (0-100)
            roles: Contribution roles
            contributions: Specific contributions
        """
        attribution = self.load_attribution(object_hash)
        if not attribution:
            raise ValueError(f"No attribution found for {object_hash}")
        
        # Register author if not already registered
        if author.id not in self.authors:
            self.register_author(author)
        
        credit = Credit(
            author=author,
            percentage=percentage,
            roles=roles or [],
            contributions=contributions or []
        )
        
        attribution.credits.append(credit)
        attribution.last_modified = datetime.utcnow().isoformat() + 'Z'
        
        self._save_attribution(attribution)
    
    def compute_inherited_attribution(
        self,
        object_hash: str,
        parent_hashes: List[str],
        own_contribution_pct: float = 30.0
    ) -> AttributionChain:
        """
        Compute attribution for derived object based on parent attributions.
        
        Args:
            object_hash: Hash of derived object
            parent_hashes: List of parent object hashes
            own_contribution_pct: Percentage of credit for new contribution
        
        Returns:
            AttributionChain with inherited credits
        """
        attribution = self.load_attribution(object_hash)
        if not attribution:
            raise ValueError(f"No attribution found for {object_hash}")
        
        # Load parent attributions
        parent_attributions = []
        for parent_hash in parent_hashes:
            parent_attr = self.load_attribution(parent_hash)
            if parent_attr:
                parent_attributions.append(parent_attr)
        
        if not parent_attributions:
            return attribution
        
        # Distribute inherited credit among parents
        inherited_pct = 100.0 - own_contribution_pct
        pct_per_parent = inherited_pct / len(parent_attributions)
        
        # Aggregate credits from parents
        inherited_credits: Dict[str, Credit] = {}
        
        for parent_attr in parent_attributions:
            for parent_credit in parent_attr.credits:
                author_id = parent_credit.author.id
                
                # Proportional credit inheritance
                inherited_amount = (
                    parent_credit.percentage / 100.0
                ) * pct_per_parent
                
                if author_id in inherited_credits:
                    inherited_credits[author_id].percentage += inherited_amount
                    inherited_credits[author_id].inherited_from.append(
                        parent_attr.object_hash
                    )
                else:
                    inherited_credits[author_id] = Credit(
                        author=parent_credit.author,
                        percentage=inherited_amount,
                        roles=parent_credit.roles.copy(),
                        contributions=["inherited_contribution"],
                        inherited_from=[parent_attr.object_hash]
                    )
        
        # Add inherited credits to attribution
        for credit in inherited_credits.values():
            attribution.credits.append(credit)
        
        attribution.parent_attributions = parent_hashes
        attribution.last_modified = datetime.utcnow().isoformat() + 'Z'
        
        self._save_attribution(attribution)
        return attribution
    
    def generate_citation(
        self,
        object_hash: str,
        style: CitationStyle = CitationStyle.APA,
        level: AttributionLevel = AttributionLevel.STANDARD
    ) -> Citation:
        """
        Generate citation for an object.
        
        Args:
            object_hash: Object to cite
            style: Citation style
            level: Level of attribution detail
        
        Returns:
            Citation instance
        """
        attribution = self.load_attribution(object_hash)
        if not attribution:
            raise ValueError(f"No attribution found for {object_hash}")
        
        # Filter authors based on level
        authors = self._filter_authors_by_level(attribution, level)
        
        if style == CitationStyle.APA:
            text = self._format_apa(attribution, authors)
        elif style == CitationStyle.BIBTEX:
            text = self._format_bibtex(attribution, authors)
        elif style == CitationStyle.MLA:
            text = self._format_mla(attribution, authors)
        elif style == CitationStyle.CHICAGO:
            text = self._format_chicago(attribution, authors)
        elif style == CitationStyle.IEEE:
            text = self._format_ieee(attribution, authors)
        else:
            text = self._format_default(attribution, authors)
        
        return Citation(
            style=style,
            text=text,
            bibtex_key=self._generate_bibtex_key(attribution),
            metadata=attribution.citation_metadata
        )
    
    def _compute_credits_from_provenance(self, attribution: AttributionChain):
        """Compute credits from provenance chain"""
        if not self.provenance_manager:
            return
        
        prov = self.provenance_manager.load_provenance(
            attribution.object_hash,
            attribution.object_type
        )
        if not prov:
            return
        
        # Convert provenance contributors to attribution credits
        for contributor in prov.contributors:
            # Map contributor ID to author
            author = self.get_author(contributor.contributor_id)
            if not author:
                # Create basic author from contributor
                author = Author(
                    id=contributor.contributor_id,
                    name=contributor.contributor_id,
                    roles=self._map_contributor_role(contributor.role)
                )
                self.register_author(author)
            
            credit = Credit(
                author=author,
                percentage=contributor.contribution_pct,
                roles=self._map_contributor_role(contributor.role),
                contributions=contributor.contributions
            )
            
            attribution.credits.append(credit)
    
    def _map_contributor_role(
        self,
        prov_role
    ) -> List[ContributionType]:
        """Map provenance contributor role to attribution contribution types"""
        if not ContributorRole:
            return [ContributionType.DEVELOPMENT]
        
        mapping = {
            ContributorRole.PRIMARY_AUTHOR: [ContributionType.CREATION],
            ContributorRole.CO_AUTHOR: [ContributionType.CREATION],
            ContributorRole.MAINTAINER: [ContributionType.MAINTENANCE],
            ContributorRole.CONTRIBUTOR: [ContributionType.DEVELOPMENT],
            ContributorRole.REVIEWER: [ContributionType.REVIEW],
            ContributorRole.TESTER: [ContributionType.TESTING],
            ContributorRole.DOCUMENTER: [ContributionType.DOCUMENTATION],
            ContributorRole.TRANSLATOR: [ContributionType.TRANSLATION],
            ContributorRole.SPONSOR: [ContributionType.FUNDING]
        }
        
        return mapping.get(prov_role, [ContributionType.DEVELOPMENT])
    
    def _filter_authors_by_level(
        self,
        attribution: AttributionChain,
        level: AttributionLevel
    ) -> List[Credit]:
        """Filter authors based on attribution level"""
        if level == AttributionLevel.MINIMAL:
            # Top 3 contributors only
            sorted_credits = sorted(
                attribution.credits,
                key=lambda c: c.percentage,
                reverse=True
            )
            return sorted_credits[:3]
        
        elif level == AttributionLevel.STANDARD:
            # Contributors with >5% credit (strictly greater)
            return [c for c in attribution.credits if c.percentage > 5.0]
        
        else:  # DETAILED or COMPLETE
            return attribution.credits
    
    def _format_apa(
        self,
        attribution: AttributionChain,
        authors: List[Credit]
    ) -> str:
        """Format citation in APA style"""
        # Format authors
        author_names = []
        for credit in authors[:20]:  # APA: max 20 authors
            name = credit.author.name
            # Split name into last, first
            parts = name.split()
            if len(parts) >= 2:
                formatted = f"{parts[-1]}, {parts[0][0]}."
            else:
                formatted = name
            author_names.append(formatted)
        
        if len(authors) > 20:
            author_str = ", ".join(author_names[:19]) + ", ... " + author_names[-1]
        elif len(author_names) > 1:
            author_str = ", ".join(author_names[:-1]) + ", & " + author_names[-1]
        else:
            author_str = author_names[0] if author_names else "Unknown"
        
        # Get year
        year = attribution.citation_metadata.get(
            'year',
            attribution.created_at[:4]
        )
        
        # Format: Author, A. (Year). Title. Type. Hash.
        return (
            f"{author_str} ({year}). {attribution.title}. "
            f"[{attribution.object_type}]. Hash: {attribution.object_hash[:8]}"
        )
    
    def _format_bibtex(
        self,
        attribution: AttributionChain,
        authors: List[Credit]
    ) -> str:
        """Format citation in BibTeX"""
        key = self._generate_bibtex_key(attribution)
        
        # Format authors
        author_names = []
        for credit in authors:
            author_names.append(credit.author.name)
        author_str = " and ".join(author_names)
        
        year = attribution.citation_metadata.get(
            'year',
            attribution.created_at[:4]
        )
        
        lines = [
            f"@misc{{{key},",
            f"  author = {{{author_str}}},",
            f"  title = {{{attribution.title}}},",
            f"  year = {{{year}}},",
            f"  note = {{CAS Object: {attribution.object_hash[:8]}}}",
            "}"
        ]
        
        return "\n".join(lines)
    
    def _format_mla(
        self,
        attribution: AttributionChain,
        authors: List[Credit]
    ) -> str:
        """Format citation in MLA style"""
        # First author: Last, First
        if not authors:
            author_str = "Unknown"
        else:
            first = authors[0].author.name.split()
            if len(first) >= 2:
                author_str = f"{first[-1]}, {first[0]}"
            else:
                author_str = first[0]
            
            if len(authors) > 1:
                author_str += ", et al"
        
        # Format: Author. "Title." Type, Year.
        year = attribution.citation_metadata.get(
            'year',
            attribution.created_at[:4]
        )
        
        return (
            f'{author_str}. "{attribution.title}." '
            f'{attribution.object_type.title()}, {year}.'
        )
    
    def _format_chicago(
        self,
        attribution: AttributionChain,
        authors: List[Credit]
    ) -> str:
        """Format citation in Chicago style"""
        # Similar to APA but different punctuation
        author_names = []
        for i, credit in enumerate(authors[:10]):
            name = credit.author.name
            parts = name.split()
            if i == 0 and len(parts) >= 2:
                # First author: Last, First
                formatted = f"{parts[-1]}, {' '.join(parts[:-1])}"
            else:
                # Others: First Last
                formatted = name
            author_names.append(formatted)
        
        if len(authors) > 10:
            author_str = ", ".join(author_names) + ", et al."
        elif len(author_names) > 1:
            author_str = ", ".join(author_names[:-1]) + ", and " + author_names[-1]
        else:
            author_str = author_names[0] if author_names else "Unknown"
        
        year = attribution.citation_metadata.get(
            'year',
            attribution.created_at[:4]
        )
        
        return (
            f'{author_str}. {year}. "{attribution.title}." '
            f'{attribution.object_type.title()}. Hash {attribution.object_hash[:8]}.'
        )
    
    def _format_ieee(
        self,
        attribution: AttributionChain,
        authors: List[Credit]
    ) -> str:
        """Format citation in IEEE style"""
        # Format: [1] F. Last, "Title," Type, Year.
        author_names = []
        for credit in authors[:6]:  # IEEE: max 6 authors
            name = credit.author.name
            parts = name.split()
            if len(parts) >= 2:
                formatted = f"{parts[0][0]}. {parts[-1]}"
            else:
                formatted = name
            author_names.append(formatted)
        
        if len(authors) > 6:
            author_str = ", ".join(author_names) + ", et al."
        else:
            author_str = ", ".join(author_names)
        
        year = attribution.citation_metadata.get(
            'year',
            attribution.created_at[:4]
        )
        
        return (
            f'{author_str}, "{attribution.title}," '
            f'{attribution.object_type}, {year}.'
        )
    
    def _format_default(
        self,
        attribution: AttributionChain,
        authors: List[Credit]
    ) -> str:
        """Default citation format"""
        author_names = [c.author.name for c in authors]
        author_str = ", ".join(author_names) if author_names else "Unknown"
        
        return (
            f"{author_str}. {attribution.title}. "
            f"{attribution.object_type}. {attribution.created_at[:10]}."
        )
    
    def _generate_bibtex_key(self, attribution: AttributionChain) -> str:
        """Generate BibTeX key"""
        if attribution.credits:
            # First author last name
            first_author = attribution.credits[0].author.name.split()[-1]
        else:
            first_author = "unknown"
        
        year = attribution.citation_metadata.get(
            'year',
            attribution.created_at[:4]
        )
        
        # Key format: firstauthor_year_type
        return f"{first_author.lower()}_{year}_{attribution.object_type}"
    
    def _attribution_path(self, object_hash: str) -> Path:
        """Get path to attribution file"""
        return self.attributions_dir / f"{object_hash}.json"
    
    def _save_attribution(self, attribution: AttributionChain):
        """Save attribution to storage"""
        path = self._attribution_path(attribution.object_hash)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(attribution.to_dict(), f, indent=2)
    
    def export_to_yaml(self, object_hash: str, output_path: str):
        """Export attribution to YAML"""
        attribution = self.load_attribution(object_hash)
        if not attribution:
            raise ValueError(f"No attribution found for {object_hash}")
        
        with open(output_path, 'w') as f:
            yaml.dump(attribution.to_dict(), f, default_flow_style=False)
    
    def get_total_credits(self, object_hash: str) -> float:
        """Get total credit percentage (should be ~100%)"""
        attribution = self.load_attribution(object_hash)
        if not attribution:
            return 0.0
        
        return sum(c.percentage for c in attribution.credits)


# ============================================================================
# Utility Functions
# ============================================================================

def create_author(
    author_id: str,
    name: str,
    email: Optional[str] = None,
    **kwargs
) -> Author:
    """
    Create an Author instance.
    
    Args:
        author_id: Unique identifier
        name: Full name
        email: Email address
        **kwargs: Additional Author attributes
    
    Returns:
        Author instance
    """
    return Author(id=author_id, name=name, email=email, **kwargs)


if __name__ == "__main__":
    # Demo usage
    manager = AttributionManager()
    
    print("=== Attribution Manager Demo ===\n")
    
    # Create authors
    alice = create_author(
        "alice",
        "Alice Johnson",
        email="alice@example.com",
        affiliation="University of Linguistics"
    )
    bob = create_author(
        "bob",
        "Bob Smith",
        email="bob@example.com"
    )
    
    manager.register_author(alice)
    manager.register_author(bob)
    
    # Create attribution
    attribution = manager.create_attribution(
        object_hash="abc123",
        object_type="pattern",
        title="Sanskrit Nominal Pattern Extractor",
        description="Automated pattern extraction from corpus",
        citation_metadata={'year': '2025', 'version': '1.0'}
    )
    
    # Add credits
    manager.add_credit(
        "abc123",
        alice,
        60.0,
        roles=[ContributionType.CREATION, ContributionType.DEVELOPMENT],
        contributions=["initial_implementation", "algorithm_design"]
    )
    
    manager.add_credit(
        "abc123",
        bob,
        40.0,
        roles=[ContributionType.TESTING, ContributionType.REVIEW],
        contributions=["testing", "code_review"]
    )
    
    print("Credits:")
    for credit in attribution.credits:
        print(f"  {credit.author.name}: {credit.percentage}%")
    
    print("\n" + "="*60 + "\n")
    
    # Generate citations
    print("Citations:\n")
    
    for style in [CitationStyle.APA, CitationStyle.BIBTEX, CitationStyle.MLA]:
        citation = manager.generate_citation("abc123", style)
        print(f"{style.value.upper()}:")
        print(f"{citation.text}\n")
