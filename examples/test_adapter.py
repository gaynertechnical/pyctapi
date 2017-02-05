#! /usr/bin/env python

import sys
sys.path.append("../")

from pyctapi import adapter

IP_ADDRESS = "127.0.0.1"
CITECT_USERNAME = "engineer"
CITECT_PASSWORD = "control"
SOME_CITECT_TAG_NAME = "KNODLRS_PM10_CALC_24H"

# Test using adapter as an object
cti = adapter.CTAPIAdapter(IP_ADDRESS, CITECT_USERNAME, CITECT_PASSWORD)
cti.connect()
print(cti.read_tag(SOME_CITECT_TAG_NAME))
cti.write_tag(SOME_CITECT_TAG_NAME, 1)
print(cti.read_tag(SOME_CITECT_TAG_NAME))
print(cti.call_function("Version(3)"))

# Test using adapter as context manager
# simple tag rea/write & cicode function call
with adapter.CTAPIAdapter(IP_ADDRESS, CITECT_USERNAME, CITECT_PASSWORD) as ct2:
    ct2.write_tag(SOME_CITECT_TAG_NAME, 2)
    print(ct2.read_tag(SOME_CITECT_TAG_NAME))
    print(ct2.call_function("Version(3)"))

# Testusing adapter as a context manager
# tag list read/write
with adapter.CTAPIAdapter(IP_ADDRESS, CITECT_USERNAME, CITECT_PASSWORD) as ct3:
    ct3.create_tag_list("my_tag_list")
    ct3.add_tag_to_list("my_tag_list", SOME_CITECT_TAG_NAME)
    ct3.refresh_list("my_tag_list")
    print(ct3.value_from_list(SOME_CITECT_TAG_NAME))
    ct3.write_tag_list(SOME_CITECT_TAG_NAME, 3)
    ct3.refresh_list("my_tag_list")
    print(ct3.value_from_list(SOME_CITECT_TAG_NAME))

