import time
from sungrowinverter import SungrowInverter
from datetime import datetime


last_freq = None
interval = 0.05
next_call = time.time()
sgi = SungrowInverter(host="modbusSungrow.fritz.box")
current_day = datetime.now().date()
filename = f"data/frequency_{current_day}.csv"

try:
    while True:
        freq = sgi.get_frequency()
        now = datetime.now()
        if freq is not None and freq != last_freq:
            if now.date() != current_day:
                current_day = now.date()
                filename = f"data/frequency_{current_day}.csv"
            with open(filename, "a") as f:
                now = datetime.now()
                time_str = now.strftime('%H:%M:%S.%f')[:-3]  # Nur bis Millisekunden
                f.write(f"{time_str},{freq:.2f}\n")
            last_freq = freq
        next_call += interval
        sleep_time = max(0,next_call-time.time())
        time.sleep(sleep_time)  # Intervall in Sekunden
except KeyboardInterrupt:
    print("Überwachung beendet.")
except Exception as e:
    print("Shuting down of error.")
    print(e)
