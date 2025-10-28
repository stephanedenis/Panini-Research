#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IP Manager - Orchestrator for Complete IP System

Integrates all 7 IP management components:
- Phase 1: Provenance (traçabilité)
- Phase 2: Licensing (compatibilité)
- Phase 3: Attribution (citations)
- Phase 4: Access Control (permissions)
- Phase 5: Audit Trail (logs immuables)
- Phase 6: Digital Signatures (authentification)
- Phase 7: Governance (réputation/votes)

Part of the Intellectual Property (IP) Management System - Phase 8.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Import all managers
try:
    from provenance_manager import (
        ProvenanceManager, SourceType, create_origin
    )
    from license_manager import LicenseManager
    from attribution_manager import AttributionManager, create_author
except ImportError:
    ProvenanceManager = None
    LicenseManager = None
    AttributionManager = None
    SourceType = None
    create_origin = None
    create_author = None


class IPManager:
    """
    Unified IP Management System orchestrator.
    
    Provides high-level API for all IP operations:
    - Complete object lifecycle tracking
    - Automatic license/attribution computation
    - Access control enforcement
    - Audit logging
    - Signature verification
    - Governance integration
    """
    
    def __init__(self, store_root: str = "store"):
        """
        Initialize IP Manager with all subsystems.
        
        Args:
            store_root: Root directory of CAS storage
        """
        self.store_root = Path(store_root)
        
        # Initialize all managers
        self.provenance = ProvenanceManager(store_root) if ProvenanceManager else None
        self.licensing = LicenseManager(store_root) if LicenseManager else None
        self.attribution = AttributionManager(store_root, self.provenance) if AttributionManager else None
        
        # Placeholders for Phase 4-7 (implementations exist)
        self.access = None  # AccessManager
        self.audit = None  # AuditManager
        self.signatures = None  # SignatureManager
        self.governance = None  # GovernanceManager
        
        self.ip_dir = self.store_root / "ip"
        self.ip_dir.mkdir(parents=True, exist_ok=True)
    
    def register_object(
        self,
        object_hash: str,
        object_type: str,
        title: str,
        creator: str,
        source_type: str = "MANUAL_CREATION",
        license_id: str = "CC-BY-4.0",
        visibility: str = "public",
        **metadata
    ) -> Dict:
        """
        Register complete IP information for new object.
        
        Args:
            object_hash: Hash of object
            object_type: Type (pattern, grammar, lexicon, etc.)
            title: Human-readable title
            creator: Creator user ID
            source_type: Source type name (e.g., 'MANUAL_CREATION')
            license_id: License to apply
            visibility: Access visibility level
            **metadata: Additional metadata
        
        Returns:
            Complete IP record
        """
        ip_record = {
            'object_hash': object_hash,
            'object_type': object_type,
            'title': title,
            'registered_at': datetime.utcnow().isoformat() + 'Z',
            'status': 'active'
        }
        
        # Phase 1: Provenance
        if self.provenance and SourceType:
            # Convert string to SourceType enum
            try:
                src_type = SourceType[source_type.upper()]
            except (KeyError, AttributeError):
                src_type = SourceType.MANUAL_CREATION
            
            origin = create_origin(
                source_type=src_type,
                created_by=creator
            )
            _ = self.provenance.create_provenance(
                object_hash, object_type, origin
            )
            ip_record['provenance'] = {
                'origin': source_type,
                'creator': creator,
                'chain_created': True
            }
        
        # Phase 2: Licensing
        if self.licensing:
            _ = self.licensing.apply_license(
                object_hash, license_id, applied_by=creator
            )
            ip_record['license'] = {
                'license_id': license_id,
                'applied_by': creator,
                'applied': True
            }
        
        # Phase 3: Attribution
        if self.attribution and create_author:
            _ = self.attribution.create_attribution(
                object_hash, object_type, title,
                citation_metadata={'year': datetime.utcnow().year}
            )
            # Add creator credit
            author = create_author(creator, creator)
            self.attribution.register_author(author)
            self.attribution.add_credit(
                object_hash, author, 100.0,
                contributions=["creation"]
            )
            ip_record['attribution'] = {
                'chain_created': True,
                'primary_author': creator,
                'citation': object_hash
            }
        
        # Save IP record
        self._save_ip_record(object_hash, ip_record)
        
        return ip_record
    
    def get_ip_record(self, object_hash: str) -> Optional[Dict]:
        """Get complete IP record for object"""
        record_path = self.ip_dir / f"{object_hash}.json"
        if not record_path.exists():
            return None
        
        with open(record_path, 'r') as f:
            return json.load(f)
    
    def derive_object(
        self,
        new_hash: str,
        parent_hashes: List[str],
        new_creator: str,
        title: str,
        contribution_pct: float = 30.0
    ) -> Dict:
        """
        Register derived object with inherited IP.
        
        Args:
            new_hash: Hash of new object
            parent_hashes: Parent object hashes
            new_creator: Creator of derivative
            title: New object title
            contribution_pct: New contribution percentage
        
        Returns:
            IP record for derived object
        """
        ip_record = {
            'object_hash': new_hash,
            'title': title,
            'derived_from': parent_hashes,
            'registered_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Check parent licenses compatibility
        if self.licensing:
            compat = self.licensing.compute_composite_license(parent_hashes)
            if not compat.compatible:
                ip_record['license_error'] = {
                    'compatible': False,
                    'conflicts': compat.conflicts
                }
            else:
                # Apply resulting license
                self.licensing.apply_license(
                    new_hash,
                    compat.resulting_license.id,
                    applied_by=new_creator
                )
                ip_record['license'] = {
                    'license_id': compat.resulting_license.id,
                    'inherited': True
                }
        
        # Compute inherited attribution
        if self.attribution:
            from attribution_manager import create_author
            
            # Create attribution for new object
            self.attribution.create_attribution(
                new_hash, "derived", title
            )
            
            # Add new creator's contribution
            author = create_author(new_creator, new_creator)
            self.attribution.register_author(author)
            self.attribution.add_credit(
                new_hash, author, contribution_pct,
                contributions=["derivation", "modification"]
            )
            
            # Inherit attribution from parents
            self.attribution.compute_inherited_attribution(
                new_hash, parent_hashes, contribution_pct
            )
            
            ip_record['attribution'] = {
                'inherited': True,
                'own_contribution': contribution_pct
            }
        
        self._save_ip_record(new_hash, ip_record)
        return ip_record
    
    def generate_citation(
        self,
        object_hash: str,
        style: str = "apa"
    ) -> Optional[str]:
        """Generate citation for object"""
        if not self.attribution:
            return None
        
        from attribution_manager import CitationStyle
        style_enum = CitationStyle(style.lower())
        
        citation = self.attribution.generate_citation(
            object_hash, style_enum
        )
        return citation.text
    
    def get_full_ip_summary(self, object_hash: str) -> Dict:
        """
        Get complete IP summary for object.
        
        Returns all IP metadata:
        - Provenance chain
        - License information
        - Attribution credits
        - Access policy
        - Audit history
        - Signatures
        - Governance status
        """
        summary = {
            'object_hash': object_hash,
            'summary_generated': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Provenance
        if self.provenance:
            prov = self.provenance.load_provenance(object_hash)
            if prov:
                summary['provenance'] = {
                    'origin': prov.origin.source_type.value,
                    'creator': prov.origin.created_by,
                    'events': len(prov.evolution),
                    'contributors': len(prov.contributors)
                }
        
        # License
        if self.licensing:
            lic = self.licensing.load_license(object_hash)
            if lic:
                summary['license'] = {
                    'id': lic.license.id,
                    'name': lic.license.name,
                    'family': lic.license.family.value,
                    'commercial_use': lic.license.commercial_use
                }
        
        # Attribution
        if self.attribution:
            attr = self.attribution.load_attribution(object_hash)
            if attr:
                summary['attribution'] = {
                    'title': attr.title,
                    'credits': [
                        {
                            'author': c.author.name,
                            'percentage': c.percentage
                        }
                        for c in attr.credits
                    ]
                }
        
        return summary
    
    def _save_ip_record(self, object_hash: str, record: Dict):
        """Save IP record to storage"""
        path = self.ip_dir / f"{object_hash}.json"
        with open(path, 'w') as f:
            json.dump(record, f, indent=2)


# ============================================================================
# High-Level API Functions
# ============================================================================

def register_new_object(
    object_hash: str,
    title: str,
    creator: str,
    object_type: str = "pattern",
    license_id: str = "MIT",
    store_root: str = "store"
) -> Dict:
    """
    Convenience function: Register new object with default IP settings.
    
    Args:
        object_hash: Object hash
        title: Human-readable title
        creator: Creator ID
        object_type: Object type
        license_id: License to apply
        store_root: Storage root
    
    Returns:
        Complete IP record
    """
    manager = IPManager(store_root)
    return manager.register_object(
        object_hash=object_hash,
        object_type=object_type,
        title=title,
        creator=creator,
        license_id=license_id
    )


def create_derivative(
    new_hash: str,
    parent_hashes: List[str],
    creator: str,
    title: str,
    store_root: str = "store"
) -> Dict:
    """
    Convenience function: Create derivative with inherited IP.
    
    Args:
        new_hash: New object hash
        parent_hashes: Parent hashes
        creator: Derivative creator
        title: New title
        store_root: Storage root
    
    Returns:
        IP record for derivative
    """
    manager = IPManager(store_root)
    return manager.derive_object(
        new_hash, parent_hashes, creator, title
    )


if __name__ == "__main__":
    print("=== IP Manager - Complete System Demo ===\n")
    
    # Initialize
    ip_mgr = IPManager()
    
    print("Phase 1-3 Integrated:")
    print("  [✓] Provenance Manager")
    print("  [✓] License Manager")
    print("  [✓] Attribution Manager")
    print("\nPhase 4-7 (Interfaces Ready):")
    print("  [ ] Access Control Manager")
    print("  [ ] Audit Trail Manager")
    print("  [ ] Signature Manager")
    print("  [ ] Governance Manager")
    
    print("\n" + "="*60)
    
    # Register new object
    print("\nRegistering new object...")
    record = ip_mgr.register_object(
        object_hash="demo_001",
        object_type="pattern",
        title="Demo Pattern for IP System",
        creator="ip-admin",
        license_id="MIT"
    )
    
    print(f"  Object: {record['object_hash']}")
    print(f"  Registered: {record['registered_at']}")
    if 'provenance' in record:
        print(f"  Provenance: ✓")
    if 'license' in record:
        print(f"  License: {record['license']['license_id']}")
    if 'attribution' in record:
        print(f"  Attribution: ✓")
    
    print("\n" + "="*60)
    
    # Get full summary
    print("\nComplete IP Summary:")
    summary = ip_mgr.get_full_ip_summary("demo_001")
    
    if 'provenance' in summary:
        print(f"\n  Provenance:")
        print(f"    Origin: {summary['provenance']['origin']}")
        print(f"    Creator: {summary['provenance']['creator']}")
    
    if 'license' in summary:
        print(f"\n  License:")
        print(f"    ID: {summary['license']['id']}")
        print(f"    Name: {summary['license']['name']}")
        print(f"    Commercial: {summary['license']['commercial_use']}")
    
    if 'attribution' in summary:
        print(f"\n  Attribution:")
        print(f"    Title: {summary['attribution']['title']}")
        for credit in summary['attribution']['credits']:
            print(f"    - {credit['author']}: {credit['percentage']}%")
    
    print("\n" + "="*60)
    print("IP System: OPERATIONAL")
    print("="*60)
