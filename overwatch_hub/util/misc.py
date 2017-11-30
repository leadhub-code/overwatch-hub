from sys import intern


def intern_keys(d):
    r = {}
    for k, v in d.items():
        if isinstance(v, dict):
            v = intern_keys(v)
        if isinstance(k, str):
            k = intern(k)
        r[k] = v
    return r
