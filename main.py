# Initialisierung
from sungrowinverter import SungrowInverter


inverter = SungrowInverter(host="modbusSungrow.fritz.box")

# Werte abrufen
freq = inverter.get_frequency()


print(f"Netzfrequenz: {freq} Hz")