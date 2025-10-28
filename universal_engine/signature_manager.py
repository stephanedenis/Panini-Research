#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Signature Manager - Cryptographic Signature System

Provides:
- Digital signatures for objects
- Certificate chain validation
- Timestamp authority integration
- Signature verification
- Key management

Part of the Intellectual Property (IP) Management System - Phase 6.
"""

import json
import hashlib
import base64
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

# Cryptography support (simplified - production would use real crypto)
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.backends import default_backend
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


# ============================================================================
# Enums
# ============================================================================

class SignatureAlgorithm(Enum):
    """Signature algorithms"""
    RSA_SHA256 = "rsa_sha256"
    RSA_SHA512 = "rsa_sha512"
    ECDSA_SHA256 = "ecdsa_sha256"
    ED25519 = "ed25519"


class SignatureStatus(Enum):
    """Signature verification status"""
    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    UNTRUSTED = "untrusted"
    UNKNOWN = "unknown"


class CertificateStatus(Enum):
    """Certificate status"""
    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class PublicKey:
    """
    Public key information.
    
    Attributes:
        key_id: Unique key identifier
        algorithm: Key algorithm
        key_data: Base64-encoded public key
        created_at: Creation timestamp
        owner: Key owner identity
        metadata: Additional metadata
    """
    key_id: str
    algorithm: SignatureAlgorithm
    key_data: str
    created_at: str
    owner: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'key_id': self.key_id,
            'algorithm': self.algorithm.value,
            'key_data': self.key_data,
            'created_at': self.created_at,
            'owner': self.owner,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PublicKey':
        """Create from dictionary"""
        return cls(
            key_id=data['key_id'],
            algorithm=SignatureAlgorithm(data['algorithm']),
            key_data=data['key_data'],
            created_at=data['created_at'],
            owner=data['owner'],
            metadata=data.get('metadata', {})
        )


@dataclass
class Certificate:
    """
    Digital certificate.
    
    Attributes:
        cert_id: Certificate identifier
        subject: Certificate subject
        issuer: Certificate issuer
        public_key: Associated public key
        valid_from: Validity start date
        valid_until: Validity end date
        status: Certificate status
        serial_number: Certificate serial
        signature: Issuer signature
        chain: Certificate chain (parent cert IDs)
    """
    cert_id: str
    subject: str
    issuer: str
    public_key: PublicKey
    valid_from: str
    valid_until: str
    status: CertificateStatus
    serial_number: str
    signature: str
    chain: List[str] = field(default_factory=list)
    
    def is_valid(self) -> bool:
        """Check if certificate is currently valid"""
        if self.status != CertificateStatus.VALID:
            return False
        
        now = datetime.utcnow()
        valid_from = datetime.fromisoformat(self.valid_from.rstrip('Z'))
        valid_until = datetime.fromisoformat(self.valid_until.rstrip('Z'))
        
        return valid_from <= now <= valid_until
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'cert_id': self.cert_id,
            'subject': self.subject,
            'issuer': self.issuer,
            'public_key': self.public_key.to_dict(),
            'valid_from': self.valid_from,
            'valid_until': self.valid_until,
            'status': self.status.value,
            'serial_number': self.serial_number,
            'signature': self.signature,
            'chain': self.chain
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Certificate':
        """Create from dictionary"""
        return cls(
            cert_id=data['cert_id'],
            subject=data['subject'],
            issuer=data['issuer'],
            public_key=PublicKey.from_dict(data['public_key']),
            valid_from=data['valid_from'],
            valid_until=data['valid_until'],
            status=CertificateStatus(data['status']),
            serial_number=data['serial_number'],
            signature=data['signature'],
            chain=data.get('chain', [])
        )


@dataclass
class Timestamp:
    """
    Trusted timestamp.
    
    Attributes:
        timestamp_id: Unique timestamp ID
        timestamp: ISO 8601 timestamp
        authority: Timestamp authority
        signature: Authority signature
        data_hash: Hash of timestamped data
    """
    timestamp_id: str
    timestamp: str
    authority: str
    signature: str
    data_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp_id': self.timestamp_id,
            'timestamp': self.timestamp,
            'authority': self.authority,
            'signature': self.signature,
            'data_hash': self.data_hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Timestamp':
        """Create from dictionary"""
        return cls(
            timestamp_id=data['timestamp_id'],
            timestamp=data['timestamp'],
            authority=data['authority'],
            signature=data['signature'],
            data_hash=data['data_hash']
        )


@dataclass
class ObjectSignature:
    """
    Digital signature for an object.
    
    Attributes:
        signature_id: Unique signature identifier
        object_hash: Hash of signed object
        object_type: Type of signed object
        signer: Identity of signer
        signed_at: Signature timestamp
        algorithm: Signature algorithm
        signature_data: Base64-encoded signature
        certificate: Signer's certificate
        timestamp: Optional trusted timestamp
        metadata: Additional metadata
    """
    signature_id: str
    object_hash: str
    object_type: str
    signer: str
    signed_at: str
    algorithm: SignatureAlgorithm
    signature_data: str
    certificate: Optional[Certificate] = None
    timestamp: Optional[Timestamp] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'signature_id': self.signature_id,
            'object_hash': self.object_hash,
            'object_type': self.object_type,
            'signer': self.signer,
            'signed_at': self.signed_at,
            'algorithm': self.algorithm.value,
            'signature_data': self.signature_data,
            'certificate': (self.certificate.to_dict()
                          if self.certificate else None),
            'timestamp': (self.timestamp.to_dict()
                        if self.timestamp else None),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ObjectSignature':
        """Create from dictionary"""
        return cls(
            signature_id=data['signature_id'],
            object_hash=data['object_hash'],
            object_type=data['object_type'],
            signer=data['signer'],
            signed_at=data['signed_at'],
            algorithm=SignatureAlgorithm(data['algorithm']),
            signature_data=data['signature_data'],
            certificate=(Certificate.from_dict(data['certificate'])
                        if data.get('certificate') else None),
            timestamp=(Timestamp.from_dict(data['timestamp'])
                      if data.get('timestamp') else None),
            metadata=data.get('metadata', {})
        )


@dataclass
class VerificationResult:
    """
    Signature verification result.
    
    Attributes:
        valid: Whether signature is valid
        status: Verification status
        signature: The signature that was verified
        certificate_valid: Whether certificate is valid
        timestamp_valid: Whether timestamp is valid
        chain_valid: Whether certificate chain is valid
        errors: List of validation errors
        warnings: List of warnings
    """
    valid: bool
    status: SignatureStatus
    signature: ObjectSignature
    certificate_valid: bool = False
    timestamp_valid: bool = False
    chain_valid: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'valid': self.valid,
            'status': self.status.value,
            'signature_id': self.signature.signature_id,
            'certificate_valid': self.certificate_valid,
            'timestamp_valid': self.timestamp_valid,
            'chain_valid': self.chain_valid,
            'errors': self.errors,
            'warnings': self.warnings
        }


# ============================================================================
# Signature Manager
# ============================================================================

class SignatureManager:
    """
    Manages digital signatures for objects.
    
    Provides:
    - Object signing with private keys
    - Signature verification
    - Certificate management
    - Timestamp authority integration
    """
    
    def __init__(self, store_path: Path):
        """
        Initialize signature manager.
        
        Args:
            store_path: Path to CAS store directory
        """
        self.store_path = Path(store_path)
        self.sig_dir = self.store_path / "signatures"
        self.sig_dir.mkdir(parents=True, exist_ok=True)
        
        # Subdirectories
        self.keys_dir = self.sig_dir / "keys"
        self.certs_dir = self.sig_dir / "certificates"
        self.sigs_dir = self.sig_dir / "objects"
        self.timestamps_dir = self.sig_dir / "timestamps"
        
        for dir_path in [self.keys_dir, self.certs_dir,
                         self.sigs_dir, self.timestamps_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def generate_key_pair(
        self,
        owner: str,
        algorithm: SignatureAlgorithm = SignatureAlgorithm.RSA_SHA256
    ) -> Tuple[str, str]:
        """
        Generate key pair (simplified version).
        
        Args:
            owner: Key owner identity
            algorithm: Signature algorithm
        
        Returns:
            Tuple of (key_id, public_key_data)
        """
        # Simplified: In production, use real cryptography
        key_id = hashlib.sha256(
            f"{owner}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Mock public key
        public_key_data = base64.b64encode(
            f"PUBLIC_KEY_{key_id}".encode()
        ).decode()
        
        public_key = PublicKey(
            key_id=key_id,
            algorithm=algorithm,
            key_data=public_key_data,
            created_at=datetime.utcnow().isoformat() + 'Z',
            owner=owner
        )
        
        # Save public key
        key_path = self.keys_dir / f"{key_id}.json"
        with open(key_path, 'w') as f:
            json.dump(public_key.to_dict(), f, indent=2)
        
        return key_id, public_key_data
    
    def create_certificate(
        self,
        subject: str,
        key_id: str,
        issuer: str = "self-signed",
        valid_days: int = 365,
        parent_cert_id: Optional[str] = None
    ) -> Certificate:
        """
        Create digital certificate.
        
        Args:
            subject: Certificate subject
            key_id: Public key ID
            issuer: Certificate issuer
            valid_days: Validity period in days
            parent_cert_id: Parent certificate ID (for chain)
        
        Returns:
            Certificate
        """
        # Load public key
        key_path = self.keys_dir / f"{key_id}.json"
        with open(key_path) as f:
            public_key = PublicKey.from_dict(json.load(f))
        
        # Generate certificate
        now = datetime.utcnow()
        valid_until = now + timedelta(days=valid_days)
        
        serial = hashlib.sha256(
            f"{subject}{now.isoformat()}".encode()
        ).hexdigest()[:16]
        
        cert_id = hashlib.sha256(
            f"{subject}{issuer}{serial}".encode()
        ).hexdigest()[:16]
        
        # Build chain
        chain = []
        if parent_cert_id:
            parent_path = self.certs_dir / f"{parent_cert_id}.json"
            if parent_path.exists():
                with open(parent_path) as f:
                    parent = Certificate.from_dict(json.load(f))
                chain = [parent_cert_id] + parent.chain
        
        # Create signature (simplified)
        cert_data = f"{subject}{issuer}{serial}{now.isoformat()}"
        signature = hashlib.sha256(cert_data.encode()).hexdigest()
        
        certificate = Certificate(
            cert_id=cert_id,
            subject=subject,
            issuer=issuer,
            public_key=public_key,
            valid_from=now.isoformat() + 'Z',
            valid_until=valid_until.isoformat() + 'Z',
            status=CertificateStatus.VALID,
            serial_number=serial,
            signature=signature,
            chain=chain
        )
        
        # Save certificate
        cert_path = self.certs_dir / f"{cert_id}.json"
        with open(cert_path, 'w') as f:
            json.dump(certificate.to_dict(), f, indent=2)
        
        return certificate
    
    def sign_object(
        self,
        object_hash: str,
        object_type: str,
        signer: str,
        key_id: str,
        cert_id: Optional[str] = None,
        add_timestamp: bool = False
    ) -> ObjectSignature:
        """
        Sign an object.
        
        Args:
            object_hash: Hash of object to sign
            object_type: Type of object
            signer: Identity of signer
            key_id: Private key ID (simplified)
            cert_id: Certificate ID
            add_timestamp: Add trusted timestamp
        
        Returns:
            ObjectSignature
        """
        now = datetime.utcnow().isoformat() + 'Z'
        
        # Load certificate if provided
        certificate = None
        if cert_id:
            cert_path = self.certs_dir / f"{cert_id}.json"
            if cert_path.exists():
                with open(cert_path) as f:
                    certificate = Certificate.from_dict(json.load(f))
        
        # Generate signature (simplified)
        sig_input = f"{object_hash}{object_type}{signer}{now}"
        signature_data = hashlib.sha256(sig_input.encode()).hexdigest()
        signature_data_b64 = base64.b64encode(
            signature_data.encode()
        ).decode()
        
        sig_id = hashlib.sha256(
            f"{object_hash}{signer}{now}".encode()
        ).hexdigest()[:16]
        
        # Create timestamp if requested
        timestamp = None
        if add_timestamp:
            timestamp = self._create_timestamp(object_hash, signature_data)
        
        signature = ObjectSignature(
            signature_id=sig_id,
            object_hash=object_hash,
            object_type=object_type,
            signer=signer,
            signed_at=now,
            algorithm=SignatureAlgorithm.RSA_SHA256,
            signature_data=signature_data_b64,
            certificate=certificate,
            timestamp=timestamp
        )
        
        # Save signature
        sig_path = self.sigs_dir / f"{object_hash}_{sig_id}.json"
        with open(sig_path, 'w') as f:
            json.dump(signature.to_dict(), f, indent=2)
        
        return signature
    
    def _create_timestamp(
        self,
        data_hash: str,
        signature: str
    ) -> Timestamp:
        """Create trusted timestamp"""
        now = datetime.utcnow().isoformat() + 'Z'
        
        ts_id = hashlib.sha256(
            f"{data_hash}{now}".encode()
        ).hexdigest()[:16]
        
        # TSA signature (simplified)
        ts_data = f"{data_hash}{now}{signature}"
        ts_signature = hashlib.sha256(ts_data.encode()).hexdigest()
        
        timestamp = Timestamp(
            timestamp_id=ts_id,
            timestamp=now,
            authority="CAS-TSA",
            signature=ts_signature,
            data_hash=data_hash
        )
        
        # Save timestamp
        ts_path = self.timestamps_dir / f"{ts_id}.json"
        with open(ts_path, 'w') as f:
            json.dump(timestamp.to_dict(), f, indent=2)
        
        return timestamp
    
    def verify_signature(
        self,
        signature: ObjectSignature,
        verify_chain: bool = True
    ) -> VerificationResult:
        """
        Verify object signature.
        
        Args:
            signature: Signature to verify
            verify_chain: Whether to verify certificate chain
        
        Returns:
            VerificationResult
        """
        errors = []
        warnings = []
        
        # Basic signature validation (simplified)
        sig_input = (f"{signature.object_hash}{signature.object_type}"
                    f"{signature.signer}{signature.signed_at}")
        expected_sig = hashlib.sha256(sig_input.encode()).hexdigest()
        
        signature_data = base64.b64decode(
            signature.signature_data
        ).decode()
        
        valid = signature_data == expected_sig
        
        if not valid:
            errors.append("Signature data mismatch")
        
        # Verify certificate
        cert_valid = False
        if signature.certificate:
            cert_valid = signature.certificate.is_valid()
            if not cert_valid:
                errors.append("Certificate expired or invalid")
        else:
            warnings.append("No certificate provided")
        
        # Verify timestamp
        ts_valid = False
        if signature.timestamp:
            ts_valid = self._verify_timestamp(signature.timestamp)
            if not ts_valid:
                warnings.append("Timestamp verification failed")
        
        # Verify certificate chain
        chain_valid = False
        if verify_chain and signature.certificate:
            chain_valid = self._verify_certificate_chain(
                signature.certificate
            )
            if not chain_valid:
                warnings.append("Certificate chain incomplete")
        
        # Determine status
        if valid and cert_valid:
            status = SignatureStatus.VALID
        elif not cert_valid:
            status = SignatureStatus.UNTRUSTED
        else:
            status = SignatureStatus.INVALID
        
        return VerificationResult(
            valid=valid and cert_valid,
            status=status,
            signature=signature,
            certificate_valid=cert_valid,
            timestamp_valid=ts_valid,
            chain_valid=chain_valid,
            errors=errors,
            warnings=warnings
        )
    
    def _verify_timestamp(self, timestamp: Timestamp) -> bool:
        """Verify timestamp (simplified)"""
        # In production: verify against TSA
        ts_path = self.timestamps_dir / f"{timestamp.timestamp_id}.json"
        return ts_path.exists()
    
    def _verify_certificate_chain(self, certificate: Certificate) -> bool:
        """Verify certificate chain"""
        if not certificate.chain:
            return True  # Self-signed or root
        
        # Verify each certificate in chain exists
        for cert_id in certificate.chain:
            cert_path = self.certs_dir / f"{cert_id}.json"
            if not cert_path.exists():
                return False
        
        return True
    
    def get_signatures(self, object_hash: str) -> List[ObjectSignature]:
        """
        Get all signatures for object.
        
        Args:
            object_hash: Object hash
        
        Returns:
            List of signatures
        """
        signatures = []
        
        for sig_file in self.sigs_dir.glob(f"{object_hash}_*.json"):
            with open(sig_file) as f:
                sig = ObjectSignature.from_dict(json.load(f))
                signatures.append(sig)
        
        return signatures
    
    def revoke_certificate(self, cert_id: str, reason: str = "") -> bool:
        """
        Revoke certificate.
        
        Args:
            cert_id: Certificate ID
            reason: Revocation reason
        
        Returns:
            True if revoked
        """
        cert_path = self.certs_dir / f"{cert_id}.json"
        
        if not cert_path.exists():
            return False
        
        with open(cert_path) as f:
            cert_data = json.load(f)
        
        cert_data['status'] = CertificateStatus.REVOKED.value
        cert_data['metadata'] = cert_data.get('metadata', {})
        cert_data['metadata']['revocation_reason'] = reason
        cert_data['metadata']['revoked_at'] = (
            datetime.utcnow().isoformat() + 'Z'
        )
        
        with open(cert_path, 'w') as f:
            json.dump(cert_data, f, indent=2)
        
        return True


# ============================================================================
# Utility Functions
# ============================================================================

def verify_object_authenticity(
    sig_manager: SignatureManager,
    object_hash: str
) -> Tuple[bool, List[VerificationResult]]:
    """
    Verify object authenticity using all signatures.
    
    Args:
        sig_manager: SignatureManager instance
        object_hash: Object hash to verify
    
    Returns:
        Tuple of (any_valid, all_results)
    """
    signatures = sig_manager.get_signatures(object_hash)
    
    if not signatures:
        return False, []
    
    results = []
    any_valid = False
    
    for sig in signatures:
        result = sig_manager.verify_signature(sig)
        results.append(result)
        if result.valid:
            any_valid = True
    
    return any_valid, results


if __name__ == '__main__':
    # Demo usage
    print("Signature Manager Demo")
    print("=" * 60)
    
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        sig_mgr = SignatureManager(tmpdir)
        
        # Generate key pair
        print("\n[1] Generating key pair...")
        key_id, pub_key = sig_mgr.generate_key_pair("alice@example.com")
        print(f"  ✓ Key ID: {key_id}")
        
        # Create certificate
        print("\n[2] Creating certificate...")
        cert = sig_mgr.create_certificate(
            subject="alice@example.com",
            key_id=key_id,
            valid_days=365
        )
        print(f"  ✓ Certificate ID: {cert.cert_id}")
        print(f"  ✓ Valid until: {cert.valid_until}")
        
        # Sign object
        print("\n[3] Signing object...")
        signature = sig_mgr.sign_object(
            object_hash="pattern_001",
            object_type="pattern",
            signer="alice@example.com",
            key_id=key_id,
            cert_id=cert.cert_id,
            add_timestamp=True
        )
        print(f"  ✓ Signature ID: {signature.signature_id}")
        print(f"  ✓ Signed at: {signature.signed_at}")
        print(f"  ✓ Timestamp: {signature.timestamp is not None}")
        
        # Verify signature
        print("\n[4] Verifying signature...")
        result = sig_mgr.verify_signature(signature)
        print(f"  ✓ Valid: {result.valid}")
        print(f"  ✓ Status: {result.status.value}")
        print(f"  ✓ Certificate valid: {result.certificate_valid}")
        print(f"  ✓ Timestamp valid: {result.timestamp_valid}")
        
        print("\n" + "=" * 60)
        print("✅ Signature Manager operational")
