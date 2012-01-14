# -*- coding: ISO-8859-1 -*-
import re
import time
import math


def doxReMatch (Pattern, Text):
    match = re.search (Pattern, Text)
    if match:
        return (match.group(0))
    return (None)


def doxTime ():
    return (int (math.floor (time.time ())))