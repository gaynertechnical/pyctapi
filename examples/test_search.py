#! /usr/bin/env python

import sys
sys.path.append("../")

from pyctapi import adapter

IP_ADDRESS = "127.0.0.1"
CITECT_USERNAME = "engineer"
CITECT_PASSWORD = "control"
SOME_CITECT_TAG_NAME = "KNODLRS_PM10_CALC_24H"
TIMESTAMP_UTC_IN_SECONDS = "1672725468"

# Test search using TRNQUERY of CTAPI, fetch trend values
# trend tag read, Maximum 300 values can be queried at a time. See doc at https://johnwiltshire.com/citect-help/Content/trnQuery.html 
with adapter.CTAPIAdapter(IP_ADDRESS, CITECT_USERNAME, CITECT_PASSWORD) as ct:
    resultData = ct.search('TRNQUERY,{},0,1.00,3000,{},4194304,1,0,250'.format("TIMESTAMP_UTC_IN_SECONDS",SOME_CITECT_TAG_NAME))


