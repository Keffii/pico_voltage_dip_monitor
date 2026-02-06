# Data formats

## pico_medians.csv
Long format. Logged only when stable.

Header:
time_s,channel,median_V

Example:
12.300,PLC,1.274
12.300,MODEM,1.281
12.300,BATTERY,1.268

## pico_dips.csv
One row per completed dip event.

Header:
channel,dip_start_s,dip_end_s,duration_ms,baseline_V,min_V,drop_V

Example:
BATTERY,18.420,18.470,50,1.274,1.112,0.162
