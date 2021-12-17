import satpy
from satpy import Scene, available_readers

print(available_readers())

decompressed_nat = "/run/timeshift/backup/MSG3-SEVI-MSG15-0100-NA-20210103235915.986000000Z-NA.nat"
grb = "/run/timeshift/backup/MSG3-SEVI-MSGCLMK-0100-0100-20210104000000.000000000Z-NA.grb"

scene = Scene(filenames={"seviri_l1b_native": [decompressed_nat], "seviri_l2_grib": [grb]})
