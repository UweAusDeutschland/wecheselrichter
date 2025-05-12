from pymodbus.client import ModbusTcpClient

INVERTER_IP = 'modbusSungrow.fritz.box'  # Hier deine echte IP-Adresse eintragen
PORT = 502
UNIT_ID = 1

REGISTER_FREQUENCY = 4999      # Register für Netzfrequenz
REGISTER_PV_POWER = 3004       # Register für PV-Leistung
REGISTER_BATTERY_LEVEL = 3700  # Register für Batteriestand

client = ModbusTcpClient(INVERTER_IP, port=PORT)

if client.connect():
    freq = client.read_input_registers(REGISTER_FREQUENCY, 1, unit=UNIT_ID)
    pv_power = client.read_input_registers(REGISTER_PV_POWER, 1, unit=UNIT_ID)
    battery = client.read_input_registers(REGISTER_BATTERY_LEVEL, 1, unit=UNIT_ID)
    response = client.read_input_registers(4999, 1, unit=1)
    print('Fehlermeldung', response)
    print('Netzfrequenz:', freq.registers if freq.isError() == False else 'Fehler')
    print('PV-Leistung:', pv_power.registers if pv_power.isError() == False else 'Fehler')
    print('Batteriestand:', battery.registers if battery.isError() == False else 'Fehler')
    client.close()
else:
    print('Verbindung zum Wechselrichter fehlgeschlagen!')
