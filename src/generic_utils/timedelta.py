# TODO just use .total_seconds() once Python 2.7 is out everywhere
# This method is only needed because Python 2.7 is not deployed everywhere just yet.
def get_total_seconds(delta):
    if hasattr(delta, "total_seconds"):
        return delta.total_seconds()
    else:
        return (delta.microseconds + (delta.seconds + delta.days * 24 * 3600) * 10 ** 6) / 10 ** 6
