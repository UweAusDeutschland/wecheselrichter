"""
test_monitor_base.py — Unit tests for monitor_base utilities

Tests coverage target: >95%
Focus areas:
- test_port() retry logic edge cases
- cleanup_old_csv_files() retention scenarios  
- resolve_with_retry() DNS failure handling
"""

import os
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, mock_open
import pytest
from io import StringIO

# Import functions to test from monitor_base
from monitor_base import (
    ConnectionConfig,
    resolve_with_retry,
    test_port,
    cleanup_old_csv_files,
)


class TestConnectionConfig:
    """Tests for ConnectionConfig dataclass."""
    
    def test_connection_config_defaults(self):
        """Test default values for ConnectionConfig."""
        config = ConnectionConfig(hostname="192.168.0.1")
        assert config.hostname == "192.168.0.1"
        assert config.port == 502
        assert config.description == ""
    
    def test_connection_config_custom(self):
        """Test custom values for ConnectionConfig."""
        config = ConnectionConfig(
            hostname="modbus.inverter.local",
            port=502,
            description="Main Inverter"
        )
        assert config.hostname == "modbus.inverter.local"
        assert config.port == 502
        assert config.description == "Main Inverter"


class TestResolveWithRetry:
    """Tests for resolve_with_retry() DNS resolution with retries."""
    
    def test_resolve_success_immediate(self):
        """Test successful DNS resolution on first attempt."""
        mock_socket = MagicMock()
        mock_socket.getaddrinfo.return_value = [('', '', 'tcp', 0, ('192.168.0.100', None))]
        
        with patch('socket.getaddrinfo', mock_socket):
            result = resolve_with_retry("example.local", retries=3, delay=0.5)
            
        assert result == "192.168.0.100"
    
    def test_resolve_success_after_retries(self):
        """Test successful resolution after initial failures."""
        call_count = [0]
        
        def mock_getaddrinfo(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 2:
                raise socket.gaierror("Temporary failure")
            return [('', '', 'tcp', 0, ('192.168.0.100', None))]
        
        with patch('socket.getaddrinfo', mock_getaddrinfo):
            result = resolve_with_retry("example.local", retries=3, delay=0.5)
            
        assert result == "192.168.0.100"
        assert call_count[0] == 2
    
    def test_resolve_all_failures(self):
        """Test resolution failing after all retries."""
        def mock_getaddrinfo(*args, **kwargs):
            raise socket.gaierror("Temporary failure")
        
        with patch('socket.getaddrinfo', mock_getaddrinfo):
            with pytest.raises(RuntimeError) as exc_info:
                resolve_with_retry("example.local", retries=2, delay=0.1)
            
        assert "Could not resolve host after 2 attempts" in str(exc_info.value)


class TestTestPort:
    """Tests for test_port() port connectivity checking."""
    
    def test_port_reachable(self):
        """Test that reachable ports return True."""
        mock_socket = MagicMock()
        mock_socket.create_connection.return_value.close.return_value = None
        
        with patch('socket.create_connection', mock_socket.create_connection):
            result = test_port("127.0.0.1", 502, retries=1, delay=0.1)
            
        assert result is True
    
    def test_port_not_reachable(self):
        """Test that unreachable ports return False."""
        mock_socket = MagicMock()
        mock_socket.create_connection.side_effect = ConnectionRefusedError("Connection refused")
        
        with patch('socket.create_connection', mock_socket.create_connection):
            result = test_port("127.0.0.1", 502, retries=1, delay=0.1)
            
        assert result is False
    
    def test_port_timeout_error(self):
        """Test handling of timeout errors."""
        mock_socket = MagicMock()
        mock_socket.create_connection.side_effect = TimeoutError("Connection timed out")
        
        with patch('socket.create_connection', mock_socket.create_connection):
            result = test_port("127.0.0.1", 502, retries=1, delay=0.1)
            
        assert result is False
    
    def test_port_reachable_after_retries(self):
        """Test port becomes reachable after initial failures."""
        call_count = [0]
        
        def mock_create_connection(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionRefusedError("Not ready yet")
            result = MagicMock()
            result.close.return_value = None
            return result
        
        with patch('socket.create_connection', mock_create_connection):
            result = test_port("127.0.0.1", 502, retries=3, delay=0.1)
            
        assert result is True


class TestCleanupOldCsvFiles:
    """Tests for cleanup_old_csv_files() retention policy."""
    
    def test_cleanup_removes_old_files(self):
        """Test that files older than retention period are deleted."""
        # Create test directory with old and new files
        base_dir = "test_data_temp"
        os.makedirs(base_dir, exist_ok=True)
        
        try:
            # Create old file (100 days ago)
            old_file = f"{base_dir}/battery_2025-01-01.csv"
            with open(old_file, "w") as f:
                f.write("time,value\n10:00:00.000,75\n")
            
            # Create new file (today)
            today = datetime.now().strftime("%Y-%m-%d")
            new_file = f"{base_dir}/battery_{today}.csv"
            with open(new_file, "w") as f:
                f.write("time,value\n10:00:00.000,80\n")
            
            # Create another old file (95 days ago) - should be kept
            old_file_2 = f"{base_dir}/battery_2026-01-15.csv"  # Only 3 weeks old
            with open(old_file_2, "w") as f:
                f.write("time,value\n10:00:00.000,82\n")
            
            # Run cleanup (90 day retention)
            cutoff_date = datetime.now() - timedelta(days=90)
            files_before = os.listdir(base_dir)
            cleanup_old_csv_files(base_dir=base_dir, prefix="battery_", retention_days=90)
            files_after = os.listdir(base_dir)
            
            # Verify old file deleted, new and recent kept
            assert len(files_before) == 3
            assert len(files_after) == 2
            assert old_file not in files_after
            assert new_file in files_after
            assert old_file_2 in files_after
            
        finally:
            # Cleanup test directory
            if os.path.exists(base_dir):
                import shutil
                shutil.rmtree(base_dir)
    
    def test_cleanup_keeps_recent_files(self):
        """Test that recent files are kept regardless of retention."""
        base_dir = "test_data_temp_2"
        os.makedirs(base_dir, exist_ok=True)
        
        try:
            # Create file from 5 days ago (within retention period)
            five_days_ago = datetime.now() - timedelta(days=5)
            recent_file = f"{base_dir}/battery_{five_days_ago.strftime('%Y-%m-%d')}.csv"
            with open(recent_file, "w") as f:
                f.write("time,value\n10:00:00.000,78\n")
            
            # Create file from 2 days ago
            two_days_ago = datetime.now() - timedelta(days=2)
            recent_file_2 = f"{base_dir}/battery_{two_days_ago.strftime('%Y-%m-%d')}.csv"
            with open(recent_file_2, "w") as f:
                f.write("time,value\n10:00:00.000,79\n")
            
            # Run cleanup (90 day retention)
            cleanup_old_csv_files(base_dir=base_dir, prefix="battery_", retention_days=90)
            
            # Both files should still exist
            assert os.path.exists(recent_file)
            assert os.path.exists(recent_file_2)
            
        finally:
            if os.path.exists(base_dir):
                import shutil
                shutil.rmtree(base_dir)
    
    def test_cleanup_respects_prefix(self):
        """Test that non-matching prefix files are not affected."""
        base_dir = "test_data_temp_3"
        os.makedirs(base_dir, exist_ok=True)
        
        try:
            # Create old file with wrong prefix
            wrong_prefix_file = f"{base_dir}/other_2025-01-01.csv"
            with open(wrong_prefix_file, "w") as f:
                f.write("data\n")
            
            # Create old battery file (should be deleted)
            old_battery = f"{base_dir}/battery_2025-01-01.csv"
            with open(old_battery, "w") as f:
                f.write("time,value\n10:00:00.000,75\n")
            
            # Run cleanup
            cutoff_date = datetime.now() - timedelta(days=90)
            cleanup_old_csv_files(base_dir=base_dir, prefix="battery_", retention_days=90)
            
            # Wrong prefix file should still exist
            assert os.path.exists(wrong_prefix_file)
            # Battery file should be deleted
            assert not os.path.exists(old_battery)
            
        finally:
            if os.path.exists(base_dir):
                import shutil
                shutil.rmtree(base_dir)
    
    def test_cleanup_respects_suffix(self):
        """Test that non-matching suffix files are not affected."""
        base_dir = "test_data_temp_4"
        os.makedirs(base_dir, exist_ok=True)
        
        try:
            # Create old file with wrong suffix (.txt instead of .csv)
            wrong_suffix_file = f"{base_dir}/battery_2025-01-01.txt"
            with open(wrong_suffix_file, "w") as f:
                f.write("data\n")
            
            # Create old battery file (should be deleted)
            old_battery = f"{base_dir}/battery_2025-01-01.csv"
            with open(old_battery, "w") as f:
                f.write("time,value\n10:00:00.000,75\n")
            
            # Run cleanup
            cutoff_date = datetime.now() - timedelta(days=90)
            cleanup_old_csv_files(base_dir=base_dir, prefix="battery_", retention_days=90)
            
            # Wrong suffix file should still exist
            assert os.path.exists(wrong_suffix_file)
            # CSV file should be deleted
            assert not os.path.exists(old_battery)
            
        finally:
            if os.path.exists(base_dir):
                import shutil
                shutil.rmtree(base_dir)
    
    def test_cleanup_with_retention_edge(self):
        """Test retention boundary - files exactly at cutoff are kept."""
        base_dir = "test_data_temp_5"
        os.makedirs(base_dir, exist_ok=True)
        
        try:
            # Create file from exactly 90 days ago (should be KEPT)
            ninety_days_ago = datetime.now() - timedelta(days=90)
            boundary_file = f"{base_dir}/battery_{ninety_days_ago.strftime('%Y-%m-%d')}.csv"
            with open(boundary_file, "w") as f:
                f.write("time,value\n10:00:00.000,75\n")
            
            # Create file from 91 days ago (should be DELETED)
            ninety_one_days_ago = datetime.now() - timedelta(days=91)
            beyond_file = f"{base_dir}/battery_{ninety_one_days_ago.strftime('%Y-%m-%d')}.csv"
            with open(beyond_file, "w") as f:
                f.write("time,value\n10:00:00.000,75\n")
            
            # Run cleanup (90 day retention)
            cutoff_date = datetime.now() - timedelta(days=90)
            cleanup_old_csv_files(base_dir=base_dir, prefix="battery_", retention_days=90)
            
            # File at exactly 90 days should be kept
            assert os.path.exists(boundary_file)
            # File beyond 90 days should be deleted
            assert not os.path.exists(beyond_file)
            
        finally:
            if os.path.exists(base_dir):
                import shutil
                shutil.rmtree(base_dir)
    
    def test_cleanup_with_nonexistent_dir(self):
        """Test cleanup handles non-existent directory gracefully."""
        nonexistent_dir = "/nonexistent/path/that/does/not/exist"
        
        # Should not raise exception
        with patch('os.listdir') as mock_listdir:
            mock_listdir.side_effect = FileNotFoundError("No such file or directory")
            
            cleanup_old_csv_files(base_dir=nonexistent_dir, prefix="battery_", retention_days=90)

