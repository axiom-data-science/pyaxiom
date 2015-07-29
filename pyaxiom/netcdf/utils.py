#!python
# coding=utf-8


def cf_safe_name(name):
    import re
    if isinstance(name, str):
        if re.match('^[0-9_]', name):
            # Add a letter to the front
            name = "v_{}".format(name)
        return re.sub(r'[^_a-zA-Z0-9]', "_", name)
