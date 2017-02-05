#! /usr/bin/env python

from time import sleep
from datetime import datetime
from threading import Thread, Lock

from pyctapi import pyctapi
from pyctapi import adapter
from pyctapi.adapter import CTAPIFailedToConnect, CTAPIGeneralError, CTAPITagDoesNotExist

class CTAPIClusterConnection(Thread):
    '''Allows multiple connection objects to share a lock for processin callbacks'''
    def __init__(self, cluster_params):
        self._poll_lock = Lock()
        self.cluster_params = cluster_params

        self.connections = set()

        for server_params in self.cluster_params:
            connection = CTAPIConnection(server_params, poll_lock=self._poll_lock)
            self.connections.add(connection)

    def add_list(self, list_name):
        for con in self.connections:
            con.add_list(list_name) 

    def add_tag(self, list_name, tag_name):
        for con in self.connections:
            con.add_tag(list_name, tag_name) 

    def subscribe(self, list_name, callback):
        for con in self.connections:
            con.subscribe(list_name, callback)

    def die(self):
        for con in self.connections:
            con.die()

class CTAPIConnection(Thread):
    def __init__(self, connection_params, scan_rate=0.1, poll_lock=None):
        Thread.__init__(self)
        self._ctapi = None
        self._ok_to_run = True
        self._scan_rate = scan_rate
        self._poll_lock = poll_lock

        self._backoff_time = 0.5

        self.CITECT_CONNECTION_PARAMS = connection_params

        self.tag_lists = set() 
        self.tags = set() 
        self.tag_lists_changed = set()
        self.tags_changed = set()

        self.subscribers = set()

        self.start()

    def add_list(self, list_name):
        self.tag_lists_changed.add(list_name) 

    def add_tag(self, list_name, tag_name):
        self.tags_changed.add((list_name, tag_name,)) 

    def subscribe(self, list_name, callback):
        self.subscribers.add((list_name, callback))

    def _process_events(self, tag_list):
        # Check for tag list events
        event_date = datetime.utcnow().isoformat()
        new_events = []
        while self._ok_to_run:
            event = self._ctapi.next_event(tag_list, pyctapi.CT_LIST_EVENT_NEW + pyctapi.CT_LIST_EVENT_STATUS)
            if event == None:
                break
            new_events.append(event)

        # If no new events, do proceed to callbacks
        if len(new_events) == 0:
            return

        # Call tag list subcribers
        for list_name, callback in self.subscribers:
            if list_name == tag_list:
                callback((event_date, new_events, self.host()))

    def host(self):
        return self.CITECT_CONNECTION_PARAMS[0]

    def _read_lists(self):
        print("Running event check loop")
        # Reading entire tag list
        while self._ok_to_run:

            try:
                # Update internal tags lists
                self._update_tag_lists()

                for tag_list in self.tag_lists:
                    # Refresh list
                    self._ctapi.refresh_list(tag_list)

                    # Check if the polling lock is available
                    if self._poll_lock != None and self._poll_lock.acquire(blocking=False):
                        print("Lock acquired")
                        self._process_events(tag_list)

            except CTAPITagDoesNotExist as e:
                    print("Error", e)

            except CTAPIGeneralError as e:
                if self._poll_lock != None:
                    self._poll_lock.release()
                    print("Lock released")
            
                if e.error_code == 233:
                    print("Connection lost to %" % self.host())
                    break

            sleep(self._scan_rate)
        self._poll_lock.release()
        print("Lock released") 

    def _init_tag_lists(self):
        for list_name in self.tag_lists:
            print("Created tag list %s" % list_name)
            self._ctapi.create_tag_list(list_name, pyctapi.CT_LIST_EVENT + pyctapi.CT_LIST_LIGHTWEIGHT_MODE)

        for list_name, tag_name in self.tags:
            print("Created tag %s -> %s" % (list_name, tag_name))
            self._ctapi.add_tag_to_list(list_name, tag_name)

    def _update_tag_lists(self):
        for list_name in self.tag_lists_changed - self.tag_lists:
            print("Added tag list %s" % list_name)
            self._ctapi.create_tag_list(list_name, pyctapi.CT_LIST_EVENT + pyctapi.CT_LIST_LIGHTWEIGHT_MODE)
        self.tag_lists |= self.tag_lists_changed

        for list_name, tag_name in self.tags_changed - self.tags:
            print("Added tag %s -> %s" % (list_name, tag_name))
            self._ctapi.add_tag_to_list(list_name, tag_name)
        self.tags |= self.tags_changed

    def _increase_backoff_time(self):
        self._backoff_time *= 2.0
        if self._backoff_time > 10:
            self._backoff_time = 10

    def run(self):
        host, username, password = self.CITECT_CONNECTION_PARAMS
        while self._ok_to_run:
            try:
                with adapter.CTAPIAdapter(host, username, password) as self._ctapi:
                    # If we get a connection reset the backoff timer
                    self._backoff_time = 0.5

                    # Read the tags sir
                    self._init_tag_lists()
                    self._read_lists()

            except CTAPIFailedToConnect:
                print("Connection failed retrying")
                self._increase_backoff_time()
                sleep(self._backoff_time)
                continue

            sleep(self._backoff_time)

    def die(self):
        print("Stopping connection")
        self._ok_to_run = False
        self.join()

