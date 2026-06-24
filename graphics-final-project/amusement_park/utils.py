def hex_color(value):
    if isinstance(value, (tuple, list)):
        return tuple(value)
    return (
        (value >> 16 & 0xFF) / 255.0,
        (value >> 8 & 0xFF) / 255.0,
        (value & 0xFF) / 255.0,
    )
