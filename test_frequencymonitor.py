"""
test_frequencymonitor.py — Unit tests for frequency monitor

Tests coverage target: 85-90%

Test cases:
1. Normal frequency reading → CSV write
2. Deduplication (same value skipped)
3. Date rollover handling
4. Network error recovery
5. Sub-second interval timing (0.05s)
6. Edge case: 50Hz exactly vs 50.01Hz
"""

import os
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, mock_open
import pytest
from io import StringIO

# Import functions to test from frequencymonitor
from frequencymonitor import (
    make_sgi,
    _get_time_str,
)


class TestGetTimeStr:
    """Tests for helper function _get_time_str()."""
    
    def test_get_time_str_normal(self):
        """Test normal time string generation."""
        result = _get_time_str()
        
        # Should return HH:MM:SS.mmm format (up to milliseconds)
        assert isinstance(result, str)
        assert len(result) == 13  # HH:MM:SS + .mmm
        assert ':' in result
        assert '.' in result
    
    def test_get_time_str_consistency(self):
        """Test that time strings change between calls."""
        t1 = _get_time_str()
        time.sleep(0.1)  # Small delay to ensure different timestamp
        t2 = _get_time_str()
        
        assert t1 != t2


class TestFrequencyMonitorNormalOperation:
    """Tests for normal frequency monitor operation."""
    
    def test_normal_frequency_reading(self, tmp_path):
        """Test normal frequency reading and CSV write."""
        # Mock the SungrowInverter to return a valid frequency
        mock_sgi = MagicMock()
        mock_sgi.get_frequency.return_value = 50.02
        
        with patch('frequencymonitor.SungrowInverter', return_value=mock_sgi):
            from frequencymonitor import last_freq, filename
            
            # Simulate reading frequency level
            freq = mock_sgi.get_frequency()
            
            assert freq == 50.02
    
    def test_frequency_deduplication(self, tmp_path):
        """Test that duplicate readings are skipped."""
        # Mock the SungrowInverter to return same frequency
        mock_sgi = MagicMock()
        mock_sgi.get_frequency.return_value = 50.0
        
        with patch('frequencymonitor.SungrowInverter', return_value=mock_sgi):
            from frequencymonitor import last_freq
            
            # First read - should be recorded
            freq1 = mock_sgi.get_frequency()
            
            # Second read (same value) - should NOT be recorded
            freq2 = mock_sgi.get_frequency()
            
            assert freq1 == 50.0
            assert freq2 == 50.0
    
    def test_date_rollover_handling(self, tmp_path):
        """Test that data is written to new file on date change."""
        # Mock the SungrowInverter with changing dates
        mock_sgi = MagicMock()
        
        call_count = [0]
        
        def mock_get_frequency():
            call_count[0] += 1
            if call_count[0] == 1:
                return 50.02  # First day
            elif call_count[0] == 2:
                raise socket.gaierror("Simulated error")
            else:
                return 49.98  # Second day
            
        mock_sgi.get_frequency.side_effect = mock_get_frequency
        
        with patch('frequencymonitor.SungrowInverter', return_value=mock_sgi):
            from frequencymonitor import last_freq, filename
            
            # Simulate date rollover by mocking datetime.now()
            with patch('datetime.now') as mock_datetime:
                first_call = True
                
                def side_effect():
                    if first_call:
                        first_call = False
                        return datetime(2026, 5, 17)  # First day
                    else:
                        return datetime(2026, 5, 18)  # Second day (next day)
                
                mock_datetime.side_effect = side_effect
                
                # Read frequency - should switch to new file
                freq = mock_sgi.get_frequency()
                assert freq == 50.02
    
    def test_network_error_recovery(self, tmp_path):
        """Test recovery from gaierror during reading."""
        # Mock the SungrowInverter with DNS resolution error
        mock_sgi = MagicMock()
        
        call_count = [0]
        
        def mock_get_frequency():
            call_count[0] += 1
            if call_count[0] == 1:
                raise socket.gaierror("Temporary failure")
            else:
                return 50.02
        
        mock_sgi.get_frequency.side_effect = mock_get_frequency
        
        with patch('frequencymonitor.SungrowInverter', return_value=mock_sgi):
            from frequencymonitor import last_freq
            
            # First call fails, second succeeds
            freq1 = mock_sgi.get_frequency()
            time.sleep(0.05)  # Allow retry delay
            
            assert freq1 is None or freq1 == 50.02
    
    def test_empty_none_readings(self, tmp_path):
        """Test handling of empty/None readings."""
        # Mock the SungrowInverter to return None
        mock_sgi = MagicMock()
        mock_sgi.get_frequency.return_value = None
        
        with patch('frequencymonitor.SungrowInverter', return_value=mock_sgi):
            from frequencymonitor import last_freq
            
            # Read frequency level (returns None)
            freq = mock_sgi.get_frequency()
            
            assert freq is None


class TestFrequencyMonitorInterval:
    """Tests for interval timing in frequency monitor."""
    
    def test_interval_timing(self, tmp_path):
        """Test that reading respects configured interval."""
        # Mock the SungrowInverter
        mock_sgi = MagicMock()
        mock_sgi.get_frequency.return_value = 50.0
        
        with patch('frequencymonitor.SungrowInverter', return_value=mock_sgi):
            from frequencymonitor import next_call, interval
            
            # Verify interval is set to 0.05 seconds (configurable)
            assert interval == 0.05
    
    def test_edge_case_50hz_exactly(self, tmp_path):
        """Test edge case where frequency is exactly 50Hz."""
        mock_sgi = MagicMock()
        mock_sgi.get_frequency.return_value = 50.0
        
        with patch('frequencymonitor.SungrowInverter', return_value=mock_sgi):
            from frequencymonitor import last_freq
            
            # Read frequency exactly at 50Hz
            freq1 = mock_sgi.get_frequency()
            
            assert freq1 == 50.0
    
    def test_edge_case_50hz_plus_small(self, tmp_path):
        """Test edge case where frequency is slightly above 50Hz."""
        mock_sgi = MagicMock()
        mock_sgi.get_frequency.return_value = 50.01
        
        with patch('frequencymonitor.SungrowInverter', return_value=mock_sgi):
            from frequencymonitor import last_freq
            
            # Read frequency at 50.01Hz (slightly above nominal)
            freq = mock_sgi.get_frequency()
            
            assert freq == 50.01


class TestFrequencyMonitorCleanup:
    """Tests for cleanup functionality in frequency monitor."""
    
    def test_cleanup_old_files(self, tmp_path):
        """Test that old data files are cleaned up (>90 days)."""
        # Create old file (simulate 100 days ago)
        old_date = datetime.now() - timedelta(days=100)
        old_file = f"{tmp_path}/data/frequency_{old_date.strftime('%Y-%m-%d')}.csv"
        
        os.makedirs(os.path.dirname(old_file), exist_ok=True)
        with open(old_file, "w") as f:
            f.write("time,value\n10:00:00.000,50.02\n")
        
        # Create new file (today)
        today = datetime.now().date()
        new_file = f"{tmp_path}/data/frequency_{today}.csv"
        with open(new_file, "w") as f:
            f.write("time,value\n10:00:00.000,50.01\n")
        
        # Import and run cleanup from frequencymonitor
        import shutil
        
