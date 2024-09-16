"""Constants for utils.py"""
import numpy as np

# Define satellite bands and their min and max values
ALL_BANDS = [
    "HRV",
    "IR_016",
    "IR_039",
    "IR_087",
    "IR_097",
    "IR_108",
    "IR_120",
    "IR_134",
    "VIS006",
    "VIS008",
    "WV_062",
    "WV_073",
]

NON_HRV_BANDS = [
    "IR_016",
    "IR_039",
    "IR_087",
    "IR_097",
    "IR_108",
    "IR_120",
    "IR_134",
    "VIS006",
    "VIS008",
    "WV_062",
    "WV_073",
]

SCALER_MINS = np.array([
    -2.5118103,
    -64.83977,
    63.404694,
    2.844452,
    199.10002,
    -17.254883,
    -26.29155,
    -1.1009827,
    -2.4184198,
    199.57048,
    198.95093,
])

SCALER_MAXS = np.array([
    69.60857,
    339.15588,
    340.26526,
    317.86752,
    313.2767,
    315.99194,
    274.82297,
    93.786545,
    101.34922,
    249.91806,
    286.96323,
])

HRV_SCALER_MIN = np.array([-1.2278595])
HRV_SCALER_MAX = np.array([103.90016])
SAT_VARIABLE_NAMES = (
    "HRV",
    "IR_016",
    "IR_039",
    "IR_087",
    "IR_097",
    "IR_108",
    "IR_120",
    "IR_134",
    "VIS006",
    "VIS008",
    "WV_062",
    "WV_073",
)
NATIVE_FILESIZE_MB = 102.210123
CLOUD_FILESIZE_MB = 3.445185
RSS_ID = "EO:EUM:DAT:MSG:MSG15-RSS"
CLOUD_ID = "EO:EUM:DAT:MSG:RSS-CLM"
SEVIRI_ID = "EO:EUM:DAT:MSG:HRSEVIRI"
SEVIRI_IODC_ID = "EO:EUM:DAT:MSG:HRSEVIRI-IODC"
