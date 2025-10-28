#!/usr/bin/env python3
"""
PaniniFS v3.15 - iCalendar (ICS) Format Extractor
Author: Stéphane Denis (SDenis.ai)
Deconstructs iCalendar/ICS files to their finest details

Supports:
- RFC 5545 (iCalendar format)
- VEVENT (calendar events)
- VTODO (task items)
- VJOURNAL (journal entries)
- VFREEBUSY (free/busy time)
- VTIMEZONE (timezone definitions)
- VALARM (reminders/alarms)
- Recurrence rules (RRULE)
- Attendees and organizers
- Geographic coordinates
- Attachments and URLs
"""

import re
from datetime import datetime
from typing import Dict, List, Any, Optional

class ICSExtractor:
    """Extract metadata from iCalendar (ICS) files"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.metadata = {
            'format': 'iCalendar',
            'version': None,
            'product_id': None,
            'method': None,
            'calendar_scale': None,
            'events': [],
            'todos': [],
            'journals': [],
            'freebusys': [],
            'timezones': [],
            'alarms': [],
            'statistics': {}
        }
    
    def extract(self) -> Dict[str, Any]:
        """Extract all iCalendar metadata"""
        with open(self.filename, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        self._parse_calendar_properties(content)
        self._parse_events(content)
        self._parse_todos(content)
        self._parse_journals(content)
        self._parse_freebusys(content)
        self._parse_timezones(content)
        self._analyze_calendar()
        
        return self.metadata
    
    def _parse_calendar_properties(self, content: str):
        """Parse top-level calendar properties"""
        # VERSION
        version_match = re.search(r'VERSION:(.+)', content)
        if version_match:
            self.metadata['version'] = version_match.group(1).strip()
        
        # PRODID (product identifier)
        prodid_match = re.search(r'PRODID:(.+)', content)
        if prodid_match:
            self.metadata['product_id'] = prodid_match.group(1).strip()
        
        # METHOD (iTIP method)
        method_match = re.search(r'METHOD:(.+)', content)
        if method_match:
            self.metadata['method'] = method_match.group(1).strip()
        
        # CALSCALE
        calscale_match = re.search(r'CALSCALE:(.+)', content)
        if calscale_match:
            self.metadata['calendar_scale'] = calscale_match.group(1).strip()
    
    def _parse_events(self, content: str):
        """Parse VEVENT components"""
        event_pattern = re.compile(r'BEGIN:VEVENT\r?\n(.*?)\r?\nEND:VEVENT', re.DOTALL)
        
        for match in event_pattern.finditer(content):
            event_data = match.group(1)
            event = self._parse_event(event_data)
            if event:
                self.metadata['events'].append(event)
    
    def _parse_event(self, data: str) -> Optional[Dict[str, Any]]:
        """Parse a single VEVENT"""
        event = {}
        
        # UID (unique identifier)
        uid_match = re.search(r'UID:(.+)', data)
        if uid_match:
            event['uid'] = uid_match.group(1).strip()
        
        # SUMMARY (title)
        summary_match = re.search(r'SUMMARY:(.+)', data)
        if summary_match:
            event['summary'] = self._decode_value(summary_match.group(1).strip())
        
        # DESCRIPTION
        desc_match = re.search(r'DESCRIPTION:(.+?)(?=\r?\n[A-Z]|\r?\nEND:)', data, re.DOTALL)
        if desc_match:
            event['description'] = self._decode_value(desc_match.group(1).strip())
        
        # DTSTART (start date/time)
        dtstart_match = re.search(r'DTSTART(?:;[^:]*)?:(.+)', data)
        if dtstart_match:
            event['start'] = self._parse_datetime(dtstart_match.group(1).strip())
        
        # DTEND (end date/time)
        dtend_match = re.search(r'DTEND(?:;[^:]*)?:(.+)', data)
        if dtend_match:
            event['end'] = self._parse_datetime(dtend_match.group(1).strip())
        
        # DURATION (alternative to DTEND)
        duration_match = re.search(r'DURATION:(.+)', data)
        if duration_match:
            event['duration'] = duration_match.group(1).strip()
        
        # LOCATION
        location_match = re.search(r'LOCATION:(.+)', data)
        if location_match:
            event['location'] = self._decode_value(location_match.group(1).strip())
        
        # GEO (geographic coordinates)
        geo_match = re.search(r'GEO:([^;]+);([^;\r\n]+)', data)
        if geo_match:
            event['geo'] = {
                'latitude': float(geo_match.group(1)),
                'longitude': float(geo_match.group(2))
            }
        
        # STATUS
        status_match = re.search(r'STATUS:(.+)', data)
        if status_match:
            event['status'] = status_match.group(1).strip()
        
        # PRIORITY (0-9, 0=undefined)
        priority_match = re.search(r'PRIORITY:(\d+)', data)
        if priority_match:
            event['priority'] = int(priority_match.group(1))
        
        # CLASS (PUBLIC, PRIVATE, CONFIDENTIAL)
        class_match = re.search(r'CLASS:(.+)', data)
        if class_match:
            event['class'] = class_match.group(1).strip()
        
        # TRANSP (OPAQUE, TRANSPARENT)
        transp_match = re.search(r'TRANSP:(.+)', data)
        if transp_match:
            event['transparency'] = transp_match.group(1).strip()
        
        # ORGANIZER
        organizer_match = re.search(r'ORGANIZER(?:;[^:]*)?:(.+)', data)
        if organizer_match:
            event['organizer'] = self._parse_attendee(organizer_match.group(0))
        
        # ATTENDEE (can be multiple)
        event['attendees'] = []
        attendee_pattern = re.compile(r'ATTENDEE(?:;[^:]*)?:(.+)', re.MULTILINE)
        for match in attendee_pattern.finditer(data):
            attendee = self._parse_attendee(match.group(0))
            if attendee:
                event['attendees'].append(attendee)
        
        # RRULE (recurrence rule)
        rrule_match = re.search(r'RRULE:(.+)', data)
        if rrule_match:
            event['recurrence'] = self._parse_rrule(rrule_match.group(1))
        
        # EXDATE (exception dates)
        event['exception_dates'] = []
        exdate_pattern = re.compile(r'EXDATE(?:;[^:]*)?:(.+)', re.MULTILINE)
        for match in exdate_pattern.finditer(data):
            event['exception_dates'].append(self._parse_datetime(match.group(1).strip()))
        
        # RDATE (recurrence dates)
        event['recurrence_dates'] = []
        rdate_pattern = re.compile(r'RDATE(?:;[^:]*)?:(.+)', re.MULTILINE)
        for match in rdate_pattern.finditer(data):
            event['recurrence_dates'].append(self._parse_datetime(match.group(1).strip()))
        
        # URL
        url_match = re.search(r'URL:(.+)', data)
        if url_match:
            event['url'] = url_match.group(1).strip()
        
        # ATTACH (attachments)
        event['attachments'] = []
        attach_pattern = re.compile(r'ATTACH(?:;[^:]*)?:(.+)', re.MULTILINE)
        for match in attach_pattern.finditer(data):
            event['attachments'].append(match.group(1).strip())
        
        # CREATED, DTSTAMP, LAST-MODIFIED
        created_match = re.search(r'CREATED:(.+)', data)
        if created_match:
            event['created'] = self._parse_datetime(created_match.group(1).strip())
        
        dtstamp_match = re.search(r'DTSTAMP:(.+)', data)
        if dtstamp_match:
            event['timestamp'] = self._parse_datetime(dtstamp_match.group(1).strip())
        
        modified_match = re.search(r'LAST-MODIFIED:(.+)', data)
        if modified_match:
            event['last_modified'] = self._parse_datetime(modified_match.group(1).strip())
        
        # SEQUENCE (revision number)
        sequence_match = re.search(r'SEQUENCE:(\d+)', data)
        if sequence_match:
            event['sequence'] = int(sequence_match.group(1))
        
        # VALARM (alarms)
        event['alarms'] = self._parse_alarms(data)
        
        return event if event else None
    
    def _parse_todos(self, content: str):
        """Parse VTODO components"""
        todo_pattern = re.compile(r'BEGIN:VTODO\r?\n(.*?)\r?\nEND:VTODO', re.DOTALL)
        
        for match in todo_pattern.finditer(content):
            todo_data = match.group(1)
            todo = self._parse_todo(todo_data)
            if todo:
                self.metadata['todos'].append(todo)
    
    def _parse_todo(self, data: str) -> Optional[Dict[str, Any]]:
        """Parse a single VTODO"""
        todo = {}
        
        # UID
        uid_match = re.search(r'UID:(.+)', data)
        if uid_match:
            todo['uid'] = uid_match.group(1).strip()
        
        # SUMMARY
        summary_match = re.search(r'SUMMARY:(.+)', data)
        if summary_match:
            todo['summary'] = self._decode_value(summary_match.group(1).strip())
        
        # STATUS (NEEDS-ACTION, COMPLETED, IN-PROCESS, CANCELLED)
        status_match = re.search(r'STATUS:(.+)', data)
        if status_match:
            todo['status'] = status_match.group(1).strip()
        
        # PERCENT-COMPLETE (0-100)
        percent_match = re.search(r'PERCENT-COMPLETE:(\d+)', data)
        if percent_match:
            todo['percent_complete'] = int(percent_match.group(1))
        
        # PRIORITY
        priority_match = re.search(r'PRIORITY:(\d+)', data)
        if priority_match:
            todo['priority'] = int(priority_match.group(1))
        
        # DUE (due date)
        due_match = re.search(r'DUE(?:;[^:]*)?:(.+)', data)
        if due_match:
            todo['due'] = self._parse_datetime(due_match.group(1).strip())
        
        # COMPLETED (completion date)
        completed_match = re.search(r'COMPLETED:(.+)', data)
        if completed_match:
            todo['completed'] = self._parse_datetime(completed_match.group(1).strip())
        
        return todo if todo else None
    
    def _parse_journals(self, content: str):
        """Parse VJOURNAL components"""
        journal_pattern = re.compile(r'BEGIN:VJOURNAL\r?\n(.*?)\r?\nEND:VJOURNAL', re.DOTALL)
        
        for match in journal_pattern.finditer(content):
            journal_data = match.group(1)
            journal = self._parse_journal(journal_data)
            if journal:
                self.metadata['journals'].append(journal)
    
    def _parse_journal(self, data: str) -> Optional[Dict[str, Any]]:
        """Parse a single VJOURNAL"""
        journal = {}
        
        # UID
        uid_match = re.search(r'UID:(.+)', data)
        if uid_match:
            journal['uid'] = uid_match.group(1).strip()
        
        # SUMMARY
        summary_match = re.search(r'SUMMARY:(.+)', data)
        if summary_match:
            journal['summary'] = self._decode_value(summary_match.group(1).strip())
        
        # DESCRIPTION
        desc_match = re.search(r'DESCRIPTION:(.+?)(?=\r?\n[A-Z]|\r?\nEND:)', data, re.DOTALL)
        if desc_match:
            journal['description'] = self._decode_value(desc_match.group(1).strip())
        
        # DTSTART
        dtstart_match = re.search(r'DTSTART(?:;[^:]*)?:(.+)', data)
        if dtstart_match:
            journal['start'] = self._parse_datetime(dtstart_match.group(1).strip())
        
        return journal if journal else None
    
    def _parse_freebusys(self, content: str):
        """Parse VFREEBUSY components"""
        freebusy_pattern = re.compile(r'BEGIN:VFREEBUSY\r?\n(.*?)\r?\nEND:VFREEBUSY', re.DOTALL)
        
        for match in freebusy_pattern.finditer(content):
            fb_data = match.group(1)
            fb = self._parse_freebusy(fb_data)
            if fb:
                self.metadata['freebusys'].append(fb)
    
    def _parse_freebusy(self, data: str) -> Optional[Dict[str, Any]]:
        """Parse a single VFREEBUSY"""
        fb = {}
        
        # DTSTART
        dtstart_match = re.search(r'DTSTART:(.+)', data)
        if dtstart_match:
            fb['start'] = self._parse_datetime(dtstart_match.group(1).strip())
        
        # DTEND
        dtend_match = re.search(r'DTEND:(.+)', data)
        if dtend_match:
            fb['end'] = self._parse_datetime(dtend_match.group(1).strip())
        
        # FREEBUSY periods
        fb['periods'] = []
        fb_pattern = re.compile(r'FREEBUSY(?:;FBTYPE=([^:]+))?:(.+)', re.MULTILINE)
        for match in fb_pattern.finditer(data):
            fb_type = match.group(1) or 'BUSY'
            periods = match.group(2).strip()
            fb['periods'].append({
                'type': fb_type,
                'periods': periods
            })
        
        return fb if fb else None
    
    def _parse_timezones(self, content: str):
        """Parse VTIMEZONE components"""
        tz_pattern = re.compile(r'BEGIN:VTIMEZONE\r?\n(.*?)\r?\nEND:VTIMEZONE', re.DOTALL)
        
        for match in tz_pattern.finditer(content):
            tz_data = match.group(1)
            tz = self._parse_timezone(tz_data)
            if tz:
                self.metadata['timezones'].append(tz)
    
    def _parse_timezone(self, data: str) -> Optional[Dict[str, Any]]:
        """Parse a single VTIMEZONE"""
        tz = {}
        
        # TZID (timezone identifier)
        tzid_match = re.search(r'TZID:(.+)', data)
        if tzid_match:
            tz['tzid'] = tzid_match.group(1).strip()
        
        # STANDARD and DAYLIGHT components
        tz['standard'] = []
        tz['daylight'] = []
        
        standard_pattern = re.compile(r'BEGIN:STANDARD\r?\n(.*?)\r?\nEND:STANDARD', re.DOTALL)
        for match in standard_pattern.finditer(data):
            std = self._parse_tz_component(match.group(1))
            if std:
                tz['standard'].append(std)
        
        daylight_pattern = re.compile(r'BEGIN:DAYLIGHT\r?\n(.*?)\r?\nEND:DAYLIGHT', re.DOTALL)
        for match in daylight_pattern.finditer(data):
            dl = self._parse_tz_component(match.group(1))
            if dl:
                tz['daylight'].append(dl)
        
        return tz if tz else None
    
    def _parse_tz_component(self, data: str) -> Optional[Dict[str, Any]]:
        """Parse STANDARD or DAYLIGHT timezone component"""
        comp = {}
        
        # DTSTART
        dtstart_match = re.search(r'DTSTART:(.+)', data)
        if dtstart_match:
            comp['start'] = self._parse_datetime(dtstart_match.group(1).strip())
        
        # TZOFFSETFROM
        from_match = re.search(r'TZOFFSETFROM:(.+)', data)
        if from_match:
            comp['offset_from'] = from_match.group(1).strip()
        
        # TZOFFSETTO
        to_match = re.search(r'TZOFFSETTO:(.+)', data)
        if to_match:
            comp['offset_to'] = to_match.group(1).strip()
        
        # TZNAME
        name_match = re.search(r'TZNAME:(.+)', data)
        if name_match:
            comp['name'] = name_match.group(1).strip()
        
        return comp if comp else None
    
    def _parse_alarms(self, data: str) -> List[Dict[str, Any]]:
        """Parse VALARM components within an event"""
        alarms = []
        alarm_pattern = re.compile(r'BEGIN:VALARM\r?\n(.*?)\r?\nEND:VALARM', re.DOTALL)
        
        for match in alarm_pattern.finditer(data):
            alarm_data = match.group(1)
            alarm = {}
            
            # ACTION (AUDIO, DISPLAY, EMAIL)
            action_match = re.search(r'ACTION:(.+)', alarm_data)
            if action_match:
                alarm['action'] = action_match.group(1).strip()
            
            # TRIGGER
            trigger_match = re.search(r'TRIGGER(?:;[^:]*)?:(.+)', alarm_data)
            if trigger_match:
                alarm['trigger'] = trigger_match.group(1).strip()
            
            # DESCRIPTION (for DISPLAY/EMAIL)
            desc_match = re.search(r'DESCRIPTION:(.+)', alarm_data)
            if desc_match:
                alarm['description'] = self._decode_value(desc_match.group(1).strip())
            
            # SUMMARY (for EMAIL)
            summary_match = re.search(r'SUMMARY:(.+)', alarm_data)
            if summary_match:
                alarm['summary'] = self._decode_value(summary_match.group(1).strip())
            
            # ATTENDEE (for EMAIL)
            alarm['attendees'] = []
            attendee_pattern = re.compile(r'ATTENDEE:(.+)', re.MULTILINE)
            for att_match in attendee_pattern.finditer(alarm_data):
                alarm['attendees'].append(att_match.group(1).strip())
            
            # ATTACH (for AUDIO)
            attach_match = re.search(r'ATTACH:(.+)', alarm_data)
            if attach_match:
                alarm['attachment'] = attach_match.group(1).strip()
            
            if alarm:
                alarms.append(alarm)
        
        return alarms
    
    def _parse_attendee(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse ATTENDEE or ORGANIZER property"""
        attendee = {}
        
        # Extract email/URI
        uri_match = re.search(r':(.+)$', line)
        if uri_match:
            attendee['uri'] = uri_match.group(1).strip()
        
        # CN (common name)
        cn_match = re.search(r'CN=([^;:]+)', line)
        if cn_match:
            attendee['name'] = cn_match.group(1).strip('"')
        
        # ROLE (CHAIR, REQ-PARTICIPANT, OPT-PARTICIPANT, NON-PARTICIPANT)
        role_match = re.search(r'ROLE=([^;:]+)', line)
        if role_match:
            attendee['role'] = role_match.group(1).strip()
        
        # PARTSTAT (NEEDS-ACTION, ACCEPTED, DECLINED, TENTATIVE, DELEGATED)
        partstat_match = re.search(r'PARTSTAT=([^;:]+)', line)
        if partstat_match:
            attendee['participation_status'] = partstat_match.group(1).strip()
        
        # RSVP
        rsvp_match = re.search(r'RSVP=(TRUE|FALSE)', line)
        if rsvp_match:
            attendee['rsvp'] = rsvp_match.group(1) == 'TRUE'
        
        return attendee if attendee else None
    
    def _parse_rrule(self, rrule: str) -> Dict[str, Any]:
        """Parse recurrence rule"""
        rule = {}
        
        # FREQ (SECONDLY, MINUTELY, HOURLY, DAILY, WEEKLY, MONTHLY, YEARLY)
        freq_match = re.search(r'FREQ=([^;]+)', rrule)
        if freq_match:
            rule['frequency'] = freq_match.group(1).strip()
        
        # INTERVAL
        interval_match = re.search(r'INTERVAL=(\d+)', rrule)
        if interval_match:
            rule['interval'] = int(interval_match.group(1))
        
        # COUNT
        count_match = re.search(r'COUNT=(\d+)', rrule)
        if count_match:
            rule['count'] = int(count_match.group(1))
        
        # UNTIL
        until_match = re.search(r'UNTIL=([^;]+)', rrule)
        if until_match:
            rule['until'] = self._parse_datetime(until_match.group(1).strip())
        
        # BYDAY (MO, TU, WE, TH, FR, SA, SU)
        byday_match = re.search(r'BYDAY=([^;]+)', rrule)
        if byday_match:
            rule['by_day'] = byday_match.group(1).strip().split(',')
        
        # BYMONTHDAY
        bymonthday_match = re.search(r'BYMONTHDAY=([^;]+)', rrule)
        if bymonthday_match:
            rule['by_month_day'] = [int(x) for x in bymonthday_match.group(1).split(',')]
        
        # BYMONTH
        bymonth_match = re.search(r'BYMONTH=([^;]+)', rrule)
        if bymonth_match:
            rule['by_month'] = [int(x) for x in bymonth_match.group(1).split(',')]
        
        # WKST (week start)
        wkst_match = re.search(r'WKST=([^;]+)', rrule)
        if wkst_match:
            rule['week_start'] = wkst_match.group(1).strip()
        
        return rule
    
    def _parse_datetime(self, dt_str: str) -> Optional[str]:
        """Parse iCalendar datetime format"""
        if not dt_str:
            return None
        
        # Remove timezone identifier if present
        dt_str = re.sub(r';TZID=[^:]+:', '', dt_str)
        
        try:
            # Try parsing different formats
            if 'T' in dt_str:
                if dt_str.endswith('Z'):
                    # UTC format: 20231215T120000Z
                    dt = datetime.strptime(dt_str, '%Y%m%dT%H%M%SZ')
                else:
                    # Local format: 20231215T120000
                    dt = datetime.strptime(dt_str, '%Y%m%dT%H%M%S')
                return dt.isoformat()
            else:
                # Date only: 20231215
                dt = datetime.strptime(dt_str, '%Y%m%d')
                return dt.date().isoformat()
        except ValueError:
            return dt_str
    
    def _decode_value(self, value: str) -> str:
        """Decode iCalendar value (handle line folding, escaping)"""
        # Remove line folding (CRLF + space/tab)
        value = re.sub(r'\r?\n[ \t]', '', value)
        
        # Unescape special characters
        value = value.replace('\\n', '\n')
        value = value.replace('\\,', ',')
        value = value.replace('\\;', ';')
        value = value.replace('\\\\', '\\')
        
        return value
    
    def _analyze_calendar(self):
        """Generate calendar statistics"""
        stats = {
            'total_events': len(self.metadata['events']),
            'total_todos': len(self.metadata['todos']),
            'total_journals': len(self.metadata['journals']),
            'total_freebusys': len(self.metadata['freebusys']),
            'total_timezones': len(self.metadata['timezones']),
            'recurring_events': sum(1 for e in self.metadata['events'] if 'recurrence' in e),
            'events_with_location': sum(1 for e in self.metadata['events'] if 'location' in e),
            'events_with_attendees': sum(1 for e in self.metadata['events'] if e.get('attendees')),
            'events_with_alarms': sum(1 for e in self.metadata['events'] if e.get('alarms')),
            'todos_completed': sum(1 for t in self.metadata['todos'] if t.get('status') == 'COMPLETED'),
            'todos_in_progress': sum(1 for t in self.metadata['todos'] if t.get('status') == 'IN-PROCESS')
        }
        
        # Event status distribution
        status_counts = {}
        for event in self.metadata['events']:
            status = event.get('status', 'UNKNOWN')
            status_counts[status] = status_counts.get(status, 0) + 1
        stats['event_status_distribution'] = status_counts
        
        # Date range
        if self.metadata['events']:
            dates = [e['start'] for e in self.metadata['events'] if 'start' in e]
            if dates:
                stats['earliest_event'] = min(dates)
                stats['latest_event'] = max(dates)
        
        self.metadata['statistics'] = stats


def main():
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python ics_extractor.py <file.ics>")
        sys.exit(1)
    
    filename = sys.argv[1]
    extractor = ICSExtractor(filename)
    metadata = extractor.extract()
    
    print(json.dumps(metadata, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
