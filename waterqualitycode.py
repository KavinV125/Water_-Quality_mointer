import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import time
import serial

# -----------------------------------------
#  I2C Setup for ADS1115
# -----------------------------------------
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ads.gain = 1     # 4.096V full-scale

# -----------------------------------------
#  Sensor Channel Mapping (Correct)
# -----------------------------------------
ph_sensor = AnalogIn(ads, 0)        # Channel A0
turbidity_sensor = AnalogIn(ads, 1) # Channel A1
orp_sensor = AnalogIn(ads, 2)       # Channel A2
tds_sensor = AnalogIn(ads, 3)       # Channel A3

# -----------------------------------------
#  pH Calibration Values (Adjust if needed)
# -----------------------------------------
ph_4_voltage = 2.056
ph_7_voltage = 1.563

# -----------------------------------------
#  Serial Ports
# -----------------------------------------
ser_nextion = serial.Serial('/dev/ttyS0', 9600, timeout=1)      # For Nextion HMI
ser_pc = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)       # To PC via USB

eof = b"\xff\xff\xff"   # Nextion command terminator

# -----------------------------------------
#  Main Loop
# -----------------------------------------
try:
    while True:

        # -------- pH Sensor Calculation ----------
        raw_ph = ph_sensor.value
        voltage_ph = (raw_ph * 4.096) / 32767.0

        slope = (ph_7_voltage - ph_4_voltage) / 3
        offset = ph_4_voltage - (slope * 4)
        ph_value = (voltage_ph - offset) / slope

        # -------- Turbidity Calculation ----------
        raw_tur = turbidity_sensor.value
        turbidity = (raw_tur / 65535) * 1000  # NTU

        # -------- ORP Calculation ----------
        raw_orp = orp_sensor.value
        orp_mV = (raw_orp / 65535) * 600  # mV

        # -------- TDS Calculation ----------
        raw_tds = tds_sensor.value
        tds_ppm = (raw_tds / 65535) * 5000  # ppm

        # -------- Prepare Display String ----------
        sensor_string = (
            f"pH={ph_value:.2f}, "
            f"Turbidity={turbidity:.2f}NTU, "
            f"ORP={orp_mV:.2f}mV, "
            f"TDS={tds_ppm:.2f}ppm\n"
        )

        # -------- Send to PC via USB Serial (PySerial) --------
        ser_pc.write(sensor_string.encode())
        print("PC USB →", sensor_string.strip())

        # -------- Send to Nextion Display --------
        ser_nextion.write(f'page0.t5.txt="{ph_value:.2f}"'.encode() + eof)
        ser_nextion.write(f'page0.t6.txt="{turbidity:.2f}"'.encode() + eof)
        ser_nextion.write(f'page0.t7.txt="{orp_mV:.2f}"'.encode() + eof)
        ser_nextion.write(f'page0.t8.txt="{tds_ppm:.2f}"'.encode() + eof)

        time.sleep(1)

except KeyboardInterrupt:
    print("\nStopped by user")

except Exception as e:
    print("Error:", e)
