# -*- coding: utf-8 -*-
import os
# import diaper for backward compatibility

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'


def safe_string(o):
    """This will make string out of ANYTHING without having to worry about the stupid Unicode errors

    This function tries to make str/unicode out of ``o`` unless it already is one of those and then
    it processes it so in the end there is a harmless ascii string.

    Args:
        o: Anything.
    """
    if not isinstance(o, basestring):
        if hasattr(o, "__unicode__"):
            o = unicode(o)
        else:
            o = str(o)
    if isinstance(o, str):
        o = o.decode('utf-8', "ignore")
    if isinstance(o, unicode):
        o = o.encode("ascii", "xmlcharrefreplace")
    return o
