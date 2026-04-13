"""RAK4631 flow-current device payload decoder.

Ported from the legacy ul_formatter.js found in
https://github.com/getdoover/rak4631(flow-current branch).

13-byte fixed-layout payload (big-endian):
    bytes[0..1]  = current reading raw (mA * 1000)
    bytes[2..3]  = count reading (per-period pulse count)
    bytes[4]     = battery voltage (1 LSB = 20 mV)
    bytes[5..6]  = sleep time (seconds)
    bytes[7]     = fast-rate counter (remaining burst-mode uplinks)
    bytes[8..11] = total count (uint32)
    bytes[12]    = battery percent (device-reported)
"""
from __future__ import annotations

EXPECTED_LENGTH = 13


def decode(payload: bytes) -> dict | None:
    if len(payload) != EXPECTED_LENGTH:
        return None

    current_raw = (payload[0] << 8) | payload[1]
    count_reading = (payload[2] << 8) | payload[3]
    batt_mv = payload[4] * 20
    sleep_time_s = (payload[5] << 8) | payload[6]
    fast_rate_counter = payload[7]
    total_count = (
        (payload[8] << 24) | (payload[9] << 16) | (payload[10] << 8) | payload[11]
    )
    batt_percent_reported = payload[12]

    return {
        "current_ma": current_raw / 1000,
        "count_reading": count_reading,
        "battery_v": batt_mv / 1000,
        "battery_percent_reported": batt_percent_reported,
        "sleep_time_s": sleep_time_s,
        "fast_rate_counter": fast_rate_counter,
        "total_count": total_count,
    }
