#! /usr/bin/env python

import sys
sys.path.append("../")

from ctypes import create_string_buffer, GetLastError

from pyctapi import pyctapi

IP_ADDRESS = "127.0.0.1"
CITECT_USERNAME = "engineer"
CITECT_PASSWORD = "control"
SOME_CITECT_TAG_NAME = "KNODLRS_PM10_CALC_24H"

w = pyctapi.CTAPIWrapper("C:/Program Files (x86)/Schneider Electric/CitectSCADA 7.50/Bin")

#
# Connect to CitectSCADA client instance 
#
connection = w.ctOpen(IP_ADDRESS, CITECT_USERNAME, CITECT_PASSWORD, pyctapi.CT_OPEN_NO_OPTION)
if connection != 0:
    print("Connected")
else:
    print("Failed to connect")

#
# Read a tag
#
value_buffer = create_string_buffer(b'0' * 4)
result = w.ctTagRead(connection, SOME_CITECT_TAG_NAME, value_buffer)

if result == pyctapi.CT_SUCCESS:
    print("Read success", value_buffer.value)
else:
    err = w.getErrorCode()

    if pyctapi.IsCitectError(err):
        print(pyctapi.WIN32_TO_CT_ERROR(err))
    else:
        print(pyctapi.CT_TO_WIN32_ERROR(err))

#
# Write a value to tag
#
value_to_write = 1.3
result = w.ctTagWrite(connection, SOME_CITECT_TAG_NAME, value_to_write)

if result == pyctapi.CT_SUCCESS:
    print("write success")
else:
    err = w.getErrorCode()

    if pyctapi.IsCitectError(err):
        print(pyctapi.WIN32_TO_CT_ERROR(err))
    else:
        print(pyctapi.CT_TO_WIN32_ERROR(err))

#
# Call a cicode function
#
value_buffer = create_string_buffer(b'0' * 32)
result = w.ctCicode(connection, "Version(3)", value_buffer)
if result == pyctapi.CT_SUCCESS:
    print(value_buffer.value)
else:
    err = w.getErrorCode()

    if pyctapi.IsCitectError(err):
        print(pyctapi.WIN32_TO_CT_ERROR(err))
    else:
        print(pyctapi.CT_TO_WIN32_ERROR(err))

# Call a cicode function without enough room in
# result buffer
value_buffer = create_string_buffer(b'0' * 3)
result = w.ctCicode(connection, "Version(3)", value_buffer)

if pyctapi.IsCitectError(result):
    print("Citect error")
else:
    err = w.getErrorCode()

    print("Expected error (buffer overflow)")
    if pyctapi.IsCitectError(err):
        print(pyctapi.WIN32_TO_CT_ERROR(err))
    else:
        print(pyctapi.CT_TO_WIN32_ERROR(err))

w.ctClose(connection)

