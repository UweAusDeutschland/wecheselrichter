import pandas as pd
import matplotlib.pyplot as plt

# Daten laden
df = pd.read_csv("freq_log.csv", names=["time", "freq"], parse_dates=["time"])

# Liniendiagramm zeichnen
plt.figure(figsize=(12,4))
plt.plot(df["time"], df["freq"], drawstyle="steps-post")
plt.xlabel("Zeit")
plt.ylabel("Frequenz (Hz)")
plt.title("Netzfrequenz Tagesverlauf")
plt.grid(True)
plt.show()