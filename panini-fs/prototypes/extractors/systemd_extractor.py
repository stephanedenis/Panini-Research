#!/usr/bin/env python3
"""
Systemd Unit File Format Extractor - PaniniFS v3.37

This extractor analyzes systemd unit files (.service, .timer, .target, .socket, etc.).
These files define system services, timers, targets, and other systemd units.

Format Structure:
- INI-like format with [Section] groups
- Key=Value pairs (no locale support unlike desktop files)
- Comments start with # or ;
- Continuation lines: backslash at end or indentation
- Section order matters for systemd

Common Sections:
- [Unit]: Generic unit information (Description, Documentation, Requires, After, etc.)
- [Service]: Service-specific configuration (Type, ExecStart, Restart, etc.)
- [Timer]: Timer-specific configuration (OnBootSec, OnUnitActiveSec, etc.)
- [Socket]: Socket-specific configuration (ListenStream, Accept, etc.)
- [Install]: Installation information (WantedBy, RequiredBy, Alias, etc.)

Unit Section Keys:
- Description: Human-readable description
- Documentation: URLs to documentation (man:, http:, file:)
- Requires/Wants: Dependencies
- After/Before: Ordering dependencies
- ConditionPathExists: Conditional activation

Service Section Keys:
- Type: oneshot, forking, simple, notify, dbus, idle
- ExecStart/ExecStop/ExecReload: Commands
- Restart: no, on-failure, always, on-abnormal, on-abort, on-watchdog
- User/Group: Process credentials
- WorkingDirectory: Working directory
- Environment/EnvironmentFile: Environment variables
- StandardInput/Output/Error: stdio redirection (null, tty, journal, socket)

Install Section Keys:
- WantedBy: Target units that want this unit
- RequiredBy: Target units that require this unit
- Alias: Alternative names

Specifiers:
- %i: Instance name (from template@instance.service)
- %n: Unit name
- %p: Prefix name (before @)
- %u: User name
- %h: User home directory

Author: PaniniFS Research Team
Version: 3.37
Target: Systemd units in /run/media/stephane/babba1d2-aea8-4876-ba6c-d47aa6de90d1/
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import re

class SystemdExtractor:
    """Extract metadata from systemd unit files."""
    
    # Unit file types (by extension)
    UNIT_TYPES = {
        ".service": "Service",
        ".timer": "Timer",
        ".target": "Target",
        ".socket": "Socket",
        ".device": "Device",
        ".mount": "Mount",
        ".automount": "Automount",
        ".swap": "Swap",
        ".path": "Path",
        ".slice": "Slice",
        ".scope": "Scope",
    }
    
    # Service types
    SERVICE_TYPES = ["simple", "forking", "oneshot", "dbus", "notify", "idle"]
    
    # Restart policies
    RESTART_POLICIES = [
        "no", "on-success", "on-failure", "on-abnormal", 
        "on-abort", "on-watchdog", "always"
    ]
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        
    def extract(self) -> Dict[str, Any]:
        """Extract all metadata from the systemd unit file."""
        try:
            # Read file with UTF-8 encoding
            with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            metadata = {
                "format": "Systemd Unit File",
                "file_path": str(self.file_path),
                "file_size": len(content),
            }
            
            # Detect unit type from extension
            unit_type = None
            for ext, type_name in self.UNIT_TYPES.items():
                if self.file_path.name.endswith(ext):
                    unit_type = type_name
                    break
            
            if unit_type:
                metadata["unit_type"] = unit_type
            
            # Check if template unit (contains @)
            if '@' in self.file_path.name:
                metadata["is_template"] = True
                # Extract template name (before @)
                template_match = re.match(r'^(.+)@', self.file_path.name)
                if template_match:
                    metadata["template_name"] = template_match.group(1)
            
            # Parse sections
            sections = self._parse_sections(content)
            
            # Extract [Unit] section
            if "Unit" in sections:
                metadata["unit"] = self._parse_unit_section(sections["Unit"])
            
            # Extract type-specific sections
            if "Service" in sections and unit_type == "Service":
                metadata["service"] = self._parse_service_section(sections["Service"])
            
            if "Timer" in sections and unit_type == "Timer":
                metadata["timer"] = self._parse_timer_section(sections["Timer"])
            
            if "Socket" in sections and unit_type == "Socket":
                metadata["socket"] = self._parse_socket_section(sections["Socket"])
            
            if "Mount" in sections and unit_type == "Mount":
                metadata["mount"] = self._parse_mount_section(sections["Mount"])
            
            # Extract [Install] section
            if "Install" in sections:
                metadata["install"] = self._parse_install_section(sections["Install"])
            
            # Other sections
            other_sections = [k for k in sections.keys() 
                            if k not in ["Unit", "Service", "Timer", "Socket", "Mount", "Install"]]
            if other_sections:
                metadata["other_sections"] = other_sections
            
            return metadata
            
        except Exception as e:
            return {
                "format": "Systemd Unit File",
                "file_path": str(self.file_path),
                "error": str(e)
            }
    
    def _parse_sections(self, content: str) -> Dict[str, Dict[str, List[str]]]:
        """Parse INI-like sections and key-value pairs."""
        sections = {}
        current_section = None
        current_data = {}
        
        for line in content.split('\n'):
            # Strip whitespace
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#') or line.startswith(';'):
                continue
            
            # Section header
            if line.startswith('[') and line.endswith(']'):
                # Save previous section
                if current_section:
                    sections[current_section] = current_data
                
                # Start new section
                current_section = line[1:-1]
                current_data = {}
                continue
            
            # Key-value pair
            if '=' in line and current_section:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Allow multiple values for same key (e.g., ExecStart)
                if key in current_data:
                    if isinstance(current_data[key], list):
                        current_data[key].append(value)
                    else:
                        current_data[key] = [current_data[key], value]
                else:
                    current_data[key] = value
        
        # Save last section
        if current_section:
            sections[current_section] = current_data
        
        return sections
    
    def _get_value(self, data: Dict[str, Any], key: str) -> Optional[str]:
        """Get single value from parsed data."""
        if key not in data:
            return None
        value = data[key]
        if isinstance(value, list):
            return value[0]  # Return first value
        return value
    
    def _get_values(self, data: Dict[str, Any], key: str) -> Optional[List[str]]:
        """Get all values for a key (returns list)."""
        if key not in data:
            return None
        value = data[key]
        if isinstance(value, list):
            return value
        return [value]
    
    def _parse_unit_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse [Unit] section."""
        result = {}
        
        # Description
        description = self._get_value(data, "Description")
        if description:
            result["description"] = description
        
        # Documentation
        documentation = self._get_values(data, "Documentation")
        if documentation:
            result["documentation"] = documentation
        
        # Dependencies
        requires = self._get_values(data, "Requires")
        if requires:
            result["requires"] = requires
        
        wants = self._get_values(data, "Wants")
        if wants:
            result["wants"] = wants
        
        # Ordering
        after = self._get_values(data, "After")
        if after:
            result["after"] = after
        
        before = self._get_values(data, "Before")
        if before:
            result["before"] = before
        
        # Conditions
        conditions = {}
        for key in data.keys():
            if key.startswith("Condition"):
                value = self._get_value(data, key)
                if value:
                    conditions[key] = value
        if conditions:
            result["conditions"] = conditions
        
        # DefaultDependencies
        default_deps = self._get_value(data, "DefaultDependencies")
        if default_deps:
            result["default_dependencies"] = default_deps.lower() == "yes"
        
        return result
    
    def _parse_service_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse [Service] section."""
        result = {}
        
        # Type
        service_type = self._get_value(data, "Type")
        if service_type:
            result["type"] = service_type
        
        # Exec commands (can have multiple)
        exec_start = self._get_values(data, "ExecStart")
        if exec_start:
            result["exec_start"] = exec_start
            
            # Detect specifiers
            all_execs = ' '.join(exec_start)
            specifiers = re.findall(r'%[inpuhstmHbvwaALdCfgGojNwWTUSERVEzZ]', all_execs)
            if specifiers:
                result["specifiers"] = list(set(specifiers))
        
        exec_stop = self._get_values(data, "ExecStop")
        if exec_stop:
            result["exec_stop"] = exec_stop
        
        exec_reload = self._get_values(data, "ExecReload")
        if exec_reload:
            result["exec_reload"] = exec_reload
        
        # Restart
        restart = self._get_value(data, "Restart")
        if restart:
            result["restart"] = restart
        
        # User/Group
        user = self._get_value(data, "User")
        if user:
            result["user"] = user
        
        group = self._get_value(data, "Group")
        if group:
            result["group"] = group
        
        # WorkingDirectory
        working_directory = self._get_value(data, "WorkingDirectory")
        if working_directory:
            result["working_directory"] = working_directory
        
        # Environment
        environment = self._get_values(data, "Environment")
        if environment:
            result["environment"] = environment
        
        environment_file = self._get_values(data, "EnvironmentFile")
        if environment_file:
            result["environment_file"] = environment_file
        
        # StandardInput/Output/Error
        std_input = self._get_value(data, "StandardInput")
        if std_input:
            result["standard_input"] = std_input
        
        std_output = self._get_value(data, "StandardOutput")
        if std_output:
            result["standard_output"] = std_output
        
        std_error = self._get_value(data, "StandardError")
        if std_error:
            result["standard_error"] = std_error
        
        return result
    
    def _parse_timer_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse [Timer] section."""
        result = {}
        
        # Timer triggers
        on_boot_sec = self._get_value(data, "OnBootSec")
        if on_boot_sec:
            result["on_boot_sec"] = on_boot_sec
        
        on_startup_sec = self._get_value(data, "OnStartupSec")
        if on_startup_sec:
            result["on_startup_sec"] = on_startup_sec
        
        on_unit_active_sec = self._get_value(data, "OnUnitActiveSec")
        if on_unit_active_sec:
            result["on_unit_active_sec"] = on_unit_active_sec
        
        on_unit_inactive_sec = self._get_value(data, "OnUnitInactiveSec")
        if on_unit_inactive_sec:
            result["on_unit_inactive_sec"] = on_unit_inactive_sec
        
        on_calendar = self._get_value(data, "OnCalendar")
        if on_calendar:
            result["on_calendar"] = on_calendar
        
        # Unit to activate
        unit = self._get_value(data, "Unit")
        if unit:
            result["unit"] = unit
        
        return result
    
    def _parse_socket_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse [Socket] section."""
        result = {}
        
        # Listen addresses
        listen_stream = self._get_values(data, "ListenStream")
        if listen_stream:
            result["listen_stream"] = listen_stream
        
        listen_datagram = self._get_values(data, "ListenDatagram")
        if listen_datagram:
            result["listen_datagram"] = listen_datagram
        
        # Accept
        accept = self._get_value(data, "Accept")
        if accept:
            result["accept"] = accept.lower() == "yes"
        
        return result
    
    def _parse_mount_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse [Mount] section."""
        result = {}
        
        # What/Where/Type
        what = self._get_value(data, "What")
        if what:
            result["what"] = what
        
        where = self._get_value(data, "Where")
        if where:
            result["where"] = where
        
        fs_type = self._get_value(data, "Type")
        if fs_type:
            result["type"] = fs_type
        
        return result
    
    def _parse_install_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse [Install] section."""
        result = {}
        
        # WantedBy
        wanted_by = self._get_values(data, "WantedBy")
        if wanted_by:
            result["wanted_by"] = wanted_by
        
        # RequiredBy
        required_by = self._get_values(data, "RequiredBy")
        if required_by:
            result["required_by"] = required_by
        
        # Alias
        alias = self._get_values(data, "Alias")
        if alias:
            result["alias"] = alias
        
        return result

def main():
    if len(sys.argv) < 2:
        print("Usage: systemd_extractor.py <unit_file>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    extractor = SystemdExtractor(file_path)
    metadata = extractor.extract()
    
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
