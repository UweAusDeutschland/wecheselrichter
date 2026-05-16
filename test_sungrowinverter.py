"""
Test-Suite für die SungrowInverter-Klasse
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sungrowinverter import SungrowInverter


@pytest.fixture
def mock_modbus_client():
    """Mock für ModbusClient"""
    with patch('sungrowinverter.ModbusClient') as mock:
        yield mock


def test_sungrowinverter_init(mock_modbus_client):
    """Test: SungrowInverter kann initialisiert werden"""
    inverter = SungrowInverter(host="192.168.1.1")
    assert inverter is not None
    assert inverter.registers['frequency'] == 5241
    assert inverter.registers['pv_power'] == 5016
    assert inverter.registers['battery'] == 13022


def test_get_frequency(mock_modbus_client):
    """Test: get_frequency() gibt korrekten Wert zurück"""
    # Mock: read_input_registers zurückgeben
    mock_instance = MagicMock()
    mock_instance.read_input_registers.return_value = [5000]  # 50.00 Hz
    mock_modbus_client.return_value = mock_instance
    
    inverter = SungrowInverter(host="192.168.1.1")
    inverter.client = mock_instance
    
    freq = inverter.get_frequency()
    assert freq == 50.0


def test_get_frequency_none(mock_modbus_client):
    """Test: get_frequency() gibt None zurück bei Fehler"""
    mock_instance = MagicMock()
    mock_instance.read_input_registers.return_value = None
    mock_modbus_client.return_value = mock_instance
    
    inverter = SungrowInverter(host="192.168.1.1")
    inverter.client = mock_instance
    
    freq = inverter.get_frequency()
    assert freq is None


def test_get_pv_power(mock_modbus_client):
    """Test: get_pv_power() gibt korrekten Wert zurück"""
    mock_instance = MagicMock()
    # Little-endian 32-bit: 2500W = [3928, 0] oder ähnlich
    mock_instance.read_input_registers.return_value = [3928, 0]
    mock_modbus_client.return_value = mock_instance
    
    inverter = SungrowInverter(host="192.168.1.1")
    inverter.client = mock_instance
    
    power = inverter.get_pv_power()
    assert power == 3928


def test_get_pv_power_none(mock_modbus_client):
    """Test: get_pv_power() gibt None zurück bei Fehler"""
    mock_instance = MagicMock()
    mock_instance.read_input_registers.return_value = None
    mock_modbus_client.return_value = mock_instance
    
    inverter = SungrowInverter(host="192.168.1.1")
    inverter.client = mock_instance
    
    power = inverter.get_pv_power()
    assert power is None


def test_get_battery_level(mock_modbus_client):
    """Test: get_battery_level() gibt korrekten Wert zurück"""
    mock_instance = MagicMock()
    mock_instance.read_input_registers.return_value = [855]  # 85.5%
    mock_modbus_client.return_value = mock_instance
    
    inverter = SungrowInverter(host="192.168.1.1")
    inverter.client = mock_instance
    
    battery = inverter.get_battery_level()
    assert battery == 85.5


def test_get_battery_level_none(mock_modbus_client):
    """Test: get_battery_level() gibt None zurück bei Fehler"""
    mock_instance = MagicMock()
    mock_instance.read_input_registers.return_value = None
    mock_modbus_client.return_value = mock_instance
    
    inverter = SungrowInverter(host="192.168.1.1")
    inverter.client = mock_instance
    
    battery = inverter.get_battery_level()
    assert battery is None
