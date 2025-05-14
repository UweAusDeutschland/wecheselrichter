from pyModbusTCP.client import ModbusClient

class SungrowInverter:
    def __init__(self, host, port=502, unit_id=1):
        self.client = ModbusClient(
            host=host,
            port=port,
            unit_id=unit_id,
            auto_open=True
        )
        # Register definitions (adjust according to your model's documentation)
        self.registers = {
            'frequency': 5241,    # Frequenz (skaliert ×0.01)
            'pv_power': 5016,     # PV-Leistung (2 Register, 32-Bit)
            'battery': 13022      # Batteriestand (skaliert ×0.1)
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

    def get_frequency(self):
        """Returns grid frequency in Hz"""
        freq_raw = self._read_register('frequency')
        if freq_raw:
            return round(freq_raw[0] * 0.01, 2)  # Skalierung anpassen
        return None

    def get_pv_power(self):
        """Returns current PV power in watts"""
        pv_raw = self._read_register('pv_power', 2)
        if pv_raw and len(pv_raw) >= 2:
            # Little-endian 32-bit conversion
            return (pv_raw[1] << 16) | pv_raw[0]
        return None

    def get_battery_level(self):
        """Returns battery state of charge in percentage"""
        bat_raw = self._read_register('battery')
        if bat_raw:
            return round(bat_raw[0] * 0.1, 1)  # Skalierung anpassen
        return None

if __name__ == "__main__":
    # Example usage
    inverter = SungrowInverter(
        host="modbusSungrow.fritz.box",
        port=502,
        unit_id=1
    )
    
    if freq := inverter.get_frequency():
        print(f"Netzfrequenz: {freq} Hz")
    
    if pv := inverter.get_pv_power():
        print(f"PV-Leistung: {pv} W")
    
    if bat := inverter.get_battery_level():
        print(f"Batteriestand: {bat} %")
