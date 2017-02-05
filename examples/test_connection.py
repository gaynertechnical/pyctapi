#! /usr/bin/env python

import sys
sys.path.append("../")

from pyctapi import connection

IP_ADDRESS = "127.0.0.1"
CITECT_USERNAME = "engineer"
CITECT_PASSWORD = "control"

def print_func(stuff):
    print("print_func callback")
    print(stuff)

try:
    ct = connection.CTAPIConnection((IP_ADDRESS, CITECT_USERNAME, CITECT_PASSWORD))

    ct.add_list("mytags")
    ct.add_tag("mytags", "KNODLRS_PM10_CALC_24H")
    ct.add_tag("mytags", "BULGA___PM10_CALC_24H")
    ct.add_tag("mytags", "MAISOND_PM10_CALC_24H")
    ct.subscribe("mytags", print_func)

    input("Hit enter to stop")

except KeyboardInterrupt as e:
    pass
finally:
    ct.die()

