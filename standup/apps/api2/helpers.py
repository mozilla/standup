def numerify(str, default=None, lower=None, upper=None):
    try:
        num = int(str)
    except (TypeError, ValueError):
        if default:
            num = default
        else:
            raise

    if upper and num > int(upper):
        num = int(upper)

    if lower and num < int(lower):
        num = int(lower)

    return num
