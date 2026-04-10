from pydoover.tags import Tag, Tags


class TtsTags(Tags):
    rssi = Tag("number", default=None)
    snr = Tag("number", default=None)
    frame_counter = Tag("integer", default=None)
    frequency = Tag("string", default=None)
    data_rate = Tag("string", default=None)
    decoded_payload = Tag("object", default=None)
