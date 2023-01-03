#! /usr/bin/env python
#
# PyCtAPI Adapter
#
# An attempt to "python-ise" the CtAPI
# wrapper
#

from ctypes import create_string_buffer
from ctypes.wintypes import HANDLE

from pyctapi import pyctapi

class CTAPIFailedToConnect(Exception):
    def __init__(self, error):
        Exception.__init__(self, error)
        if pyctapi.IsCitectError(error):
            self.error_code = pyctapi.WIN32_TO_CT_ERROR(error)
        else:
            self.error_code = pyctapi.CT_TO_WIN32_ERROR(error)

class CTAPITagDoesNotExist(Exception):
    def __init__(self, error):
        Exception.__init__(self, error)

class CTAPIGeneralError(Exception):
    def __init__(self, error):
        Exception.__init__(self, error)
        if pyctapi.IsCitectError(error):
            self.error_code = pyctapi.WIN32_TO_CT_ERROR(error)
        else:
            self.error_code = pyctapi.CT_TO_WIN32_ERROR(error)

class CTAPIAdapter:
    '''Python-ise the ctypes wrapper'''
    def __init__(self, citect_host, citect_username, citect_password, mode=pyctapi.CT_OPEN_NO_OPTION, dll_path="C:/Program Files (x86)/Schneider Electric/CitectSCADA 7.50/Bin"):
        self.citect_host = citect_host
        self.citect_username = citect_username
        self.citect_password = citect_password
        self.citect_connection_mode = mode

        self._ctapi = pyctapi.CTAPIWrapper(dll_path)
        self._tag_lists = {} 
        self._tag_handles = {}
        self._search_handle = None
        self._search_obj_handle = HANDLE()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._close_all()

    def connect(self):
        con = self._ctapi.ctOpen(self.citect_host, self.citect_username, self.citect_password, self.citect_connection_mode)

        # Raise connection exception
        if con == 0:
           raise CTAPIFailedToConnect(self._ctapi.getErrorCode())

        self._connection = con

    def _close_all(self):
        for key, value in self._tag_lists.items():
            self._ctapi.ctListFree(value)

        self._ctapi.ctClose(self._connection)

    def _parse_buffer_to_value(self, buff):
        buff_as_string = buff.value.decode("utf-8")
        if buff_as_string.isdigit():
            return int(buff_as_string)

        elif buff_as_string.count(".") == 1:
            point_index = buff_as_string.find(".")
            if buff_as_string[:point_index].isdigit() and buff_as_string[point_index+1:].isdigit():
                return float(buff_as_string)

        return buff_as_string

    def read_tag(self, tag_name):
        value_buffer = create_string_buffer(b'0' * 8)
        status_code = self._ctapi.ctTagRead(self._connection, tag_name, value_buffer)
        if status_code == pyctapi.CT_SUCCESS:
            return self._parse_buffer_to_value(value_buffer)

        raise CTAPIGeneralError(self._ctapi.getErrorCode())

    def write_tag(self, tag_name, value):
        status_code = self._ctapi.ctTagWrite(self._connection, tag_name, str(value))
        if status_code == pyctapi.CT_SUCCESS:
            return status_code 

        raise CTAPIGeneralError(self._ctapi.getErrorCode())

    def call_function(self, function):
        value_buffer = create_string_buffer(b'0' * 256)
        status_code = self._ctapi.ctCicode(self._connection, function, value_buffer)

        if status_code == pyctapi.CT_SUCCESS:
            return self._parse_buffer_to_value(value_buffer) 

        raise CTAPIGeneralError(self._ctapi.getErrorCode())

    def create_tag_list(self, list_name, mode=0):
        list_handle = self._ctapi.ctListNew(self._connection, mode)
        if list_handle != None:
            self._tag_lists[list_name] = list_handle
            return list_handle

        raise CTAPIGeneralError(self._ctapi.getErrorCode())

    def add_tag_to_list(self, list_name, tag_name, raw_mode=False, poll_period_ms=300,deadband_percent=-1.0):
        tag_handle = self._ctapi.ctListAddEx(self._tag_lists[list_name], tag_name, raw_mode, poll_period_ms, deadband_percent)
        if tag_handle != None:
            self._tag_handles[tag_name] = tag_handle
            return tag_handle

        raise CTAPITagDoesNotExist(self._ctapi.getErrorCode() + " tag % does not exist" % tag_name)

    def refresh_list(self, list_name):
        status_code = self._ctapi.ctListRead(self._tag_lists[list_name])
        if status_code == 0:
            raise CTAPIGeneralError(self._ctapi.getErrorCode())

    def value_from_list(self, tag_name):
        value_buffer = create_string_buffer(b'0' * 8)
        try:
            status_code = self._ctapi.ctListData(self._tag_handles[tag_name], value_buffer)
        except KeyError as e:
            raise CTAPIGeneralError("Tag %s has not been added to tag list" % tag_name)

        if status_code == pyctapi.CT_SUCCESS:
            return self._parse_buffer_to_value(value_buffer)

        error = self._ctapi.getErrorCode()
        if pyctapi.IsCitectError(error):
            if pyctapi.WIN32_TO_CT_ERROR(error) == 424:
                raise CTAPITagDoesNotExist("%s does not exist" % tag_name)

        raise CTAPIGeneralError(error)

    def next_event(self, list_name, mode=0):
        list_handle = self._tag_lists[list_name]
        changed_handle = self._ctapi.ctListEvent(list_handle, mode)
        if changed_handle == 0:
            return None

        # Find the tag handle and return a tuple with the tag name and value
        for tag_name, tag_handle in self._tag_handles.items():
            if tag_handle == changed_handle:
                return (tag_name, self.value_from_list(tag_name),)

    def write_tag_list(self, tag_name, value):
        try:
            status_code = self._ctapi.ctListWrite(self._tag_handles[tag_name], str(value))
        except KeyError as e:
            raise CTAPIGeneralError("Tag %s has not been added to tag list" % tag_name)

        if status_code != pyctapi.CT_SUCCESS:
            raise CTAPIGeneralError(self._ctapi.getErrorCode())
        return status_code

    #Attaching this callable to restype of DLL function 
    def _return_error_check(self, value):
        if value : # Null or None has zeo boolean value
            if value == 0: # CTAPI functions return '0' on error
               raise CTAPIGeneralError(self._ctapi.getErrorCode())
            return value
        raise CTAPIGeneralError(self._ctapi.getErrorCode())# CTAPI functions return NULL on error

    def search(self, search_str):
        ''' Form search functionality as implemented by ctFindFirst family'''
        try:
            self._search_handle = self._return_error_check(self._ctapi.ctFindFirst(self._connection, search_str, self._search_obj_handle ))
            # Get Metadata of result
            value_buffer = create_string_buffer(b'0' * 50)
            self._ctapi.ctGetProperty(self._search_obj_handle, 'object.fields.count',value_buffer)
            fields_count = int(value_buffer.value)
            fields=[]
            for i in range(1,fields_count+1,1):
                self._ctapi.ctGetProperty(self._search_obj_handle, 'object.fields({}).name'.format(i),value_buffer)
                fields.append(value_buffer.value.decode("utf-8"))
            
            data=[]
            while True:
                data_item = dict()
                for field in fields:
                    self._ctapi.ctGetProperty(self._search_obj_handle, field, value_buffer)
                    data_item[str(field)] = value_buffer.value.decode("utf-8")
                data.append(data_item)
                if self._ctapi.ctFindNext(self._search_handle, self._search_obj_handle) == 0:
                    break
            return data

        except:
            error = self._ctapi.getErrorCode()
            print("Error in search {}".format(error))
        finally:
            self._ctapi.ctFindClose(self._search_handle)
            self._search_handle = None

