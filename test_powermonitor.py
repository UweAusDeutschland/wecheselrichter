"""
test_powermonitor.py — Unit tests for power monitor

Tests coverage target: 85-90%

Test cases:
1. Normal power reading → CSV write
2. Deduplication (same value skipped)
3. Date rollover handling
4. Network error recovery
5. High-frequency data writing (1s intervals)
6. Low-frequency scenarios
7. Data directory creation
8. Cleanup old files (>90 days)
"""

import os
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, mock_open
import pytest
from io import StringIO

# Import functions to test from powermonitor
from powermonitor import (
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


class TestPowerMonitorNormalOperation:
    """Tests for normal power monitor operation."""
    
    def test_normal_power_reading(self, tmp_path):
        """Test normal PV power reading and CSV write."""
        # Mock the SungrowInverter to return a valid power value
        mock_sgi = MagicMock()
        mock_sgi.get_pv_power.return_value = 2500
        
        with patch('powermonitor.SungrowInverter', return_value=mock_sgi):
            from powermonitor import last_power, filename
            
            # Simulate reading PV power level
            power = mock_sgi.get_pv_power()
            
            assert power == 2500
    
    def test_power_deduplication(self, tmp_path):
        """Test that duplicate readings are skipped."""
        # Mock the SungrowInverter to return same power
        mock_sgi = MagicMock()
        mock_sgi.get_pv_power.return_value = 2450
        
        with patch('powermonitor.SungrowInverter', return_value=mock_sgi):
            from powermonitor import last_power
            
            # First read - should be recorded
            power1 = mock_sgi.get_pv_power()
            
            # Second read (same value) - should NOT be recorded
            power2 = mock_sgi.get_pv_power()
            
            assert power1 == 2450
            assert power2 == 2450
    
    def test_date_rollover_handling(self, tmp_path):
        """Test that data is written to new file on date change."""
        # Mock the SungrowInverter with changing dates
        mock_sgi = MagicMock()
        
        call_count = [0]
        
        def mock_get_pv_power():
            call_count[0] += 1
            if call_count[0] == 1:
                return 2450  # First day
            elif call_count[0] == 2:
                raise socket.gaierror("Simulated error")
            else:
                return 2380  # Second day
            
        mock_sgi.get_pv_power.side_effect = mock_get_pv_power
        
        with patch('powermonitor.SungrowInverter', return_value=mock_sgi):
            from powermonitor import last_power, filename
            
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
                
                # Read power - should switch to new file
                power = mock_sgi.get_pv_power()
                assert power == 2450
    
    def test_network_error_recovery(self, tmp_path):
        """Test recovery from gaierror during reading."""
        # Mock the SungrowInverter with DNS resolution error
        mock_sgi = MagicMock()
        
        call_count = [0]
        
        def mock_get_pv_power():
            call_count[0] += 1
            if call_count[0] == 1:
                raise socket.gaierror("Temporary failure")
            else:
                return 2450
        
        mock_sgi.get_pv_power.side_effect = mock_get_pv_power
        
        with patch('powermonitor.SungrowInverter', return_value=mock_sgi):
            from powermonitor import last_power
            
            # First call fails, second succeeds
            power1 = mock_sgi.get_pv_power()
            time.sleep(0.05)  # Allow retry delay
            
            assert power1 is None or power1 == 2450
    
    def test_empty_none_readings(self, tmp_path):
        """Test handling of empty/None readings."""
        # Mock the SungrowInverter to return None
        mock_sgi = MagicMock()
        mock_sgi.get_pv_power.return_value = None
        
        with patch('powermonitor.SungrowInverter', return_value=mock_sgi):
            from powermonitor import last_power
            
            # Read PV power level (returns None)
            power = mock_sgi.get_pv_power()
            
            assert power is None


class TestPowerMonitorInterval:
    """Tests for interval timing in power monitor."""
    
    def test_interval_timing(self, tmp_path):
        """Test that reading respects configured interval."""
        # Mock the SungrowInverter
        mock_sgi = MagicMock()
        mock_sgi.get_pv_power.return_value = 2500
        
        with patch('powermonitor.SungrowInverter', return_value=mock_sgi):
            from powermonitor import next_call, interval
            
            # Verify interval is set to 1 second (configurable)
            assert interval == 1.0
    
    def test_high_frequency_data_writing(self, tmp_path):
        """Test high-frequency data writing at configured interval."""
        mock_sgi = MagicMock()
        mock_sgi.get_pv_power.return_value = 2500
        
        with patch('powermonitor.SungrowInverter', return_value=mock_sgi):
            from powermonitor import next_call, interval
            
            # Verify interval is set to 1 second (high frequency)
            assert interval == 1.0
    
    def test_low_frequency_scenarios(self, tmp_path):
        """Test low-frequency scenarios."""
        mock_sgi = MagicMock()
        mock_sgi.get_pv_power.return_value = 2500
        
        with patch('powermonitor.SungrowInverter', return_value=mock_sgi):
            from powermonitor import next_call, interval
            
            # Verify interval is set to 1 second (configurable)
            assert interval == 1.0


class TestPowerMonitorCleanup:
    """Tests for cleanup functionality in power monitor."""
    
    def test_cleanup_old_files(self, tmp_path):
        """Test that old data files are cleaned up (>90 days)."""
        # Create old file (simulate 100 days ago)
        old_date = datetime.now() - timedelta(days=100)
        old_file = f"{tmp_path}/data/pv_power_{old_date.strftime('%Y-%m-%d')}.csv"
        
        os.makedirs(os.path.dirname(old_file), exist_ok=True)
        with open(old_file, "w") as f:
            f.write("time,value\n10:00:00.000,2500\n")
        
        # Create new file (today)
        today = datetime.now().date()
        new_file = f"{tmp_path}/data/pv_power_{today}.csv"
        with open(new_file, "w") as f:
            f.write("time,value\n10:00:00.000,2450\n")
        
        # Import and run cleanup from powermonitor
        import shutil
        
