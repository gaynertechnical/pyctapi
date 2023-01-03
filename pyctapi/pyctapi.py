#! /usr/bin/env python
#
# PyCtAPI
#
# A plain ctypes wrapper around the CitectSCADA CtAPI DLLs
# only compatible with Windows.
#
# You must have the following DLLs on hand
# - CiDebugHelp.dll
# - Ct_ipc.dll
# - CtApi.dll
# - CtEng32.dll
# - CtRes32.DLL
# - CtUtil32.dll

__title__ = 'pyctapi'
__version__ = '0.1'
__author__ = 'Mitchell Gayner'
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright 2017 Gayner Technical Services'

import platform
if platform.system() != "Windows":
    raise OSError

from datetime import datetime
import ctypes
from ctypes import CDLL, windll, create_string_buffer, byref, sizeof, pointer, GetLastError
from ast import literal_eval
import struct

ERROR_USER_DEFINED_BASE = 0x10000000

def CT_TO_WIN32_ERROR(dwStatus): return ((dwStatus) + ERROR_USER_DEFINED_BASE)
def WIN32_TO_CT_ERROR(dwStatus): return ((dwStatus) - ERROR_USER_DEFINED_BASE)
def IsCitectError(dwStatus): return (ERROR_USER_DEFINED_BASE < dwStatus)

CT_SUCCESS = True
CT_ERROR = False

CT_SCALE_RANGE_CHECK = 0x00000001
CT_SCALE_CLAMP_LIMIT = 0x00000002
CT_SCALE_NOISE_FACTOR = 0x00000004

CT_FMT_NO_SCALE = 0x00000001
CT_FMT_NO_FORMAT = 0x00000002
CT_FMT_LAST = 0x00000004
CT_FMT_RANGE_CHECK = 0x00000008

CT_FIND_SCROLL_NEXT = 0x00000001
CT_FIND_SCROLL_PREV = 0x00000002
CT_FIND_SCROLL_FIRST = 0x00000003
CT_FIND_SCROLL_LAST = 0x00000004
CT_FIND_SCROLL_ABSOLUTE = 0x00000005
CT_FIND_SCROLL_RELATIVE = 0x00000006

CT_OPEN_NO_OPTION = 0x00000000
CT_OPEN_CRYPT = 0x00000001
CT_OPEN_RECONNECT = 0x00000002
CT_OPEN_READ_ONLY = 0x00000004
CT_OPEN_BATCH = 0x00000008

CT_LIST_EVENT = 0x00000001
CT_LIST_LIGHTWEIGHT_MODE = 0x00000002

CT_LIST_EVENT_NEW = 0x00000001
CT_LIST_EVENT_STATUS = 0x00000002

CT_LIST_VALUE = 0x00000001
CT_LIST_TIMESTAMP = 0x00000002
CT_LIST_VALUE_TIMESTAMP = 0x00000003
CT_LIST_QUALITY_TIMESTAMP = 0x00000004
CT_LIST_QUALITY_GENERAL = 0x00000005
CT_LIST_QUALITY_SUBSTATUS = 0x00000006
CT_LIST_QUALITY_LIMIT = 0x00000007
CT_LIST_QUALITY_EXTENDED_SUBSTATUS = 0x00000008
CT_LIST_QUALITY_DATASOURCE_ERROR = 0x00000009
CT_LIST_QUALITY_OVERRIDE = 0x0000000A
CT_LIST_QUALITY_CONTROL_MODE = 0x0000000B

PROPERTY_NAME_LEN = 256

DBTYPE_EMPTY = 0
DBTYPE_NULL	= 1
DBTYPE_I2 = 2
DBTYPE_I4 = 3
DBTYPE_R4 = 4
DBTYPE_R8 = 5
DBTYPE_CY = 6
DBTYPE_DATE	= 7
DBTYPE_BSTR	= 8
DBTYPE_IDISPATCH = 9
DBTYPE_ERROR = 10
DBTYPE_BOOL	= 11
DBTYPE_VARIANT = 12
DBTYPE_IUNKNOWN = 13
DBTYPE_DECIMAL = 14
DBTYPE_UI1 = 17
DBTYPE_ARRAY = 0x2000
DBTYPE_BYREF = 0x4000
DBTYPE_I1 = 16
DBTYPE_UI2 = 18
DBTYPE_UI4 = 19
DBTYPE_I8 = 20
DBTYPE_UI8 = 21
DBTYPE_GUID = 72
DBTYPE_VECTOR = 0x1000
DBTYPE_RESERVED = 0x8000
DBTYPE_BYTES = 128
DBTYPE_STR = 129
DBTYPE_WSTR = 130
DBTYPE_NUMERIC = 131
DBTYPE_UDT = 132
DBTYPE_DBDATE = 133
DBTYPE_DBTIME = 134
DBTYPE_DBTIMESTAMP = 135

COMMON_WIN32_ERRORS = {
    "21" : "ERROR_INVALID_ACCESS", # Tag doesnt exist??
    "111" : "ERROR_BUFFER_OVERFLOW", # Result buffer not big enough",
    "233" : "ERROR_PIPE_NOT_CONNECTED",
}

CITECT_ERRORS = {
    "424" : "Tag not found"
}

class CTAPIWrapper:
    '''A plain ctypes wrapper around the CitectSCADA CtAPI DLLs'''
    def __init__(self, dll_path):
        CDLL(dll_path + '/CiDebugHelp')
        CDLL(dll_path + '/CtUtil32')
        CDLL(dll_path + '/Ct_ipc')
        CDLL(dll_path + '/CtApi')

    def ctOpen(self, host_address, username, password, mode=0):
        return windll.CtApi.ctOpen(host_address.encode("ascii"), username.encode("ascii"), password.encode("ascii"), mode)

    def ctClose(self, connection):
        return windll.CtApi.ctClose(connection)

    def ctCicode(self, connection, function, buff, hWin=0, overlapped=None):
        return windll.CtApi.ctCicode(connection, function.encode("ascii"), hWin, 0, byref(buff), sizeof(buff), overlapped)

    def ctTagWrite(self, connection, tag_name, value):
        return windll.CtApi.ctTagWrite(connection, tag_name.encode("ascii"), str(value).encode("ascii"))

    def ctTagRead(self, connection, tag_name, buff):
        return windll.CtApi.ctTagRead(connection, tag_name.encode("ascii"), byref(buff), sizeof(buff))

    def ctListNew(self, connection, mode):
        return windll.CtApi.ctListNew(connection, mode)

    def ctListFree(self, _list):
        return windll.CtApi.ctListFree(_list)

    def ctListAdd(self, _list, tag_name):
        return windll.CtApi.ctListAdd(_list, tag_name.encode("ascii"))
    
    def ctListAddEx(self, _list, tag_name, raw_mode=False, poll_period_ms=300,deadband_percent=-1.0 ):
        db = ctypes.c_double(deadband_percent)
        return windll.CtApi.ctListAddEx(_list, tag_name.encode("ascii"), raw_mode, poll_period_ms,db )

    def ctListDelete(self, tag_handle):
        windll.CtApi.ctListDelete(tag_handle)

    def ctListRead(self, _list, overlapped=None):
        return windll.CtApi.ctListRead(_list, overlapped)

    def ctListWrite(self, tag_handle, value, overlapped=None):
        return windll.CtApi.ctListWrite(tag_handle, str(value).encode("ascii"), overlapped)

    def ctListData(self, tag_handle, buff):
        return windll.CtApi.ctListData(tag_handle, byref(buff), sizeof(buff), 0)
    
    def ctListItem(self, tag_handle, buff, item_code=CT_LIST_VALUE):
        return windll.CtApi.ctListItem(tag_handle, item_code, byref(buff), sizeof(buff), 0)

    def ctListEvent(self, connection, mode):
        return windll.CtApi.ctListEvent(connection, mode)

    def ctFindFirst(self, connection, query, obj_handle):
        return windll.CtApi.ctFindFirst(connection, str(query).encode("ascii"), None, pointer(obj_handle), 0 )

    def ctFindNext(self, search_handle,  obj_handle):
        return windll.CtApi.ctFindNext(search_handle, pointer(obj_handle))

    def ctFindScroll(self, search_handle, search_mode, search_offset, obj_handle):
        return windll.CtApi.ctFindScroll(search_handle, search_mode, search_offset, pointer(obj_handle))
    
    def ctFindNumRecords(self, search_handle):
        return windll.CtApi.ctFindNumRecords(search_handle)

    def ctFindClose(self, search_handle):
        return windll.CtApi.ctFindClose(search_handle)

    def ctGetProperty(self, obj_handle, prop_name, buff):
        return windll.CtApi.ctGetProperty(obj_handle, str(prop_name).encode("ascii"), byref(buff), sizeof(buff), None, DBTYPE_STR)

    def getErrorCode(self):
         return GetLastError()

