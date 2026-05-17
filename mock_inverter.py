"""
mock_inverter.py — Mock SungrowInverter for unit testing without hardware
"""

from typing import Optional, List, Dict, Any

class MockSungrowInverter:
    """Mock inverter that returns static/test data."""
    
    # Configuration values for testing
    CONFIG = {
        'battery_soc': 75.0,          # Normal battery state of charge (%)
        'battery_soc_full': 100.0,     # Full battery
        'battery_soc_empty': 10.0,      # Empty battery  
        'battery_voltage': 48.5,       # Battery voltage (V)
        
        'grid_frequency': 50.02,       # Grid frequency (Hz) - slightly above nominal
        'grid_voltage_l1': 230.5,      # Line voltage L1 (V)
        'grid_voltage_l2': 228.0,      # Line voltage L2
        'grid_voltage_l3': 231.0,      # Line voltage L3
        
        'active_power_grid': -3500,    # Grid active power (negative = export)
        'reactive_power_grid': 500,     # Reactive power (VAR)
        
        'pv_power_input_1': 2450,      # PV input 1 power (W)
        'pv_power_input_2': 1850,      # PV input 2 power (W)
        'pv_voltage_input_1': 60.5,    # PV input 1 voltage (V)
        'pv_voltage_input_2': 75.0,    # PV input 2 voltage (V)
        'pv_current_input_1': 8.0,     # PV input 1 current (A)
        'pv_current_input_2': 6.0,     # PV input 2 current (A)
        
        'temp_dc_plus': 40.0,          # DC+ terminal temperature (°C)
        'temp_dc_minus': 38.5,         # DC- terminal temperature (°C)
        'temp_ac_plus': 35.0,          # AC+ terminal temperature (°C)
        'temp_ac_minus': 34.5,         # AC- terminal temperature (°C)
        
        'system_status_code': 0,       # 0 = Normal/OK
        'error_code_1': 0.0,           # No active errors
        
        'energy_lifetime': 250000,     # Lifetime energy (kWh ×10 → actual: 25000 kWh)
        'energy_today': 456.8,         # Today's production (kWh ×10 → 45.68 kWh)
        'energy_month': 125000,        # Monthly energy (kWh ×10 → 12500 kWh)
    }
    
    def __init__(self):
        self._data = self.CONFIG.copy()
    
    def get_battery_soc(self) -> Optional[float]:
        """Returns battery state of charge in percentage."""
        return self._data.get('battery_soc')
    
    def get_battery_voltage(self) -> Optional[float]:
        """Returns battery terminal voltage in Volts."""
        return self._data.get('battery_voltage')
    
    def get_grid_frequency(self) -> Optional[float]:
        """Returns grid frequency in Hz."""
        return self._data.get('grid_frequency')
    
    def get_grid_voltage(self, phase: str = 'l1') -> Optional[float]:
        """Returns grid line voltage in Volts."""
        mapping = {
            'l1': self._data['grid_voltage_l1'],
            'l2': self._data['grid_voltage_l2'],
            'l3': self._data['grid_voltage_l3'],
        }
        return mapping.get(phase)
    
    def get_grid_power(self, type: str = 'active') -> Optional[int]:
        """Returns grid power in Watts."""
        if type == 'active':
            return self._data['active_power_grid']
        elif type == 'reactive':
            return self._data['reactive_power_grid']
        return None
    
    def get_pv_power(self, input_num: int = 1) -> Optional[int]:
        """Returns PV power in Watts."""
        key = f'pv_power_input_{input_num}'
        return self._data.get(key)
    
    def get_pv_voltage(self, input_num: int = 1) -> Optional[float]:
        """Returns PV voltage in Volts."""
        mapping = {
            1: self._data['pv_voltage_input_1'],
            2: self._data['pv_voltage_input_2'],
        }
        return mapping.get(input_num)
    
    def get_pv_current(self, input_num: int = 1) -> Optional[float]:
        """Returns PV current in Ampères."""
        mapping = {
            1: self._data['pv_current_input_1'],
            2: self._data['pv_current_input_2'],
        }
        return mapping.get(input_num)
    
    def get_temperature(self, location: str) -> Optional[float]:
        """Returns temperature in °C for specified terminal."""
        mapping = {
            'dc_plus': self._data['temp_dc_plus'],
            'dc_minus': self._data['temp_dc_minus'],
            'ac_plus': self._data['temp_ac_plus'],
            'ac_minus': self._data['temp_ac_minus'],
        }
        return mapping.get(location)
    
    def get_system_status(self) -> Optional[Dict[str, Any]]:
        """Returns system status code and description."""
        if self._data['system_status_code'] == 0:
            return {'code': 0, 'description': 'Normal / OK'}
        elif self._data['system_status_code'] == 1:
            return {'code': 1, 'description': 'Warning - Minor fault detected'}
        else:
            return {'code': self._data['system_status_code'], 
                    'description': f'Unknown code ({self._data["system_status_code"]})'}
    
    def get_error_code(self) -> Optional[float]:
        """Returns error code (×10)."""
        return self._data.get('error_code_1')
    
    def get_energy_statistics(self, period: str = 'lifetime') -> Optional[float]:
        """Returns energy statistics dictionary."""
        mapping = {
            'lifetime': self._data['energy_lifetime'],
            'today': self._data['energy_today'],
            'month': self._data['energy_month'],
        }
        return mapping.get(period)
