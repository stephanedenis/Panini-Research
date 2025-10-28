#!/usr/bin/env python3
"""
MIDI (Musical Instrument Digital Interface) Format Extractor for PaniniFS v3.8
Extracts metadata and structure from Standard MIDI Files (SMF).

Supports:
- SMF Format 0 (single track)
- SMF Format 1 (multiple synchronous tracks)
- SMF Format 2 (multiple independent tracks)
- Meta events (tempo, time signature, key signature, lyrics, etc.)
- MIDI events (note on/off, control change, program change, etc.)
- Running status compression
- Variable-length quantities
"""

import struct
import sys
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class MIDIHeader:
    """MIDI file header chunk."""
    format: int
    tracks: int
    division: int


@dataclass
class MIDIEvent:
    """MIDI event."""
    delta_time: int
    type: str
    channel: Optional[int]
    data: Dict[str, Any]


class MIDIExtractor:
    """Extract metadata from MIDI files."""
    
    # Meta event types
    META_EVENTS = {
        0x00: 'Sequence Number',
        0x01: 'Text Event',
        0x02: 'Copyright',
        0x03: 'Track Name',
        0x04: 'Instrument Name',
        0x05: 'Lyric',
        0x06: 'Marker',
        0x07: 'Cue Point',
        0x20: 'Channel Prefix',
        0x2F: 'End of Track',
        0x51: 'Tempo',
        0x54: 'SMPTE Offset',
        0x58: 'Time Signature',
        0x59: 'Key Signature',
        0x7F: 'Sequencer Specific'
    }
    
    # MIDI event types (status bytes)
    EVENT_TYPES = {
        0x80: 'Note Off',
        0x90: 'Note On',
        0xA0: 'Aftertouch',
        0xB0: 'Control Change',
        0xC0: 'Program Change',
        0xD0: 'Channel Pressure',
        0xE0: 'Pitch Bend',
        0xF0: 'System Exclusive',
        0xF7: 'System Exclusive (continued)',
        0xFF: 'Meta Event'
    }
    
    # Note names
    NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    def __init__(self, filepath: str):
        """Initialize extractor with file path."""
        self.filepath = filepath
        self.data = None
        self.offset = 0
        self.header: Optional[MIDIHeader] = None
        self.running_status = 0
        
    def extract_metadata(self) -> Dict[str, Any]:
        """Extract all metadata from MIDI file."""
        with open(self.filepath, 'rb') as f:
            self.data = f.read()
        
        # Parse header chunk
        self.header = self._parse_header_chunk()
        
        # Parse all tracks
        tracks = []
        for track_num in range(self.header.tracks):
            try:
                track = self._parse_track_chunk(track_num)
                tracks.append(track)
            except Exception as e:
                tracks.append({
                    'track_number': track_num,
                    'error': str(e)
                })
        
        # Analyze MIDI content
        analysis = self._analyze_tracks(tracks)
        
        return {
            'format': 'MIDI',
            'header': {
                'format': self.header.format,
                'format_name': self._get_format_name(self.header.format),
                'tracks': self.header.tracks,
                'division': self.header.division,
                'ticks_per_quarter': self.header.division if self.header.division > 0 else None
            },
            'tracks': tracks,
            'analysis': analysis
        }
    
    def _parse_header_chunk(self) -> MIDIHeader:
        """Parse MIDI header chunk (MThd)."""
        if len(self.data) < 14:
            raise ValueError("File too small for MIDI header")
        
        # Check magic
        magic = self.data[0:4]
        if magic != b'MThd':
            raise ValueError(f"Invalid MIDI magic: {magic}")
        
        # Parse header
        length = struct.unpack('>I', self.data[4:8])[0]
        if length != 6:
            raise ValueError(f"Invalid header length: {length}")
        
        format_type = struct.unpack('>H', self.data[8:10])[0]
        num_tracks = struct.unpack('>H', self.data[10:12])[0]
        division = struct.unpack('>H', self.data[12:14])[0]
        
        self.offset = 14
        
        return MIDIHeader(
            format=format_type,
            tracks=num_tracks,
            division=division
        )
    
    def _parse_track_chunk(self, track_num: int) -> Dict[str, Any]:
        """Parse a single MIDI track chunk (MTrk)."""
        # Check magic
        if self.offset + 8 > len(self.data):
            raise ValueError(f"Unexpected end of file at track {track_num}")
        
        magic = self.data[self.offset:self.offset+4]
        if magic != b'MTrk':
            raise ValueError(f"Invalid track magic: {magic}")
        
        length = struct.unpack('>I', self.data[self.offset+4:self.offset+8])[0]
        self.offset += 8
        
        track_start = self.offset
        track_end = self.offset + length
        
        # Parse events
        events = []
        self.running_status = 0
        
        while self.offset < track_end:
            try:
                event = self._parse_event()
                if event:
                    events.append(event)
            except Exception as e:
                # Skip malformed events
                break
        
        # Ensure offset is at track end
        self.offset = track_end
        
        # Analyze track
        track_info = self._analyze_track(track_num, events)
        track_info['length'] = length
        track_info['event_count'] = len(events)
        
        return track_info
    
    def _parse_event(self) -> Optional[MIDIEvent]:
        """Parse a single MIDI event."""
        # Read delta time
        delta_time = self._read_variable_length()
        
        # Read status byte
        if self.offset >= len(self.data):
            return None
        
        status = self.data[self.offset]
        
        # Check for running status
        if status < 0x80:
            # Running status - reuse previous status
            status = self.running_status
        else:
            self.offset += 1
            # Update running status (except for meta/sysex)
            if status < 0xF0:
                self.running_status = status
        
        # Determine event type
        event_type = status & 0xF0
        channel = status & 0x0F if event_type < 0xF0 else None
        
        # Parse event data
        if status == 0xFF:
            # Meta event
            return self._parse_meta_event(delta_time)
        elif status == 0xF0 or status == 0xF7:
            # System Exclusive
            return self._parse_sysex_event(delta_time, status)
        else:
            # Channel event
            return self._parse_channel_event(delta_time, event_type, channel)
    
    def _parse_meta_event(self, delta_time: int) -> MIDIEvent:
        """Parse a meta event."""
        if self.offset >= len(self.data):
            raise ValueError("Unexpected end of meta event")
        
        meta_type = self.data[self.offset]
        self.offset += 1
        
        length = self._read_variable_length()
        
        if self.offset + length > len(self.data):
            raise ValueError("Meta event data overflow")
        
        data_bytes = self.data[self.offset:self.offset+length]
        self.offset += length
        
        # Parse specific meta events
        event_name = self.META_EVENTS.get(meta_type, f'Unknown (0x{meta_type:02X})')
        data = {'raw_type': meta_type}
        
        if meta_type == 0x51:  # Tempo
            if length == 3:
                microseconds = (data_bytes[0] << 16) | (data_bytes[1] << 8) | data_bytes[2]
                bpm = 60000000 / microseconds if microseconds > 0 else 0
                data['microseconds_per_quarter'] = microseconds
                data['bpm'] = round(bpm, 2)
        elif meta_type == 0x58:  # Time Signature
            if length >= 4:
                data['numerator'] = data_bytes[0]
                data['denominator'] = 2 ** data_bytes[1]
                data['clocks_per_click'] = data_bytes[2]
                data['32nds_per_quarter'] = data_bytes[3]
        elif meta_type == 0x59:  # Key Signature
            if length >= 2:
                sharps_flats = struct.unpack('b', bytes([data_bytes[0]]))[0]
                major_minor = data_bytes[1]
                data['sharps_flats'] = sharps_flats
                data['mode'] = 'major' if major_minor == 0 else 'minor'
        elif meta_type in (0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07):  # Text events
            try:
                data['text'] = data_bytes.decode('utf-8', errors='replace')
            except:
                data['text'] = repr(data_bytes)
        
        return MIDIEvent(
            delta_time=delta_time,
            type=event_name,
            channel=None,
            data=data
        )
    
    def _parse_sysex_event(self, delta_time: int, status: int) -> MIDIEvent:
        """Parse a system exclusive event."""
        length = self._read_variable_length()
        
        if self.offset + length > len(self.data):
            raise ValueError("SysEx data overflow")
        
        data_bytes = self.data[self.offset:self.offset+length]
        self.offset += length
        
        return MIDIEvent(
            delta_time=delta_time,
            type='System Exclusive',
            channel=None,
            data={'length': length}
        )
    
    def _parse_channel_event(self, delta_time: int, event_type: int, 
                            channel: int) -> MIDIEvent:
        """Parse a channel event."""
        event_name = self.EVENT_TYPES.get(event_type, f'Unknown (0x{event_type:02X})')
        data = {'channel': channel}
        
        if event_type in (0x80, 0x90, 0xA0):  # Note Off, Note On, Aftertouch
            if self.offset + 2 > len(self.data):
                raise ValueError("Channel event data underflow")
            note = self.data[self.offset]
            velocity = self.data[self.offset + 1]
            self.offset += 2
            
            data['note'] = note
            data['note_name'] = self._get_note_name(note)
            data['velocity'] = velocity
            
            # Note On with velocity 0 is actually Note Off
            if event_type == 0x90 and velocity == 0:
                event_name = 'Note Off'
        
        elif event_type == 0xB0:  # Control Change
            if self.offset + 2 > len(self.data):
                raise ValueError("Channel event data underflow")
            controller = self.data[self.offset]
            value = self.data[self.offset + 1]
            self.offset += 2
            
            data['controller'] = controller
            data['value'] = value
        
        elif event_type == 0xC0:  # Program Change
            if self.offset + 1 > len(self.data):
                raise ValueError("Channel event data underflow")
            program = self.data[self.offset]
            self.offset += 1
            
            data['program'] = program
        
        elif event_type == 0xD0:  # Channel Pressure
            if self.offset + 1 > len(self.data):
                raise ValueError("Channel event data underflow")
            pressure = self.data[self.offset]
            self.offset += 1
            
            data['pressure'] = pressure
        
        elif event_type == 0xE0:  # Pitch Bend
            if self.offset + 2 > len(self.data):
                raise ValueError("Channel event data underflow")
            lsb = self.data[self.offset]
            msb = self.data[self.offset + 1]
            self.offset += 2
            
            value = (msb << 7) | lsb
            data['value'] = value
            data['semitones'] = (value - 8192) / 4096.0  # ±2 semitones
        
        return MIDIEvent(
            delta_time=delta_time,
            type=event_name,
            channel=channel,
            data=data
        )
    
    def _read_variable_length(self) -> int:
        """Read a variable-length quantity."""
        value = 0
        
        while self.offset < len(self.data):
            byte = self.data[self.offset]
            self.offset += 1
            
            value = (value << 7) | (byte & 0x7F)
            
            if not (byte & 0x80):
                break
        
        return value
    
    def _get_note_name(self, note: int) -> str:
        """Get note name from MIDI note number."""
        octave = (note // 12) - 1
        note_name = self.NOTE_NAMES[note % 12]
        return f"{note_name}{octave}"
    
    def _get_format_name(self, format_type: int) -> str:
        """Get MIDI format name."""
        formats = {
            0: 'Single track',
            1: 'Multiple tracks (synchronous)',
            2: 'Multiple tracks (independent)'
        }
        return formats.get(format_type, f'Unknown ({format_type})')
    
    def _analyze_track(self, track_num: int, events: List[MIDIEvent]) -> Dict[str, Any]:
        """Analyze a single track."""
        track_name = None
        instrument = None
        tempo_changes = []
        time_signatures = []
        key_signatures = []
        note_count = 0
        text_events = []
        
        for event in events:
            if event.type == 'Track Name' and 'text' in event.data:
                track_name = event.data['text']
            elif event.type == 'Instrument Name' and 'text' in event.data:
                instrument = event.data['text']
            elif event.type == 'Tempo':
                tempo_changes.append({
                    'delta_time': event.delta_time,
                    'bpm': event.data.get('bpm')
                })
            elif event.type == 'Time Signature':
                time_signatures.append({
                    'delta_time': event.delta_time,
                    'numerator': event.data.get('numerator'),
                    'denominator': event.data.get('denominator')
                })
            elif event.type == 'Key Signature':
                key_signatures.append({
                    'delta_time': event.delta_time,
                    'sharps_flats': event.data.get('sharps_flats'),
                    'mode': event.data.get('mode')
                })
            elif event.type in ('Note On', 'Note Off'):
                if event.type == 'Note On' and event.data.get('velocity', 0) > 0:
                    note_count += 1
            elif 'text' in event.data:
                text_events.append({
                    'type': event.type,
                    'text': event.data['text']
                })
        
        return {
            'track_number': track_num,
            'name': track_name,
            'instrument': instrument,
            'note_count': note_count,
            'tempo_changes': tempo_changes if tempo_changes else None,
            'time_signatures': time_signatures if time_signatures else None,
            'key_signatures': key_signatures if key_signatures else None,
            'text_events': text_events[:5] if text_events else None  # Limit to 5
        }
    
    def _analyze_tracks(self, tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze all tracks for statistics."""
        total_events = sum(t.get('event_count', 0) for t in tracks)
        total_notes = sum(t.get('note_count', 0) for t in tracks)
        
        # Get global tempo
        first_tempo = None
        for track in tracks:
            if track.get('tempo_changes'):
                first_tempo = track['tempo_changes'][0].get('bpm')
                break
        
        # Get global time signature
        first_time_sig = None
        for track in tracks:
            if track.get('time_signatures'):
                ts = track['time_signatures'][0]
                first_time_sig = f"{ts.get('numerator')}/{ts.get('denominator')}"
                break
        
        return {
            'total_tracks': len(tracks),
            'total_events': total_events,
            'total_notes': total_notes,
            'tempo_bpm': first_tempo,
            'time_signature': first_time_sig
        }


def main():
    """Main extraction function."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.mid>", file=sys.stderr)
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    try:
        extractor = MIDIExtractor(filepath)
        metadata = extractor.extract_metadata()
        print(json.dumps(metadata, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
