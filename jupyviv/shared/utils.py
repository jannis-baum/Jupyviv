# safely access d which may or may not be a dictionary at k which may be a key
# or a list of keys for nested dictionaries
def dsafe(d, *k):
    if len(k) > 1:
        return dsafe(dsafe(d, k[0]), *k[1:])
    if len(k) == 1:
        return d[k[0]] if type(d) == dict and k[0] in d else None
    return d
