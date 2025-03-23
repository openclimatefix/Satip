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

# GOES ABI bands
GOES_ABI_BANDS = [
    "C01",  # 0.47 μm - Blue
    "C02",  # 0.64 μm - Red
    "C03",  # 0.86 μm - Veggie
    "C04",  # 1.37 μm - Cirrus
    "C05",  # 1.6 μm - Snow/Ice
    "C06",  # 2.2 μm - Cloud Particle Size
    "C07",  # 3.9 μm - Shortwave Window
    "C08",  # 6.2 μm - Upper-Level Water Vapor
    "C09",  # 6.9 μm - Mid-Level Water Vapor
    "C10",  # 7.3 μm - Lower-Level Water Vapor
    "C11",  # 8.4 μm - Cloud-Top Phase
    "C12",  # 9.6 μm - Ozone
    "C13",  # 10.3 μm - Clean IR Longwave Window
    "C14",  # 11.2 μm - IR Longwave Window
    "C15",  # 12.3 μm - Dirty Longwave Window
    "C16",  # 13.3 μm - CO2 Longwave
]

# Himawari AHI bands
HIMAWARI_AHI_BANDS = [
    "B01",  # 0.47 μm - Blue
    "B02",  # 0.51 μm - Green
    "B03",  # 0.64 μm - Red
    "B04",  # 0.86 μm - Veggie
    "B05",  # 1.6 μm - Snow/Ice
    "B06",  # 2.3 μm - Cloud Particle Size
    "B07",  # 3.9 μm - Shortwave Window
    "B08",  # 6.2 μm - Upper-Level Water Vapor
    "B09",  # 6.9 μm - Mid-Level Water Vapor
    "B10",  # 7.3 μm - Lower-Level Water Vapor
    "B11",  # 8.6 μm - Cloud-Top Phase
    "B12",  # 9.6 μm - Ozone
    "B13",  # 10.4 μm - Clean IR Longwave Window
    "B14",  # 11.2 μm - IR Longwave Window
    "B15",  # 12.4 μm - Dirty Longwave Window
    "B16",  # 13.3 μm - CO2 Longwave
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

# GOES product IDs
GOES_16_ID = "GOES-16"  # GOES-East
GOES_17_ID = "GOES-17"  # GOES-West
GOES_18_ID = "GOES-18"  # GOES-West (replaced GOES-17)

# GOES product types
GOES_ABI_L1B_RADF = "ABI-L1b-RadF"  # Full Disk
GOES_ABI_L1B_RADC = "ABI-L1b-RadC"  # CONUS
GOES_ABI_L1B_RADM = "ABI-L1b-RadM"  # Mesoscale
GOES_ABI_L2_CMIPF = "ABI-L2-CMIPF"  # Cloud and Moisture Imagery

# Himawari product IDs
HIMAWARI_8_ID = "Himawari-8"
HIMAWARI_9_ID = "Himawari-9"

# Himawari product types
HIMAWARI_AHI_L1B_FLDK = "AHI-L1b-FLDK"  # Full Disk
HIMAWARI_AHI_L1B_JP01 = "AHI-L1b-JP01"  # Japan Area
HIMAWARI_AHI_L1B_TARG = "AHI-L1b-TARG"  # Target Area
