# -*- Mode: python; coding: utf-8; tab-width: 4; indent-tabs-mode: nil; -*-
#
# Copyright (C) 2012 - fossfreedom
# Copyright (C) 2012 - Agustin Carrasco
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

from gi.repository import RB
from gi.repository import GObject
from gi.repository import GdkPixbuf
from gi.repository import Gio
from gi.repository import GLib

import rb3compat
import time

if rb3compat.PYVER >=3:
    import dbm.gnu as gdbm
else:
    import gdbm
    
import os
import json

class Queue:
    def __init__(self):
        self.items = []
    def isEmpty(self):
        return self.items == []

    def enqueue(self, item):
        self.items.insert(0,item)

    def dequeue(self):
        return self.items.pop()

    def size(self):
        return len(self.items)

class CoverArtExtDB:
    '''
    This is a simplified version of the RB.ExtDB capability.  This
    resolves the bugs in the extant capability, primarily around using
    signals for none "album-art" databases.
    
    N.B. crashes and very weird behaviour was noticed with "artist-art"
    it is assumed that because we are not using official RhythmDB properties
    this causes unusual and unstable behaviour
    
    Rather than using trivial-database format which has not yet been 
    ported to python3 - this uses the analagous gdbm format.

    :param name: `str` name of the external database.
    '''
    
    # storage for the instance references
    __instances = {}
    NEXT_FILE = 'next-file'
    
    class _impl(GObject.Object):
        """ Implementation of the singleton interface """
        # properties
        
        # signals
        __gsignals__ = {
            'added': (GObject.SIGNAL_RUN_LAST, None, (object, object, object)),
            'request': (GObject.SIGNAL_RUN_LAST, None, (object, object))
            }
        
        #added (ExtDB self, ExtDBKey object, String path, Value pixbuf)    
        #request (ExtDB self, ExtDBKey object, guint64 last_time)
        
        _callback = {}
        
        def __init__(self, name):
            super(CoverArtExtDB._impl, self).__init__()
            self.cachedir = RB.user_cache_dir() + "/" + name
            if not os.path.exists(self.cachedir):
                os.makedirs(self.cachedir)
            
            filename = self.cachedir + "/store.db"
            self.db = gdbm.open(filename, 'c')
            self.queue = Queue()
        
        def _encode(self, param):
            if rb3compat.PYVER >=3:
                return param.encode('utf-8')
            else:
                return param
                
        def _decode(self, param):
            if rb3compat.PYVER >=3:
                return param.decode('utf-8')
            else:
                return param
            
        def _get_next_file(self):
            if self._encode(CoverArtExtDB.NEXT_FILE) not in self.db:
                next_file = str(0).zfill(8)
            else:
                next_file = self._decode(self.db[self._encode(CoverArtExtDB.NEXT_FILE)])
                next_file = str(int(next_file)+1).zfill(8)
            
            self.db[self._encode(CoverArtExtDB.NEXT_FILE)] = next_file
            return next_file
            
        def _get_field_key(self, key):
            return "/".join(key.get_field_names())
            
        def _get_field_values(self, key):
            field_values = ""
            for field in key.get_field_names():
                field_values += "#!~#".join(key.get_field_values(field))
            return field_values
            
        def _construct_key(self, key):
            keyval = self._get_field_key(key) + 'values' + \
                self._get_field_values(key)
                
            keyval = self._encode(keyval)
            return keyval    
        
        def store(self, key, source_type, data):
            '''
            :param key: `ExtDBKey`
            :param source_type: `ExtDBSourceType`
            :param data: `GdkPixbuf.Pixbuf`
            '''
            print ("store")
            
            self.store_uri(key, source_type, data)
            
        def do_store_request(self, *args):
            
            while not self.queue.isEmpty():
                    
                key, source_type, data = self.queue.dequeue()
                storeval = {}
                storeval['last-time'] = time.time()
                filename = ''
                
                if data and source_type != RB.ExtDBSourceType.NONE:
                    filename = self._get_next_file()                    
                    storeval['filename'] = filename
                    
                    if isinstance(data, GdkPixbuf.Pixbuf):
                        data.savev(self.cachedir + "/" + filename, 'png', [], [])
                    else:
                        gfile = Gio.File.new_for_uri(data)
                        try:
                            found, contents, error = gfile.load_contents(None)
                        except:
                            print ("failed to load uri %s", data)
                            return
                            
                        filename = self.cachedir + "/" + filename
                        new = Gio.File.new_for_path(filename)
                        new.replace_contents(contents, '', '', False, None)
                    
                    self.emit('added', key, filename, data)
                else:
                    storeval['filename']=''
                
                param = self._construct_key(key)
                self.db[param] = json.dumps(storeval)
                
                if param in self._callback:
                    callback, user_data = self._callback[param]
                    callback(key, filename, data, user_data)
                    
            return False
            
        def store_uri(self, key, source_type, data):
            '''
            :param key: `ExtDBKey`
            :param source_type: `ExtDBSourceType`
            :param data: `str` which is a uri
            '''
            print ("store_uri")
            
            kick = False
            if self.queue.isEmpty():
                kick = True
                
            self.queue.enqueue((key, source_type, data))
            
            if kick:
                Gio.io_scheduler_push_job(self.do_store_request, None, 
                    GLib.PRIORITY_DEFAULT, None)
                    
        def lookup(self, key):
            '''
            :param key: `ExtDBKey`
            '''
            lookup = self._construct_key(key)
            filename = ''
            if lookup in self.db:
                storeval = json.loads(self._decode(self.db[lookup]))
                if storeval['filename'] != '':
                    filename = self.cachedir + "/" + storeval['filename']
                
            return str(filename)
            
                
        def request(self, key, callback, user_data):
            '''
            :param key: `ExtDBKey`
            :param callback: `Function` callback
            :param user_data: `Value`
            
            where callback is
            Function (ExtDBKey key, String filename, GdkPixbuf.Pixbuf data, void* user_data) boolean
            '''
            
            lookup = self._construct_key(key)
            
            filename = ''
            timeval = time.time()
            if lookup in self.db:
                storeval = json.loads(self._decode(self.db[lookup]))
                if storeval['filename'] != '':
                    filename = self.cachedir + "/" + storeval['filename']
                timeval = storeval['last-time']
                
            result = False
            if filename != '':
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)
                callback(key, filename, pixbuf, user_data)
            else:
                self._callback[lookup] = (callback, user_data)
                self.emit('request', key, timeval)
                result = True
                
            return result

    def __init__(self, name):
        """ Create a semi-singleton instance """
        # Check whether we already have an instance
        if name not in CoverArtExtDB.__instances:
            # Create and remember instance
            CoverArtExtDB.__instances[name] = CoverArtExtDB._impl(name)

        # Store instance reference as the only member in the handle
        self.__dict__['_CoverArtExtDB__instance'] = CoverArtExtDB.__instances[name]

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__dict__['_CoverArtExtDB__instance'], attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__dict__['_CoverArtExtDB__instance'], attr, value)
        
