def numerify(string, default=None, min=None, max=None):
    """Converts a string to an integer"""
    if string is None:
        string = int(default)
    num = int(string)
    if min is not None and num < int(min):
        num = min
    if max is not None and num > int(max):
        num = max
    return num
