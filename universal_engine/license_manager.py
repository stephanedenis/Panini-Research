#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
License Manager for CAS (Content-Addressable Storage)

Manages licensing information, compatibility checking, and composite license
computation for objects in the CAS. Supports 20+ standard licenses including
open source (MIT, GPL, Apache), creative commons (CC-BY, CC-SA), and custom.

Part of the Intellectual Property (IP) Management System - Phase 2.
"""

import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class LicenseFamily(str, Enum):
    """Major license families for categorization"""
    PERMISSIVE = "permissive"  # MIT, BSD, Apache
    COPYLEFT_WEAK = "copyleft_weak"  # LGPL, MPL
    COPYLEFT_STRONG = "copyleft_strong"  # GPL, AGPL
    CREATIVE_COMMONS = "creative_commons"  # CC-BY, CC-SA, CC-0
    PROPRIETARY = "proprietary"  # Custom proprietary
    PUBLIC_DOMAIN = "public_domain"  # CC-0, Unlicense
    CUSTOM = "custom"  # User-defined


class Compatibility(str, Enum):
    """Compatibility levels between licenses"""
    COMPATIBLE = "compatible"  # Can combine freely
    ONE_WAY = "one_way"  # A→B but not B→A
    CONDITIONAL = "conditional"  # Compatible under conditions
    INCOMPATIBLE = "incompatible"  # Cannot combine


class Restriction(str, Enum):
    """License restrictions and requirements"""
    ATTRIBUTION_REQUIRED = "attribution_required"
    SHARE_ALIKE = "share_alike"  # Derivative must use same license
    COPYLEFT = "copyleft"  # Source must be disclosed
    NO_WARRANTY = "no_warranty"
    TRADEMARK_USE = "trademark_use"
    PATENT_GRANT = "patent_grant"
    COMMERCIAL_USE = "commercial_use"
    MODIFICATION_ALLOWED = "modification_allowed"
    DISTRIBUTION_ALLOWED = "distribution_allowed"
    PRIVATE_USE = "private_use"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class License:
    """
    Represents a license with its properties and restrictions.
    
    Attributes:
        id: Unique identifier (e.g., "MIT", "GPL-3.0")
        name: Full name (e.g., "MIT License")
        family: License family (permissive, copyleft, etc.)
        version: Version number (e.g., "3.0" for GPL-3.0)
        url: Official license text URL
        restrictions: Set of restrictions/requirements
        commercial_use: Whether commercial use is allowed
        modification_allowed: Whether modifications are allowed
        distribution_allowed: Whether distribution is allowed
        patent_grant: Whether patent rights are granted
        attribution_required: Whether attribution is required
        share_alike: Whether derivatives must use same license
        copyleft: Whether source disclosure is required
    """
    id: str
    name: str
    family: LicenseFamily
    version: Optional[str] = None
    url: Optional[str] = None
    restrictions: Set[Restriction] = field(default_factory=set)
    commercial_use: bool = True
    modification_allowed: bool = True
    distribution_allowed: bool = True
    patent_grant: bool = False
    attribution_required: bool = False
    share_alike: bool = False
    copyleft: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'family': self.family.value,
            'version': self.version,
            'url': self.url,
            'restrictions': [r.value for r in self.restrictions],
            'commercial_use': self.commercial_use,
            'modification_allowed': self.modification_allowed,
            'distribution_allowed': self.distribution_allowed,
            'patent_grant': self.patent_grant,
            'attribution_required': self.attribution_required,
            'share_alike': self.share_alike,
            'copyleft': self.copyleft
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'License':
        """Create License from dictionary"""
        return cls(
            id=data['id'],
            name=data['name'],
            family=LicenseFamily(data['family']),
            version=data.get('version'),
            url=data.get('url'),
            restrictions={Restriction(r) for r in data.get('restrictions', [])},
            commercial_use=data.get('commercial_use', True),
            modification_allowed=data.get('modification_allowed', True),
            distribution_allowed=data.get('distribution_allowed', True),
            patent_grant=data.get('patent_grant', False),
            attribution_required=data.get('attribution_required', False),
            share_alike=data.get('share_alike', False),
            copyleft=data.get('copyleft', False)
        )


@dataclass
class ObjectLicense:
    """
    License information for a specific CAS object.
    
    Attributes:
        object_hash: Hash of the licensed object
        license: Primary license
        secondary_licenses: Additional licenses (for dual-licensing)
        applied_at: When license was applied
        applied_by: Who applied the license
        inherited_from: Parent objects if license was inherited
        custom_terms: Additional custom terms
        expiration: Optional expiration date
    """
    object_hash: str
    license: License
    secondary_licenses: List[License] = field(default_factory=list)
    applied_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')
    applied_by: Optional[str] = None
    inherited_from: List[str] = field(default_factory=list)
    custom_terms: Optional[str] = None
    expiration: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'object_hash': self.object_hash,
            'license': self.license.to_dict(),
            'secondary_licenses': [lic.to_dict() for lic in self.secondary_licenses],
            'applied_at': self.applied_at,
            'applied_by': self.applied_by,
            'inherited_from': self.inherited_from,
            'custom_terms': self.custom_terms,
            'expiration': self.expiration
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ObjectLicense':
        """Create ObjectLicense from dictionary"""
        return cls(
            object_hash=data['object_hash'],
            license=License.from_dict(data['license']),
            secondary_licenses=[License.from_dict(lic) for lic in data.get('secondary_licenses', [])],
            applied_at=data['applied_at'],
            applied_by=data.get('applied_by'),
            inherited_from=data.get('inherited_from', []),
            custom_terms=data.get('custom_terms'),
            expiration=data.get('expiration')
        )


@dataclass
class CompatibilityResult:
    """
    Result of license compatibility check.
    
    Attributes:
        compatible: Whether licenses are compatible
        compatibility: Compatibility level
        resulting_license: License to use for derivative (if compatible)
        conflicts: List of conflicts if incompatible
        conditions: Conditions required for compatibility
        recommendations: Recommendations for resolving issues
    """
    compatible: bool
    compatibility: Compatibility
    resulting_license: Optional[License] = None
    conflicts: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'compatible': self.compatible,
            'compatibility': self.compatibility.value,
            'resulting_license': self.resulting_license.to_dict() if self.resulting_license else None,
            'conflicts': self.conflicts,
            'conditions': self.conditions,
            'recommendations': self.recommendations
        }


# ============================================================================
# License Registry - Standard Licenses
# ============================================================================

STANDARD_LICENSES = {
    # ===== Permissive Licenses =====
    'MIT': License(
        id='MIT',
        name='MIT License',
        family=LicenseFamily.PERMISSIVE,
        url='https://opensource.org/licenses/MIT',
        restrictions={Restriction.ATTRIBUTION_REQUIRED, Restriction.NO_WARRANTY},
        attribution_required=True,
        patent_grant=False
    ),
    
    'BSD-2-Clause': License(
        id='BSD-2-Clause',
        name='BSD 2-Clause "Simplified" License',
        family=LicenseFamily.PERMISSIVE,
        version='2-Clause',
        url='https://opensource.org/licenses/BSD-2-Clause',
        restrictions={Restriction.ATTRIBUTION_REQUIRED, Restriction.NO_WARRANTY},
        attribution_required=True
    ),
    
    'BSD-3-Clause': License(
        id='BSD-3-Clause',
        name='BSD 3-Clause "New" or "Revised" License',
        family=LicenseFamily.PERMISSIVE,
        version='3-Clause',
        url='https://opensource.org/licenses/BSD-3-Clause',
        restrictions={Restriction.ATTRIBUTION_REQUIRED, Restriction.NO_WARRANTY, Restriction.TRADEMARK_USE},
        attribution_required=True
    ),
    
    'Apache-2.0': License(
        id='Apache-2.0',
        name='Apache License 2.0',
        family=LicenseFamily.PERMISSIVE,
        version='2.0',
        url='https://www.apache.org/licenses/LICENSE-2.0',
        restrictions={
            Restriction.ATTRIBUTION_REQUIRED,
            Restriction.NO_WARRANTY,
            Restriction.PATENT_GRANT,
            Restriction.TRADEMARK_USE
        },
        attribution_required=True,
        patent_grant=True
    ),
    
    # ===== Weak Copyleft =====
    'LGPL-2.1': License(
        id='LGPL-2.1',
        name='GNU Lesser General Public License v2.1',
        family=LicenseFamily.COPYLEFT_WEAK,
        version='2.1',
        url='https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html',
        restrictions={
            Restriction.ATTRIBUTION_REQUIRED,
            Restriction.SHARE_ALIKE,
            Restriction.NO_WARRANTY
        },
        attribution_required=True,
        share_alike=True,
        copyleft=True
    ),
    
    'LGPL-3.0': License(
        id='LGPL-3.0',
        name='GNU Lesser General Public License v3.0',
        family=LicenseFamily.COPYLEFT_WEAK,
        version='3.0',
        url='https://www.gnu.org/licenses/lgpl-3.0.html',
        restrictions={
            Restriction.ATTRIBUTION_REQUIRED,
            Restriction.SHARE_ALIKE,
            Restriction.PATENT_GRANT,
            Restriction.NO_WARRANTY
        },
        attribution_required=True,
        share_alike=True,
        copyleft=True,
        patent_grant=True
    ),
    
    'MPL-2.0': License(
        id='MPL-2.0',
        name='Mozilla Public License 2.0',
        family=LicenseFamily.COPYLEFT_WEAK,
        version='2.0',
        url='https://www.mozilla.org/MPL/2.0/',
        restrictions={
            Restriction.ATTRIBUTION_REQUIRED,
            Restriction.SHARE_ALIKE,
            Restriction.PATENT_GRANT,
            Restriction.NO_WARRANTY
        },
        attribution_required=True,
        share_alike=True,
        copyleft=True,
        patent_grant=True
    ),
    
    # ===== Strong Copyleft =====
    'GPL-2.0': License(
        id='GPL-2.0',
        name='GNU General Public License v2.0',
        family=LicenseFamily.COPYLEFT_STRONG,
        version='2.0',
        url='https://www.gnu.org/licenses/old-licenses/gpl-2.0.html',
        restrictions={
            Restriction.ATTRIBUTION_REQUIRED,
            Restriction.SHARE_ALIKE,
            Restriction.COPYLEFT,
            Restriction.NO_WARRANTY
        },
        attribution_required=True,
        share_alike=True,
        copyleft=True
    ),
    
    'GPL-3.0': License(
        id='GPL-3.0',
        name='GNU General Public License v3.0',
        family=LicenseFamily.COPYLEFT_STRONG,
        version='3.0',
        url='https://www.gnu.org/licenses/gpl-3.0.html',
        restrictions={
            Restriction.ATTRIBUTION_REQUIRED,
            Restriction.SHARE_ALIKE,
            Restriction.COPYLEFT,
            Restriction.PATENT_GRANT,
            Restriction.NO_WARRANTY
        },
        attribution_required=True,
        share_alike=True,
        copyleft=True,
        patent_grant=True
    ),
    
    'AGPL-3.0': License(
        id='AGPL-3.0',
        name='GNU Affero General Public License v3.0',
        family=LicenseFamily.COPYLEFT_STRONG,
        version='3.0',
        url='https://www.gnu.org/licenses/agpl-3.0.html',
        restrictions={
            Restriction.ATTRIBUTION_REQUIRED,
            Restriction.SHARE_ALIKE,
            Restriction.COPYLEFT,
            Restriction.PATENT_GRANT,
            Restriction.NO_WARRANTY
        },
        attribution_required=True,
        share_alike=True,
        copyleft=True,
        patent_grant=True
    ),
    
    # ===== Creative Commons =====
    'CC0-1.0': License(
        id='CC0-1.0',
        name='Creative Commons Zero v1.0 Universal',
        family=LicenseFamily.PUBLIC_DOMAIN,
        version='1.0',
        url='https://creativecommons.org/publicdomain/zero/1.0/',
        restrictions=set(),
        attribution_required=False
    ),
    
    'CC-BY-4.0': License(
        id='CC-BY-4.0',
        name='Creative Commons Attribution 4.0 International',
        family=LicenseFamily.CREATIVE_COMMONS,
        version='4.0',
        url='https://creativecommons.org/licenses/by/4.0/',
        restrictions={Restriction.ATTRIBUTION_REQUIRED, Restriction.NO_WARRANTY},
        attribution_required=True
    ),
    
    'CC-BY-SA-4.0': License(
        id='CC-BY-SA-4.0',
        name='Creative Commons Attribution-ShareAlike 4.0 International',
        family=LicenseFamily.CREATIVE_COMMONS,
        version='4.0',
        url='https://creativecommons.org/licenses/by-sa/4.0/',
        restrictions={
            Restriction.ATTRIBUTION_REQUIRED,
            Restriction.SHARE_ALIKE,
            Restriction.NO_WARRANTY
        },
        attribution_required=True,
        share_alike=True
    ),
    
    'CC-BY-NC-4.0': License(
        id='CC-BY-NC-4.0',
        name='Creative Commons Attribution-NonCommercial 4.0 International',
        family=LicenseFamily.CREATIVE_COMMONS,
        version='4.0',
        url='https://creativecommons.org/licenses/by-nc/4.0/',
        restrictions={Restriction.ATTRIBUTION_REQUIRED, Restriction.NO_WARRANTY},
        attribution_required=True,
        commercial_use=False
    ),
    
    'CC-BY-NC-SA-4.0': License(
        id='CC-BY-NC-SA-4.0',
        name='Creative Commons Attribution-NonCommercial-ShareAlike 4.0',
        family=LicenseFamily.CREATIVE_COMMONS,
        version='4.0',
        url='https://creativecommons.org/licenses/by-nc-sa/4.0/',
        restrictions={
            Restriction.ATTRIBUTION_REQUIRED,
            Restriction.SHARE_ALIKE,
            Restriction.NO_WARRANTY
        },
        attribution_required=True,
        share_alike=True,
        commercial_use=False
    ),
    
    'CC-BY-ND-4.0': License(
        id='CC-BY-ND-4.0',
        name='Creative Commons Attribution-NoDerivatives 4.0 International',
        family=LicenseFamily.CREATIVE_COMMONS,
        version='4.0',
        url='https://creativecommons.org/licenses/by-nd/4.0/',
        restrictions={Restriction.ATTRIBUTION_REQUIRED, Restriction.NO_WARRANTY},
        attribution_required=True,
        modification_allowed=False
    ),
    
    # ===== Public Domain =====
    'Unlicense': License(
        id='Unlicense',
        name='The Unlicense',
        family=LicenseFamily.PUBLIC_DOMAIN,
        url='https://unlicense.org/',
        restrictions=set(),
        attribution_required=False
    ),
    
    # ===== Other Notable Licenses =====
    'ISC': License(
        id='ISC',
        name='ISC License',
        family=LicenseFamily.PERMISSIVE,
        url='https://opensource.org/licenses/ISC',
        restrictions={Restriction.ATTRIBUTION_REQUIRED, Restriction.NO_WARRANTY},
        attribution_required=True
    ),
    
    'Artistic-2.0': License(
        id='Artistic-2.0',
        name='Artistic License 2.0',
        family=LicenseFamily.PERMISSIVE,
        version='2.0',
        url='https://opensource.org/licenses/Artistic-2.0',
        restrictions={Restriction.ATTRIBUTION_REQUIRED, Restriction.NO_WARRANTY},
        attribution_required=True
    ),
}


# ============================================================================
# License Manager
# ============================================================================

class LicenseManager:
    """
    Manages licensing for CAS objects.
    
    Features:
    - Apply licenses to objects
    - Check compatibility between licenses
    - Compute composite licenses for derived objects
    - Track license inheritance
    - Dual/multi-licensing support
    """
    
    def __init__(self, store_root: str = "store"):
        """
        Initialize LicenseManager.
        
        Args:
            store_root: Root directory of the CAS storage
        """
        self.store_root = Path(store_root)
        self.licenses_dir = self.store_root / "licenses"
        self.licenses_dir.mkdir(parents=True, exist_ok=True)
        
        # Load standard licenses
        self.registry = STANDARD_LICENSES.copy()
        
        # Compatibility matrix (will be populated)
        self.compatibility_matrix: Dict[Tuple[str, str], Compatibility] = {}
        self._init_compatibility_matrix()
    
    def _init_compatibility_matrix(self):
        """Initialize license compatibility matrix"""
        # Permissive licenses are compatible with everything
        permissive = ['MIT', 'BSD-2-Clause', 'BSD-3-Clause', 'Apache-2.0', 'ISC']
        
        # Public domain compatible with everything
        public_domain = ['CC0-1.0', 'Unlicense']
        
        # GPL family compatibility
        gpl_family = ['GPL-2.0', 'GPL-3.0', 'AGPL-3.0']
        
        # LGPL family
        lgpl_family = ['LGPL-2.1', 'LGPL-3.0', 'MPL-2.0']
        
        # Creative Commons
        cc_permissive = ['CC-BY-4.0']
        cc_sa = ['CC-BY-SA-4.0']
        
        # Permissive → Permissive (always compatible)
        for lic1 in permissive + public_domain:
            for lic2 in permissive + public_domain:
                self.compatibility_matrix[(lic1, lic2)] = Compatibility.COMPATIBLE
        
        # Permissive → GPL (one-way: can use permissive in GPL, result is GPL)
        for perm in permissive + public_domain:
            for gpl in gpl_family:
                self.compatibility_matrix[(perm, gpl)] = Compatibility.ONE_WAY
                self.compatibility_matrix[(gpl, perm)] = Compatibility.ONE_WAY
        
        # GPL → GPL (same version compatible, cross-version conditional)
        for gpl1 in gpl_family:
            for gpl2 in gpl_family:
                if gpl1 == gpl2:
                    self.compatibility_matrix[(gpl1, gpl2)] = Compatibility.COMPATIBLE
                else:
                    self.compatibility_matrix[(gpl1, gpl2)] = Compatibility.CONDITIONAL
        
        # Permissive → LGPL (compatible)
        for perm in permissive + public_domain:
            for lgpl in lgpl_family:
                self.compatibility_matrix[(perm, lgpl)] = Compatibility.COMPATIBLE
                self.compatibility_matrix[(lgpl, perm)] = Compatibility.COMPATIBLE
        
        # CC-BY with permissive (compatible)
        for perm in permissive + public_domain:
            for cc in cc_permissive:
                self.compatibility_matrix[(perm, cc)] = Compatibility.COMPATIBLE
                self.compatibility_matrix[(cc, perm)] = Compatibility.COMPATIBLE
        
        # ShareAlike incompatibilities
        self.compatibility_matrix[('CC-BY-SA-4.0', 'MIT')] = Compatibility.INCOMPATIBLE
        self.compatibility_matrix[('GPL-3.0', 'Apache-2.0')] = Compatibility.CONDITIONAL
    
    def register_license(self, license: License):
        """Register a new custom license"""
        self.registry[license.id] = license
    
    def get_license(self, license_id: str) -> Optional[License]:
        """Get license by ID"""
        return self.registry.get(license_id)
    
    def apply_license(
        self,
        object_hash: str,
        license_id: str,
        applied_by: Optional[str] = None,
        secondary_licenses: Optional[List[str]] = None,
        custom_terms: Optional[str] = None
    ) -> ObjectLicense:
        """
        Apply a license to an object.
        
        Args:
            object_hash: Hash of object to license
            license_id: ID of license to apply
            applied_by: Who is applying the license
            secondary_licenses: Additional licenses (for dual-licensing)
            custom_terms: Additional custom terms
        
        Returns:
            ObjectLicense instance
        """
        license = self.get_license(license_id)
        if not license:
            raise ValueError(f"Unknown license: {license_id}")
        
        secondary = []
        if secondary_licenses:
            for sec_id in secondary_licenses:
                sec_lic = self.get_license(sec_id)
                if not sec_lic:
                    raise ValueError(f"Unknown secondary license: {sec_id}")
                secondary.append(sec_lic)
        
        obj_license = ObjectLicense(
            object_hash=object_hash,
            license=license,
            secondary_licenses=secondary,
            applied_by=applied_by,
            custom_terms=custom_terms
        )
        
        # Save to storage
        self._save_license(obj_license)
        return obj_license
    
    def load_license(self, object_hash: str) -> Optional[ObjectLicense]:
        """Load license information for an object"""
        license_path = self._license_path(object_hash)
        if not license_path.exists():
            return None
        
        with open(license_path, 'r') as f:
            data = json.load(f)
        
        return ObjectLicense.from_dict(data)
    
    def check_compatibility(
        self,
        license1_id: str,
        license2_id: str
    ) -> CompatibilityResult:
        """
        Check compatibility between two licenses.
        
        Args:
            license1_id: First license ID
            license2_id: Second license ID
        
        Returns:
            CompatibilityResult with compatibility info and resulting license
        """
        lic1 = self.get_license(license1_id)
        lic2 = self.get_license(license2_id)
        
        if not lic1 or not lic2:
            return CompatibilityResult(
                compatible=False,
                compatibility=Compatibility.INCOMPATIBLE,
                conflicts=["Unknown license"]
            )
        
        # Check compatibility matrix
        key = (license1_id, license2_id)
        compat = self.compatibility_matrix.get(
            key,
            Compatibility.INCOMPATIBLE
        )
        
        conflicts = []
        conditions = []
        recommendations = []
        resulting = None
        
        if compat == Compatibility.COMPATIBLE:
            # Determine resulting license (most restrictive wins)
            resulting = self._most_restrictive(lic1, lic2)
        
        elif compat == Compatibility.ONE_WAY:
            # Resulting license is the copyleft one
            if lic1.copyleft:
                resulting = lic1
                conditions.append(f"Derivative must be under {lic1.id}")
            else:
                resulting = lic2
                conditions.append(f"Derivative must be under {lic2.id}")
        
        elif compat == Compatibility.CONDITIONAL:
            # Check specific conditions
            if 'GPL' in license1_id and 'Apache' in license2_id:
                conditions.append("Apache-2.0 code can be included in GPL-3.0 project")
                conditions.append("Result must be GPL-3.0")
                resulting = lic1 if 'GPL' in license1_id else lic2
            else:
                conflicts.append("Licenses have conflicting terms")
        
        else:  # INCOMPATIBLE
            conflicts.append(f"{license1_id} and {license2_id} cannot be combined")
            
            # Add specific conflict reasons
            if lic1.share_alike and not lic2.share_alike:
                conflicts.append("ShareAlike requirement conflict")
            if lic1.commercial_use != lic2.commercial_use:
                conflicts.append("Commercial use terms differ")
            if lic1.modification_allowed != lic2.modification_allowed:
                conflicts.append("Modification rights differ")
            
            # Recommendations
            recommendations.append("Consider dual-licensing")
            recommendations.append("Separate incompatible components")
            recommendations.append("Use a compatibility layer")
        
        return CompatibilityResult(
            compatible=(compat != Compatibility.INCOMPATIBLE),
            compatibility=compat,
            resulting_license=resulting,
            conflicts=conflicts,
            conditions=conditions,
            recommendations=recommendations
        )
    
    def compute_composite_license(
        self,
        parent_hashes: List[str]
    ) -> CompatibilityResult:
        """
        Compute composite license for object derived from multiple parents.
        
        Args:
            parent_hashes: List of parent object hashes
        
        Returns:
            CompatibilityResult with composite license or conflicts
        """
        if not parent_hashes:
            return CompatibilityResult(
                compatible=True,
                compatibility=Compatibility.COMPATIBLE,
                conflicts=["No parents - any license allowed"]
            )
        
        # Load all parent licenses
        parent_licenses = []
        for parent_hash in parent_hashes:
            obj_lic = self.load_license(parent_hash)
            if obj_lic:
                parent_licenses.append(obj_lic.license)
        
        if not parent_licenses:
            return CompatibilityResult(
                compatible=True,
                compatibility=Compatibility.COMPATIBLE,
                conflicts=["No parent licenses found"]
            )
        
        # Check pairwise compatibility
        if len(parent_licenses) == 1:
            return CompatibilityResult(
                compatible=True,
                compatibility=Compatibility.COMPATIBLE,
                resulting_license=parent_licenses[0]
            )
        
        # Multiple licenses - check all pairs
        result_lic = parent_licenses[0]
        all_compatible = True
        all_conflicts = []
        all_conditions = []
        
        for i in range(len(parent_licenses)):
            for j in range(i + 1, len(parent_licenses)):
                compat = self.check_compatibility(
                    parent_licenses[i].id,
                    parent_licenses[j].id
                )
                
                if not compat.compatible:
                    all_compatible = False
                    all_conflicts.extend(compat.conflicts)
                else:
                    all_conditions.extend(compat.conditions)
                    if compat.resulting_license:
                        # Use most restrictive
                        result_lic = self._most_restrictive(
                            result_lic,
                            compat.resulting_license
                        )
        
        if all_compatible:
            return CompatibilityResult(
                compatible=True,
                compatibility=Compatibility.COMPATIBLE,
                resulting_license=result_lic,
                conditions=all_conditions
            )
        else:
            return CompatibilityResult(
                compatible=False,
                compatibility=Compatibility.INCOMPATIBLE,
                conflicts=all_conflicts,
                recommendations=[
                    "Cannot combine these licenses",
                    "Remove incompatible dependencies",
                    "Obtain dual-licensing from parent authors"
                ]
            )
    
    def _most_restrictive(self, lic1: License, lic2: License) -> License:
        """Return the more restrictive of two licenses"""
        # Scoring system (higher = more restrictive)
        def score(lic: License) -> int:
            s = 0
            if lic.copyleft:
                s += 10
            if lic.share_alike:
                s += 5
            if lic.attribution_required:
                s += 2
            if not lic.commercial_use:
                s += 8
            if not lic.modification_allowed:
                s += 6
            return s
        
        return lic1 if score(lic1) >= score(lic2) else lic2
    
    def _license_path(self, object_hash: str) -> Path:
        """Get path to license file for object"""
        return self.licenses_dir / f"{object_hash}.json"
    
    def _save_license(self, obj_license: ObjectLicense):
        """Save license to storage"""
        path = self._license_path(obj_license.object_hash)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(obj_license.to_dict(), f, indent=2)
    
    def export_to_yaml(self, object_hash: str, output_path: str):
        """Export license to YAML"""
        obj_lic = self.load_license(object_hash)
        if not obj_lic:
            raise ValueError(f"No license found for {object_hash}")
        
        with open(output_path, 'w') as f:
            yaml.dump(obj_lic.to_dict(), f, default_flow_style=False)
    
    def list_licenses(self, family: Optional[LicenseFamily] = None) -> List[License]:
        """List all registered licenses, optionally filtered by family"""
        licenses = list(self.registry.values())
        if family:
            licenses = [lic for lic in licenses if lic.family == family]
        return licenses
    
    def find_compatible_licenses(self, license_id: str) -> List[Tuple[str, Compatibility]]:
        """Find all licenses compatible with given license"""
        results = []
        for other_id in self.registry.keys():
            if other_id == license_id:
                continue
            
            compat = self.check_compatibility(license_id, other_id)
            if compat.compatible:
                results.append((other_id, compat.compatibility))
        
        return results


# ============================================================================
# Utility Functions
# ============================================================================

def create_custom_license(
    license_id: str,
    name: str,
    family: LicenseFamily = LicenseFamily.CUSTOM,
    **kwargs
) -> License:
    """
    Create a custom license.
    
    Args:
        license_id: Unique identifier
        name: Full name
        family: License family
        **kwargs: Additional License attributes
    
    Returns:
        License instance
    """
    return License(id=license_id, name=name, family=family, **kwargs)


if __name__ == "__main__":
    # Demo usage
    manager = LicenseManager()
    
    print("=== License Manager Demo ===\n")
    
    # List permissive licenses
    print("Permissive Licenses:")
    for lic in manager.list_licenses(LicenseFamily.PERMISSIVE):
        print(f"  - {lic.id}: {lic.name}")
    
    print("\n" + "="*50 + "\n")
    
    # Check MIT + GPL compatibility
    print("Checking MIT + GPL-3.0 compatibility:")
    result = manager.check_compatibility('MIT', 'GPL-3.0')
    print(f"  Compatible: {result.compatible}")
    print(f"  Type: {result.compatibility.value}")
    if result.resulting_license:
        print(f"  Result: {result.resulting_license.id}")
    if result.conditions:
        print("  Conditions:")
        for cond in result.conditions:
            print(f"    - {cond}")
