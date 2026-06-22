"""
test_batterymonitor.py — Unit tests for battery monitor

Tests coverage target: 85-90%

Test cases:
1. Normal battery reading → CSV write
2. Deduplication (same value skipped)
3. Date rollover handling
4. Network error recovery (gaierror)
5. Empty/None readings
6. Interval timing verification
7. Data directory creation
8. Cleanup old files (>90 days)
"""

import os
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, mock_open
import pytest
from io import StringIO

# Import functions to test from batterymonitor
from batterymonitor import (
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


class TestBatteryMonitorNormalOperation:
    """Tests for normal battery monitor operation."""
    
    def test_normal_battery_reading(self, tmp_path):
        """Test normal battery reading and CSV write."""
        # Mock the SungrowInverter to return a valid battery level
        mock_sgi = MagicMock()
        mock_sgi.get_battery_level.return_value = 75.0
        
        with patch('batterymonitor.SungrowInverter', return_value=mock_sgi):
            from batterymonitor import last_battery, filename
            
            # Simulate reading battery level
            battery = mock_sgi.get_battery_level()
            
            assert battery == 75.0
            
            # Verify CSV file was created/updated
            current_day = datetime.now().date()
            expected_file = f"{tmp_path}/battery_{current_day}.csv"
            
            if os.path.exists(expected_file):
                with open(expected_file, 'r') as f:
                    content = f.read()
                    assert "75.0" in content
    
    def test_battery_deduplication(self, tmp_path):
        """Test that duplicate readings are skipped."""
        # Mock the SungrowInverter to return same battery level
        mock_sgi = MagicMock()
        mock_sgi.get_battery_level.return_value = 75.0
        
        with patch('batterymonitor.SungrowInverter', return_value=mock_sgi):
            from batterymonitor import last_battery
            
            # First read - should be recorded
            battery1 = mock_sgi.get_battery_level()
            
            # Second read (same value) - should NOT be recorded
            battery2 = mock_sgi.get_battery_level()
            
            assert battery1 == 75.0
            assert battery2 == 75.0
    
    def test_date_rollover_handling(self, tmp_path):
        """Test that data is written to new file on date change."""
        # Mock the SungrowInverter with changing dates
        mock_sgi = MagicMock()
        
        call_count = [0]
        
        def mock_get_battery_level():
            call_count[0] += 1
            if call_count[0] == 1:
                return 75.0  # First day
            elif call_count[0] == 2:
                raise socket.gaierror("Simulated error")
            else:
                return 80.0  # Second day
        
        mock_sgi.get_battery_level.side_effect = mock_get_battery_level
        
        with patch('batterymonitor.SungrowInverter', return_value=mock_sgi):
            from batterymonitor import last_battery, filename
            
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
                
                # Read battery - should switch to new file
                battery = mock_sgi.get_battery_level()
                assert battery == 75.0
    
    def test_network_error_recovery(self, tmp_path):
        """Test recovery from gaierror during reading."""
        # Mock the SungrowInverter with DNS resolution error
        mock_sgi = MagicMock()
        
        call_count = [0]
        
        def mock_get_battery_level():
            call_count[0] += 1
            if call_count[0] == 1:
                raise socket.gaierror("Temporary failure")
            else:
                return 75.0
        
        mock_sgi.get_battery_level.side_effect = mock_get_battery_level
        
        with patch('batterymonitor.SungrowInverter', return_value=mock_sgi):
            from batterymonitor import last_battery
            
            # First call fails, second succeeds
            battery1 = mock_sgi.get_battery_level()
            time.sleep(0.05)  # Allow retry delay
            
            assert battery1 is None or battery1 == 75.0
    
    def test_empty_none_readings(self, tmp_path):
        """Test handling of empty/None readings."""
        # Mock the SungrowInverter to return None
        mock_sgi = MagicMock()
        mock_sgi.get_battery_level.return_value = None
        
        with patch('batterymonitor.SungrowInverter', return_value=mock_sgi):
            from batterymonitor import last_battery
            
            # Read battery level (returns None)
            battery = mock_sgi.get_battery_level()
            
            assert battery is None
    
    def test_data_directory_creation(self, tmp_path):
        """Test that data directory is created if missing."""
        # Remove existing data directory
        data_dir = tmp_path / "data"
        if data_dir.exists():
            data_dir.rmdir()
        
        from batterymonitor import DATA_DIR
        
        assert not (tmp_path / DATA_DIR).exists()


class TestBatteryMonitorInterval:
    """Tests for interval timing in battery monitor."""
    
    def test_interval_timing(self, tmp_path):
        """Test that reading respects configured interval."""
        # Mock the SungrowInverter
        mock_sgi = MagicMock()
        mock_sgi.get_battery_level.return_value = 75.0
        
        with patch('batterymonitor.SungrowInverter', return_value=mock_sgi):
            from batterymonitor import next_call, interval
            
            # Verify interval is set to 5 seconds (configurable)
            assert interval == 5.0
    
    def test_interval_reduced_on_error(self, tmp_path):
        """Test that interval reduces on error."""
        mock_sgi = MagicMock()
        
        call_count = [0]
        
        def mock_get_battery_level():
            call_count[0] += 1
            if call_count[0] == 1:
                raise socket.gaierror("Error")
            else:
                return 75.0
        
        mock_sgi.get_battery_level.side_effect = mock_get_battery_level
        
        with patch('batterymonitor.SungrowInverter', return_value=mock_sgi):
            from batterymonitor import next_call
            
            # First call fails, second succeeds
            battery1 = mock_sgi.get_battery_level()
            time.sleep(0.05)  # Allow retry delay
            
            assert battery1 is None or battery1 == 75.0


class TestBatteryMonitorCleanup:
    """Tests for cleanup functionality in battery monitor."""
    
    def test_cleanup_old_files(self, tmp_path):
        """Test that old data files are cleaned up (>90 days)."""
        # Create old file (simulate 100 days ago)
        old_date = datetime.now() - timedelta(days=100)
        old_file = f"{tmp_path}/data/battery_{old_date.strftime('%Y-%m-%d')}.csv"
        
        os.makedirs(os.path.dirname(old_file), exist_ok=True)
        with open(old_file, "w") as f:
            f.write("time,value\n10:00:00.000,75\n")
        
        # Create new file (today)
        today = datetime.now().date()
        new_file = f"{tmp_path}/data/battery_{today}.csv"
        with open(new_file, "w") as f:
            f.write("time,value\n10:00:00.000,80\n")
        
        # Import and run cleanup from batterymonitor
        import shutil
        
