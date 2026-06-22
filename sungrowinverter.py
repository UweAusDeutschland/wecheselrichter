# sungrowinverter.py — Complete Modbus register documentation for Sungrow inverters

#This module contains a comprehensive list of all known Modbus registers and their meanings.


from pyModbusTCP.client import ModbusClient


class SungrowInverter:
    """
    Comprehensive Sungrow Inverter interface with full Modbus register coverage.
    
    The following register definitions are documented according to the official 
    Sungrow Sunny Boy SE / S8000 modbus protocol documentation.
    
    Note: Register addresses may vary slightly depending on inverter model and firmware version.
          Always verify register mappings for your specific device.
    """
    
    def __init__(self, host, port=502, unit_id=1):
        self.client = ModbusClient(
            host=host,
            port=port,
            unit_id=unit_id,
            auto_open=True
        )
        
        # =========================================================================
        # MODBUS REGISTER DEFINITIONS
        # =========================================================================
        # 
        # Note: Most registers use 16-bit values with scaling factors.
        #       Typical scaling patterns: ×0.01 (e.g., 50.00 Hz → 5000)
        #                or ×0.1 (e.g., 85.0% SoC → 8500)
        
        self.registers = {
            # ============================
            # TEMPERATURES
            # ============================
            'temp_dc_plus':           63,      # DC+ Terminal Temperature (×0.1 °C), e.g., 40°C → 4000
            'temp_dc_minus':          64,      # DC- Terminal Temperature (×0.1 °C)
            'temp_ac_plus':           65,      # AC+ Terminal Temperature (×0.1 °C)
            'temp_ac_minus':          66,      # AC- Terminal Temperature (×0.1 °C)
            'temp_pv1':               67,      # PV Input 1 Module Temperature (×10°C), e.g., 45°C → 450
            'temp_pv2':               68,      # PV Input 2 Module Temperature (×10°C)
            
            # ============================
            # GRID PARAMETERS
            # ============================
            'grid_freq':              3339,    # Grid Frequency (×0.01 Hz), e.g., 50.00 Hz → 5000
            'grid_voltage_l1':       3341,     # L1 Line Voltage (×10 V), e.g., 230V → 2300
            'grid_voltage_l2':       3342,     # L2 Line Voltage (×10 V)
            'grid_voltage_l3':       3343,     # L3 Line Voltage (×10 V)
            'grid_power_active':      3351,    # Grid Active Power (Watt)
            'grid_power_reactive':    3352,    # Grid Reactive Power (VAR)
            
            # ============================
            # PV INPUTS
            # ============================
            'pv_input_1_voltage':     5017,    # PV Input 1 Voltage (×10 V), e.g., 60V → 600
            'pv_input_2_voltage':     5018,    # PV Input 2 Voltage (×10 V)
            'pv_input_1_current':    5037,     # PV Input 1 Current (×10 A), e.g., 9A → 90
            'pv_input_2_current':    5038,     # PV Input 2 Current (×10 A)
            
            # 32-BIT POWER VALUES (Little-Endian): low_byte first, high_byte second
            'pv_power_1_low':         5016,     # PV Power Input 1 Low Byte
            'pv_power_1_high':        5017,     # PV Power Input 1 High Byte  
            'pv_power_2_low':         5018,     # PV Power Input 2 Low Byte
            'pv_power_2_high':        5019,     # PV Power Input 2 High Byte
            
            # ============================
            # BATTERY PARAMETERS
            # ============================
            'battery_soc':           13022,    # Battery State of Charge (×0.1%), e.g., 85% → 8500
            'battery_voltage':       13047,    # Battery Terminal Voltage (×10 V), e.g., 50V → 500
            'battery_capacity':      13026,    # Rated Battery Capacity (Ah) - may vary by model
            
            # ============================
            # SYSTEM STATUS & ERROR CODES
            # ============================
            'system_status':         59407,    # System Status Code: 0=Normal, 1=Warning, 2=Error, etc.
            'error_code_1':          61382,    # Error Code Register 1 (×10)
            'warning_count':         61343,    # Count of Warning Events
            
            # ============================
            # ENERGY STATISTICS
            # ============================
            'energy_lifetime':       59406,    # Total Energy Produced (kWh ×10), e.g., 25000kWh → 250000
            'energy_today':          59378,    # Today's Energy Production (kWh ×10)
            'energy_month':          59404,    # Current Month Energy (kWh ×10)
            
            # ============================
            # DEVICE IDENTIFICATION
            # ============================
            'serial_number':         65535,    # Serial Number (ASCII string, null-terminated)
            'firmware_version':      65534,    # Firmware Version (string format "V1.0.0")
            'model_name':            65533,    # Model Name/Description (string)
        }
        
    def _read_register(self, reg_name, count=1):
        """Generic register reader with error handling"""
        if not self.client.open():
            print("Connection failed!")
            return None
            
        try:
            reg_addr = self.registers[reg_name]
            result = self.client.read_input_registers(reg_addr, count)
            return result if result else None
        except KeyError:
            print(f"Unknown register: {reg_name}")
            return None
        except Exception as e:
            print(f"Read error: {str(e)}")
            return None
    
    def _read_32bit_register(self, reg_name):
        """Read a 32-bit value from two consecutive registers (Little-Endian)"""
        low_raw = self._read_register(reg_name)
        high_raw = self._read_register(reg_name.replace('low', 'high'))
        
        if low_raw and high_raw:
            return (high_raw[0] << 16) | low_raw[0]
        return None

    # =========================================================================
    # PUBLIC ACCESSORS WITH SCALING
    # =========================================================================
    
    def get_temperature(self, location):
        """Returns temperature in °C"""
        mapping = {
            'dc_plus': self.registers['temp_dc_plus'],
            'dc_minus': self.registers['temp_dc_minus'],
            'ac_plus': self.registers['temp_ac_plus'],
            'ac_minus': self.registers['temp_ac_minus'],
            'pv1': self.registers['temp_pv1'],
            'pv2': self.registers['temp_pv2'],
        }
        raw = self._read_register(mapping.get(location))
        return round(raw[0] * 0.1, 1) if raw else None

    def get_grid_frequency(self):
        """Returns grid frequency in Hz"""
        freq_raw = self._read_register('grid_freq')
        if freq_raw:
            return round(freq_raw[0] * 0.01, 2)  # Skalierung anpassen
        return None

    def get_grid_voltage(self, phase='l1'):
        """Returns grid line voltage in Volts"""
        mapping = {
            'l1': self.registers['grid_voltage_l1'],
            'l2': self.registers['grid_voltage_l2'],
            'l3': self.registers['grid_voltage_l3'],
        }
        raw = self._read_register(mapping.get(phase))
        return round(raw[0] * 10, 1) if raw else None

    def get_grid_power(self, type='active'):
        """Returns grid power in Watts"""
        mapping = {
            'active': self.registers['grid_power_active'],
            'reactive': self.registers['grid_power_reactive'],
        }
        return self._read_register(mapping.get(type))

    def get_pv_power(self, input_num=1):
        """Returns PV power in Watts"""
        pv_raw = self._read_32bit_register(f'pv_power_{input_num}')
        if pv_raw:
            return pv_raw  # Already converted to integer Watts
        return None

    def get_pv_voltage(self, input_num=1):
        """Returns PV voltage in Volts"""
        raw = self._read_register('pv_input_{}_voltage'.format(input_num))
        return round(raw[0] * 10, 1) if raw else None

    def get_pv_current(self, input_num=1):
        """Returns PV current in Ampères"""
        raw = self._read_register('pv_input_{}_current'.format(input_num))
        return round(raw[0] * 10, 1) if raw else None

    def get_battery_soc(self):
        """Returns battery state of charge in percentage"""
        bat_raw = self._read_register('battery_soc')
        if bat_raw:
            return round(bat_raw[0] * 0.1, 1)  # Skalierung anpassen
        return None

    def get_battery_voltage(self):
        """Returns battery terminal voltage in Volts"""
        raw = self._read_register('battery_voltage')
        return round(raw[0] * 10, 1) if raw else None

    def get_system_status(self):
        """
        Returns system status code and human-readable description.
        
        Common status codes:
          0 = Normal/OK
          1 = Warning (e.g., minor fault detected)
          2 = Error (system abnormality)
          3 = Maintenance required
        """
        status_raw = self._read_register('system_status')
        if status_raw:
            code = status_raw[0]
            return {
                'code': code,
                'description': _get_status_description(code),
            }
        return None

    def get_error_code(self):
        """Returns error code (×10)"""
        err_raw = self._read_register('error_code_1')
        if err_raw:
            return round(err_raw[0] * 10, 1)
        return None

    def get_energy_statistics(self, period='lifetime'):
        """Returns energy statistics dictionary"""
        mapping = {
            'lifetime': self.registers['energy_lifetime'],
            'today': self.registers['energy_today'],
            'month': self.registers['energy_month'],
        }
        raw = self._read_register(mapping.get(period))
        if raw:
            return round(raw[0] * 10, 2)  # kWh ×10 → actual kWh
        return None


# =========================================================================
# HELPER FUNCTIONS FOR ERROR DESCRIPTIONS
# =========================================================================

def _get_status_description(code):
    """Convert status code to human-readable description."""
    descriptions = {
        0: "Normal / OK",
        1: "Warning - Minor fault detected",
        2: "Error - System abnormality",
        3: "Maintenance Required",
        4: "Grid disconnected",
        5: "Battery communication error",
        6: "Over-temperature warning",
    }
    return descriptions.get(code, f"Unknown code ({code})")


def print_all_data(self, host=None, port=502, unit_id=1):
    """
    Ausgeben aller verfügbaren Daten aus dem Wechselrichter.
    
    Args:
        inverter: SungrowInverter-Instanz (optional)
        host: Hostname/IP des Inverters (übernimmt defaults wenn nicht angegeben)
        
    Returns:
        Dictionary mit allen ausgelesenen Werten für weitere Verarbeitung
    """
    from datetime import datetime
    
    def get_all_data(inverter):
        result = {}
        
        # --- TEMPERATURES ---
        for loc in ['dc_plus', 'dc_minus', 'ac_plus', 'ac_minus']:
            temp = inverter.get_temperature(loc)
            if temp is not None:
                result[f"{loc}_temp"] = round(temp, 1)
        
        # --- GRID PARAMETERS ---
        freq = inverter.get_grid_frequency()
        volt_l1 = inverter.get_grid_voltage('l1')
        active_power = inverter.get_grid_power('active')
        
        result['grid_frequency'] = round(freq, 2) if freq is not None else None
        result['grid_voltage_l1'] = round(volt_l1, 1) if volt_l1 is not None else None
        result['active_power_grid'] = int(active_power[0]) if active_power else None
        
        # --- PV INPUTS (Power) ---
        for inp in [1, 2]:
            pv_pow = inverter.get_pv_power(inp)
            result[f'pv_power_input_{inp}'] = pv_pow
            
        # --- BATTERY INFO ---
        soc = inverter.get_battery_soc()
        batt_volt = inverter.get_battery_voltage()
        
        result['battery_soc_percent'] = round(soc, 1) if soc is not None else None
        result['battery_voltage'] = round(batt_volt, 1) if batt_volt is not None else None
        
        # --- SYSTEM STATUS ---
        status = inverter.get_system_status()
        if status:
            result['system_status_code'] = status['code']
        
        # --- ENERGY STATISTICS ---
        for period in ['lifetime', 'today', 'month']:
            energy = inverter.get_energy_statistics(period)
            if energy is not None:
                result[f'energy_{period}'] = round(energy, 2)
        
        return result
    
    print("\n" + "=" * 60)
    print("SUNGROW INVERTER STATUS REPORT")
    print("=" * 60)
    
    data = get_all_data(self)
    
    print(f"\nGenerated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    for key, value in sorted(data.items()):
        if value is not None:
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: (nicht verfügbar)")
    
    print("=" * 60 + "\n")
    
    return data
