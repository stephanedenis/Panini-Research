#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit Trail Manager - Immutable Audit Logging System

Provides:
- Immutable audit logs for all operations
- Event tracking (read, write, delete, access attempts)
- Compliance reporting
- Temporal queries and forensics
- Chain-of-custody verification

Part of the Intellectual Property (IP) Management System - Phase 5.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field


# ============================================================================
# Enums
# ============================================================================

class AuditEventType(Enum):
    """Types of audit events"""
    # Object operations
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    
    # Derivation operations
    DERIVE = "derive"
    FORK = "fork"
    MERGE = "merge"
    
    # IP operations
    LICENSE_APPLY = "license_apply"
    LICENSE_CHANGE = "license_change"
    ATTRIBUTION_ADD = "attribution_add"
    ATTRIBUTION_UPDATE = "attribution_update"
    
    # Access control
    ACCESS_GRANT = "access_grant"
    ACCESS_REVOKE = "access_revoke"
    ACCESS_DENIED = "access_denied"
    ACCESS_ATTEMPT = "access_attempt"
    
    # System operations
    EXPORT = "export"
    IMPORT = "import"
    BACKUP = "backup"
    RESTORE = "restore"
    
    # Governance
    VOTE_CAST = "vote_cast"
    REPUTATION_CHANGE = "reputation_change"


class AuditSeverity(Enum):
    """Severity levels for audit events"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SECURITY = "security"


class AuditOutcome(Enum):
    """Outcome of audited operation"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    DENIED = "denied"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class AuditEvent:
    """
    Single audit event entry.
    
    Attributes:
        event_id: Unique event identifier (hash)
        timestamp: ISO 8601 timestamp
        event_type: Type of event
        actor: User/system performing action
        object_hash: Hash of affected object (if applicable)
        object_type: Type of affected object
        action: Human-readable action description
        outcome: Success/failure/denied
        severity: Event severity level
        details: Additional event details
        metadata: Extra metadata (IP, client, etc.)
        previous_hash: Hash of previous event (for chain integrity)
    """
    event_id: str
    timestamp: str
    event_type: AuditEventType
    actor: str
    object_hash: Optional[str] = None
    object_type: Optional[str] = None
    action: str = ""
    outcome: AuditOutcome = AuditOutcome.SUCCESS
    severity: AuditSeverity = AuditSeverity.INFO
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    previous_hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp,
            'event_type': self.event_type.value,
            'actor': self.actor,
            'object_hash': self.object_hash,
            'object_type': self.object_type,
            'action': self.action,
            'outcome': self.outcome.value,
            'severity': self.severity.value,
            'details': self.details,
            'metadata': self.metadata,
            'previous_hash': self.previous_hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEvent':
        """Create from dictionary"""
        return cls(
            event_id=data['event_id'],
            timestamp=data['timestamp'],
            event_type=AuditEventType(data['event_type']),
            actor=data['actor'],
            object_hash=data.get('object_hash'),
            object_type=data.get('object_type'),
            action=data.get('action', ''),
            outcome=AuditOutcome(data['outcome']),
            severity=AuditSeverity(data['severity']),
            details=data.get('details', {}),
            metadata=data.get('metadata', {}),
            previous_hash=data.get('previous_hash')
        )
    
    def compute_hash(self) -> str:
        """Compute hash of event for chain integrity"""
        event_data = {
            'timestamp': self.timestamp,
            'event_type': self.event_type.value,
            'actor': self.actor,
            'object_hash': self.object_hash,
            'action': self.action,
            'outcome': self.outcome.value,
            'previous_hash': self.previous_hash
        }
        event_str = json.dumps(event_data, sort_keys=True)
        return hashlib.sha256(event_str.encode()).hexdigest()[:16]


@dataclass
class AuditChain:
    """
    Chain of audit events for integrity verification.
    
    Attributes:
        chain_id: Unique chain identifier
        start_time: Chain start timestamp
        events: List of audit events
        verified: Whether chain integrity is verified
    """
    chain_id: str
    start_time: str
    events: List[AuditEvent] = field(default_factory=list)
    verified: bool = False
    
    def add_event(self, event: AuditEvent) -> None:
        """Add event to chain and link to previous"""
        if self.events:
            event.previous_hash = self.events[-1].event_id
        self.events.append(event)
    
    def verify_integrity(self) -> bool:
        """Verify chain integrity"""
        for i, event in enumerate(self.events):
            if i == 0:
                if event.previous_hash is not None:
                    return False
            else:
                prev_event = self.events[i - 1]
                if event.previous_hash != prev_event.event_id:
                    return False
            
            # Verify event hash
            computed = event.compute_hash()
            if computed != event.event_id:
                return False
        
        self.verified = True
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'chain_id': self.chain_id,
            'start_time': self.start_time,
            'events': [e.to_dict() for e in self.events],
            'verified': self.verified
        }


@dataclass
class ComplianceReport:
    """
    Compliance audit report.
    
    Attributes:
        report_id: Unique report identifier
        generated_at: Generation timestamp
        period_start: Report period start
        period_end: Report period end
        total_events: Total events in period
        events_by_type: Count by event type
        events_by_actor: Count by actor
        security_events: Count of security events
        failures: Count of failures
        violations: List of potential violations
    """
    report_id: str
    generated_at: str
    period_start: str
    period_end: str
    total_events: int
    events_by_type: Dict[str, int] = field(default_factory=dict)
    events_by_actor: Dict[str, int] = field(default_factory=dict)
    security_events: int = 0
    failures: int = 0
    violations: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'report_id': self.report_id,
            'generated_at': self.generated_at,
            'period_start': self.period_start,
            'period_end': self.period_end,
            'total_events': self.total_events,
            'events_by_type': self.events_by_type,
            'events_by_actor': self.events_by_actor,
            'security_events': self.security_events,
            'failures': self.failures,
            'violations': self.violations
        }


# ============================================================================
# Audit Manager
# ============================================================================

class AuditManager:
    """
    Manages immutable audit trail for all system operations.
    
    Provides:
    - Event logging with chain integrity
    - Temporal queries
    - Compliance reporting
    - Forensic analysis
    """
    
    def __init__(self, store_path: Path):
        """
        Initialize audit manager.
        
        Args:
            store_path: Path to CAS store directory
        """
        self.store_path = Path(store_path)
        self.audit_dir = self.store_path / "audit"
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        
        # Index directories
        self.by_date_dir = self.audit_dir / "by_date"
        self.by_actor_dir = self.audit_dir / "by_actor"
        self.by_object_dir = self.audit_dir / "by_object"
        self.chains_dir = self.audit_dir / "chains"
        
        for dir_path in [self.by_date_dir, self.by_actor_dir,
                         self.by_object_dir, self.chains_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Current chain
        self.current_chain = self._load_or_create_chain()
    
    def _load_or_create_chain(self) -> AuditChain:
        """Load current chain or create new one"""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        chain_id = f"chain_{today}"
        chain_path = self.chains_dir / f"{chain_id}.json"
        
        if chain_path.exists():
            with open(chain_path) as f:
                data = json.load(f)
            chain = AuditChain(
                chain_id=data['chain_id'],
                start_time=data['start_time'],
                events=[AuditEvent.from_dict(e) for e in data['events']],
                verified=data.get('verified', False)
            )
        else:
            chain = AuditChain(
                chain_id=chain_id,
                start_time=datetime.utcnow().isoformat() + 'Z'
            )
        
        return chain
    
    def _save_chain(self) -> None:
        """Save current chain"""
        chain_path = self.chains_dir / f"{self.current_chain.chain_id}.json"
        with open(chain_path, 'w') as f:
            json.dump(self.current_chain.to_dict(), f, indent=2)
    
    def log_event(
        self,
        event_type: AuditEventType,
        actor: str,
        action: str,
        object_hash: Optional[str] = None,
        object_type: Optional[str] = None,
        outcome: AuditOutcome = AuditOutcome.SUCCESS,
        severity: AuditSeverity = AuditSeverity.INFO,
        details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """
        Log audit event.
        
        Args:
            event_type: Type of event
            actor: User/system performing action
            action: Human-readable description
            object_hash: Hash of affected object
            object_type: Type of affected object
            outcome: Operation outcome
            severity: Event severity
            details: Additional details
            metadata: Extra metadata
        
        Returns:
            Created AuditEvent
        """
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Create event
        event = AuditEvent(
            event_id="",  # Will be computed
            timestamp=timestamp,
            event_type=event_type,
            actor=actor,
            object_hash=object_hash,
            object_type=object_type,
            action=action,
            outcome=outcome,
            severity=severity,
            details=details or {},
            metadata=metadata or {}
        )
        
        # Add to chain (sets previous_hash)
        self.current_chain.add_event(event)
        
        # Compute and set event ID
        event.event_id = event.compute_hash()
        
        # Save event to daily log
        self._save_event_to_daily_log(event)
        
        # Update indexes
        self._index_event(event)
        
        # Save chain
        self._save_chain()
        
        return event
    
    def _save_event_to_daily_log(self, event: AuditEvent) -> None:
        """Save event to daily log file"""
        date = event.timestamp[:10]  # YYYY-MM-DD
        log_path = self.by_date_dir / f"{date}.jsonl"
        
        with open(log_path, 'a') as f:
            f.write(json.dumps(event.to_dict()) + '\n')
    
    def _index_event(self, event: AuditEvent) -> None:
        """Index event for fast lookup"""
        # Index by actor
        actor_path = self.by_actor_dir / f"{event.actor}.jsonl"
        with open(actor_path, 'a') as f:
            f.write(json.dumps({
                'event_id': event.event_id,
                'timestamp': event.timestamp,
                'event_type': event.event_type.value
            }) + '\n')
        
        # Index by object
        if event.object_hash:
            obj_path = self.by_object_dir / f"{event.object_hash}.jsonl"
            with open(obj_path, 'a') as f:
                f.write(json.dumps({
                    'event_id': event.event_id,
                    'timestamp': event.timestamp,
                    'event_type': event.event_type.value,
                    'actor': event.actor
                }) + '\n')
    
    def get_events_by_date(
        self,
        date: str
    ) -> List[AuditEvent]:
        """
        Get all events for a specific date.
        
        Args:
            date: Date in YYYY-MM-DD format
        
        Returns:
            List of audit events
        """
        log_path = self.by_date_dir / f"{date}.jsonl"
        
        if not log_path.exists():
            return []
        
        events = []
        with open(log_path) as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    events.append(AuditEvent.from_dict(data))
        
        return events
    
    def get_events_by_actor(
        self,
        actor: str,
        limit: Optional[int] = None
    ) -> List[AuditEvent]:
        """
        Get events by actor.
        
        Args:
            actor: Actor identifier
            limit: Maximum events to return
        
        Returns:
            List of audit events
        """
        actor_path = self.by_actor_dir / f"{actor}.jsonl"
        
        if not actor_path.exists():
            return []
        
        events = []
        with open(actor_path) as f:
            for line in f:
                if line.strip():
                    index_data = json.loads(line)
                    # Load full event from daily log
                    date = index_data['timestamp'][:10]
                    event = self._find_event_in_log(
                        date, index_data['event_id']
                    )
                    if event:
                        events.append(event)
                        if limit and len(events) >= limit:
                            break
        
        return events
    
    def get_events_by_object(
        self,
        object_hash: str
    ) -> List[AuditEvent]:
        """
        Get all events for specific object.
        
        Args:
            object_hash: Object hash
        
        Returns:
            List of audit events
        """
        obj_path = self.by_object_dir / f"{object_hash}.jsonl"
        
        if not obj_path.exists():
            return []
        
        events = []
        with open(obj_path) as f:
            for line in f:
                if line.strip():
                    index_data = json.loads(line)
                    date = index_data['timestamp'][:10]
                    event = self._find_event_in_log(
                        date, index_data['event_id']
                    )
                    if event:
                        events.append(event)
        
        return events
    
    def _find_event_in_log(
        self,
        date: str,
        event_id: str
    ) -> Optional[AuditEvent]:
        """Find event in daily log"""
        log_path = self.by_date_dir / f"{date}.jsonl"
        
        if not log_path.exists():
            return None
        
        with open(log_path) as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if data['event_id'] == event_id:
                        return AuditEvent.from_dict(data)
        
        return None
    
    def get_events_in_range(
        self,
        start_date: str,
        end_date: str,
        event_type: Optional[AuditEventType] = None
    ) -> List[AuditEvent]:
        """
        Get events in date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            event_type: Filter by event type
        
        Returns:
            List of audit events
        """
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        events = []
        current = start
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            day_events = self.get_events_by_date(date_str)
            
            if event_type:
                day_events = [
                    e for e in day_events if e.event_type == event_type
                ]
            
            events.extend(day_events)
            current += timedelta(days=1)
        
        return events
    
    def verify_chain(self, chain_id: str) -> bool:
        """
        Verify audit chain integrity.
        
        Args:
            chain_id: Chain identifier
        
        Returns:
            True if chain is valid
        """
        chain_path = self.chains_dir / f"{chain_id}.json"
        
        if not chain_path.exists():
            return False
        
        with open(chain_path) as f:
            data = json.load(f)
        
        chain = AuditChain(
            chain_id=data['chain_id'],
            start_time=data['start_time'],
            events=[AuditEvent.from_dict(e) for e in data['events']],
            verified=False
        )
        
        return chain.verify_integrity()
    
    def generate_compliance_report(
        self,
        start_date: str,
        end_date: str
    ) -> ComplianceReport:
        """
        Generate compliance report for date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            ComplianceReport
        """
        events = self.get_events_in_range(start_date, end_date)
        
        report_id = hashlib.sha256(
            f"{start_date}{end_date}{len(events)}".encode()
        ).hexdigest()[:16]
        
        # Analyze events
        events_by_type = {}
        events_by_actor = {}
        security_events = 0
        failures = 0
        violations = []
        
        for event in events:
            # Count by type
            type_key = event.event_type.value
            events_by_type[type_key] = events_by_type.get(type_key, 0) + 1
            
            # Count by actor
            events_by_actor[event.actor] = (
                events_by_actor.get(event.actor, 0) + 1
            )
            
            # Security events
            if event.severity == AuditSeverity.SECURITY:
                security_events += 1
            
            # Failures
            if event.outcome in [AuditOutcome.FAILURE, AuditOutcome.DENIED]:
                failures += 1
                violations.append({
                    'event_id': event.event_id,
                    'timestamp': event.timestamp,
                    'actor': event.actor,
                    'action': event.action,
                    'outcome': event.outcome.value
                })
        
        return ComplianceReport(
            report_id=report_id,
            generated_at=datetime.utcnow().isoformat() + 'Z',
            period_start=start_date,
            period_end=end_date,
            total_events=len(events),
            events_by_type=events_by_type,
            events_by_actor=events_by_actor,
            security_events=security_events,
            failures=failures,
            violations=violations
        )


# ============================================================================
# Utility Functions
# ============================================================================

def create_audit_event(
    event_type: AuditEventType,
    actor: str,
    action: str,
    **kwargs
) -> AuditEvent:
    """
    Convenience function to create audit event.
    
    Args:
        event_type: Type of event
        actor: Actor performing action
        action: Action description
        **kwargs: Additional arguments
    
    Returns:
        AuditEvent instance
    """
    timestamp = datetime.utcnow().isoformat() + 'Z'
    event = AuditEvent(
        event_id="",
        timestamp=timestamp,
        event_type=event_type,
        actor=actor,
        action=action,
        **kwargs
    )
    event.event_id = event.compute_hash()
    return event


if __name__ == '__main__':
    # Demo usage
    print("Audit Manager Demo")
    print("=" * 60)
    
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        audit = AuditManager(tmpdir)
        
        # Log some events
        print("\n[1] Logging events...")
        audit.log_event(
            AuditEventType.CREATE,
            actor="alice@example.com",
            action="Created new phonological pattern",
            object_hash="pattern001",
            object_type="pattern"
        )
        
        audit.log_event(
            AuditEventType.READ,
            actor="bob@example.com",
            action="Read pattern",
            object_hash="pattern001",
            object_type="pattern"
        )
        
        audit.log_event(
            AuditEventType.ACCESS_DENIED,
            actor="charlie@example.com",
            action="Attempted to modify pattern",
            object_hash="pattern001",
            object_type="pattern",
            outcome=AuditOutcome.DENIED,
            severity=AuditSeverity.WARNING
        )
        
        print("  ✓ 3 events logged")
        
        # Query events
        print("\n[2] Querying events...")
        today = datetime.utcnow().strftime("%Y-%m-%d")
        events = audit.get_events_by_date(today)
        print(f"  ✓ Found {len(events)} events today")
        
        # Object history
        print("\n[3] Object history...")
        obj_events = audit.get_events_by_object("pattern001")
        print(f"  ✓ pattern001 has {len(obj_events)} events:")
        for e in obj_events:
            print(f"    - {e.timestamp}: {e.action} by {e.actor}")
        
        # Verify chain
        print("\n[4] Verifying chain integrity...")
        valid = audit.verify_chain(audit.current_chain.chain_id)
        print(f"  ✓ Chain valid: {valid}")
        
        # Compliance report
        print("\n[5] Generating compliance report...")
        report = audit.generate_compliance_report(today, today)
        print(f"  ✓ Report generated:")
        print(f"    - Total events: {report.total_events}")
        print(f"    - Security events: {report.security_events}")
        print(f"    - Failures: {report.failures}")
        
        print("\n" + "=" * 60)
        print("✅ Audit Manager operational")
