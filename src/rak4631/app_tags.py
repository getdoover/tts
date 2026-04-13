from pydoover.tags import Tag, Tags


class Rak4631Tags(Tags):
    # Top-level UI values
    level_pct = Tag("number", default=None)
    flow_rate_lpm = Tag("number", default=None)

    # Computed details
    raw_current_ma = Tag("number", default=None)
    raw_current_cm = Tag("number", default=None)
    count_reading = Tag("integer", default=None)
    total_count = Tag("integer", default=None)
    total_litres = Tag("number", default=None)
    raw_battery_v = Tag("number", default=None)
    battery_pct = Tag("number", default=None)
    sleep_time_s = Tag("integer", default=None)
    fast_rate_counter = Tag("integer", default=None)

    # Warning state
    level_low_warning = Tag("boolean", default=False)
    batt_low_warning = Tag("boolean", default=False)
    high_rate_warning = Tag("boolean", default=False)
