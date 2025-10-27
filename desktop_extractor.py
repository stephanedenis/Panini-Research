#!/usr/bin/env python3
"""
Desktop Entry Format Extractor - PaniniFS v3.36

This extractor analyzes .desktop files (freedesktop.org Desktop Entry Specification).
These files define application launchers, links, and directories in Linux desktop environments.

Format Structure:
- INI-like format with [Group] sections
- [Desktop Entry] is the primary section
- Key-value pairs: Key=Value or Key[locale]=Value
- Localized strings use locale codes: Name[fr_FR]=Nom français
- Comments start with #
- Continuation lines: backslash at end

Key Fields:
- Type: Application, Link, Directory
- Name: Display name (localizable)
- GenericName: Generic description
- Comment: Tooltip text
- Icon: Icon name or path
- Exec: Command to execute (with field codes %f %F %u %U)
- Path: Working directory
- Terminal: Run in terminal (true/false)
- Categories: Desktop categories (separated by ;)
- MimeType: Associated MIME types
- StartupNotify: Startup notification support
- NoDisplay: Hidden from menus
- Hidden: Disabled entry
- OnlyShowIn/NotShowIn: Desktop environment filters

Field Codes in Exec:
- %f: Single file
- %F: Multiple files
- %u: Single URL
- %U: Multiple URLs
- %i: Icon with --icon flag
- %c: Translated name
- %k: .desktop file path

Author: PaniniFS Research Team
Version: 3.36
Target: Desktop files in /run/media/stephane/babba1d2-aea8-4876-ba6c-d47aa6de90d1/
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import re

class DesktopExtractor:
    """Extract metadata from freedesktop.org Desktop Entry files."""
    
    # Desktop entry types
    ENTRY_TYPES = ["Application", "Link", "Directory"]
    
    # Boolean keys (parse as true/false)
    BOOLEAN_KEYS = {
        "Terminal", "StartupNotify", "NoDisplay", "Hidden",
        "DBusActivatable", "StartupWMClass", "PrefersNonDefaultGPU",
        "X-GNOME-Autostart-enabled", "X-systemd-skip"
    }
    
    # List keys (split by semicolon)
    LIST_KEYS = {
        "Categories", "MimeType", "Keywords", "OnlyShowIn", "NotShowIn",
        "Implements", "Actions"
    }
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        
    def extract(self) -> Dict[str, Any]:
        """Extract all metadata from the desktop file."""
        try:
            # Read file with UTF-8 encoding
            with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            metadata = {
                "format": "Desktop Entry",
                "file_path": str(self.file_path),
                "file_size": len(content),
            }
            
            # Parse sections
            sections = self._parse_sections(content)
            
            # Extract Desktop Entry section (primary)
            if "Desktop Entry" in sections:
                desktop_entry = sections["Desktop Entry"]
                metadata.update(self._parse_desktop_entry(desktop_entry))
            
            # Extract other sections (Desktop Action, X-...)
            other_sections = {k: v for k, v in sections.items() if k != "Desktop Entry"}
            if other_sections:
                metadata["other_sections"] = {
                    "count": len(other_sections),
                    "section_names": list(other_sections.keys()),
                }
                
                # Parse Desktop Action sections
                action_sections = {k: v for k, v in other_sections.items() 
                                 if k.startswith("Desktop Action ")}
                if action_sections:
                    actions = []
                    for action_name, action_data in action_sections.items():
                        action = {
                            "action_id": action_name.replace("Desktop Action ", ""),
                            "name": self._get_value(action_data, "Name"),
                            "exec": self._get_value(action_data, "Exec"),
                            "icon": self._get_value(action_data, "Icon"),
                        }
                        actions.append(action)
                    metadata["actions"] = actions
            
            return metadata
            
        except Exception as e:
            return {
                "format": "Desktop Entry",
                "file_path": str(self.file_path),
                "error": str(e)
            }
    
    def _parse_sections(self, content: str) -> Dict[str, Dict[str, Any]]:
        """Parse INI-like sections and key-value pairs."""
        sections = {}
        current_section = None
        current_data = {}
        
        for line in content.split('\n'):
            # Strip whitespace
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
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
                
                # Parse locale from key (e.g., Name[fr_FR])
                locale_match = re.match(r'^(.+)\[([^\]]+)\]$', key)
                if locale_match:
                    base_key = locale_match.group(1)
                    locale = locale_match.group(2)
                    
                    # Store localized values
                    if base_key not in current_data:
                        current_data[base_key] = {"default": None, "localized": {}}
                    elif not isinstance(current_data[base_key], dict):
                        # Convert to localized dict
                        old_value = current_data[base_key]
                        current_data[base_key] = {"default": old_value, "localized": {}}
                    
                    current_data[base_key]["localized"][locale] = value
                else:
                    # Non-localized value
                    if key in current_data and isinstance(current_data[key], dict):
                        current_data[key]["default"] = value
                    else:
                        current_data[key] = value
        
        # Save last section
        if current_section:
            sections[current_section] = current_data
        
        return sections
    
    def _get_value(self, data: Dict[str, Any], key: str) -> Optional[str]:
        """Get value from parsed data (handles localized values)."""
        if key not in data:
            return None
        
        value = data[key]
        if isinstance(value, dict):
            return value.get("default")
        return value
    
    def _get_localized_values(self, data: Dict[str, Any], key: str) -> Optional[Dict[str, str]]:
        """Get all localized values for a key."""
        if key not in data:
            return None
        
        value = data[key]
        if isinstance(value, dict):
            return value.get("localized")
        return None
    
    def _parse_boolean(self, value: Optional[str]) -> Optional[bool]:
        """Parse boolean value (true/false)."""
        if value is None:
            return None
        value_lower = value.lower()
        if value_lower == "true":
            return True
        elif value_lower == "false":
            return False
        return None
    
    def _parse_list(self, value: Optional[str]) -> Optional[List[str]]:
        """Parse semicolon-separated list."""
        if value is None:
            return None
        # Split by semicolon and filter empty strings
        items = [item.strip() for item in value.split(';') if item.strip()]
        return items if items else None
    
    def _parse_desktop_entry(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse [Desktop Entry] section."""
        result = {}
        
        # Type
        entry_type = self._get_value(data, "Type")
        if entry_type:
            result["type"] = entry_type
        
        # Name (with localization)
        name = self._get_value(data, "Name")
        if name:
            result["name"] = name
            
            # Count localizations
            name_localized = self._get_localized_values(data, "Name")
            if name_localized:
                result["name_locales"] = list(name_localized.keys())
                result["name_locale_count"] = len(name_localized)
        
        # GenericName
        generic_name = self._get_value(data, "GenericName")
        if generic_name:
            result["generic_name"] = generic_name
        
        # Comment
        comment = self._get_value(data, "Comment")
        if comment:
            result["comment"] = comment
        
        # Icon
        icon = self._get_value(data, "Icon")
        if icon:
            result["icon"] = icon
        
        # Exec (command)
        exec_cmd = self._get_value(data, "Exec")
        if exec_cmd:
            result["exec"] = exec_cmd
            
            # Detect field codes
            field_codes = re.findall(r'%[fFuUickdDnNvm]', exec_cmd)
            if field_codes:
                result["exec_field_codes"] = list(set(field_codes))
        
        # TryExec
        try_exec = self._get_value(data, "TryExec")
        if try_exec:
            result["try_exec"] = try_exec
        
        # Path (working directory)
        path = self._get_value(data, "Path")
        if path:
            result["path"] = path
        
        # Terminal
        terminal = self._parse_boolean(self._get_value(data, "Terminal"))
        if terminal is not None:
            result["terminal"] = terminal
        
        # StartupNotify
        startup_notify = self._parse_boolean(self._get_value(data, "StartupNotify"))
        if startup_notify is not None:
            result["startup_notify"] = startup_notify
        
        # NoDisplay
        no_display = self._parse_boolean(self._get_value(data, "NoDisplay"))
        if no_display is not None:
            result["no_display"] = no_display
        
        # Hidden
        hidden = self._parse_boolean(self._get_value(data, "Hidden"))
        if hidden is not None:
            result["hidden"] = hidden
        
        # Categories
        categories = self._parse_list(self._get_value(data, "Categories"))
        if categories:
            result["categories"] = categories
        
        # MimeType
        mime_types = self._parse_list(self._get_value(data, "MimeType"))
        if mime_types:
            result["mime_types"] = mime_types
        
        # Keywords
        keywords = self._parse_list(self._get_value(data, "Keywords"))
        if keywords:
            result["keywords"] = keywords
        
        # OnlyShowIn
        only_show_in = self._parse_list(self._get_value(data, "OnlyShowIn"))
        if only_show_in:
            result["only_show_in"] = only_show_in
        
        # NotShowIn
        not_show_in = self._parse_list(self._get_value(data, "NotShowIn"))
        if not_show_in:
            result["not_show_in"] = not_show_in
        
        # Actions
        actions = self._parse_list(self._get_value(data, "Actions"))
        if actions:
            result["action_ids"] = actions
        
        # DBusActivatable
        dbus_activatable = self._parse_boolean(self._get_value(data, "DBusActivatable"))
        if dbus_activatable is not None:
            result["dbus_activatable"] = dbus_activatable
        
        # Version (desktop file spec version)
        version = self._get_value(data, "Version")
        if version:
            result["version"] = version
        
        # X- extensions (vendor-specific)
        x_keys = {}
        for key in data.keys():
            if key.startswith("X-"):
                value = self._get_value(data, key)
                # Try to parse as boolean
                bool_value = self._parse_boolean(value)
                if bool_value is not None:
                    x_keys[key] = bool_value
                else:
                    x_keys[key] = value
        
        if x_keys:
            result["x_extensions"] = x_keys
        
        return result

def main():
    if len(sys.argv) < 2:
        print("Usage: desktop_extractor.py <desktop_file>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    extractor = DesktopExtractor(file_path)
    metadata = extractor.extract()
    
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
