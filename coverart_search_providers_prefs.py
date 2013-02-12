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
from gi.repository import Gio
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import PeasGtk
from gi.repository import RB
from gi.repository import Peas

import rb
import copy
from collections import OrderedDict

class GSetting:
    '''
    This class manages the differentes settings that the plugins haves to
    access to read or write.
    '''
    # storage for the instance reference
    __instance = None

    class __impl:
        """ Implementation of the singleton interface """
        # below public variables and methods that can be called for GSetting
        def __init__(self):
            '''
            Initializes the singleton interface, asigning all the constants
            used to access the plugin's settings.
            '''
            self.Path = self._enum(
                PLUGIN='org.gnome.rhythmbox.plugins.coverart_search_providers')

            self.PluginKey = self._enum(
                PROVIDERS='providers')

            self.setting = {}

        def get_setting(self, path):
            '''
            Return an instance of Gio.Settings pointing at the selected path.
            '''
            try:
                setting = self.setting[path]
            except:
                self.setting[path] = Gio.Settings(path)
                setting = self.setting[path]

            return setting

        def get_value(self, path, key):
            '''
            Return the value saved on key from the settings path.
            '''
            return self.get_setting(path)[key]

        def set_value(self, path, key, value):
            '''
            Set the passed value to key in the settings path.
            '''
            self.get_setting(path)[key] = value

        def _enum(self, **enums):
            '''
            Create an enumn.
            '''
            return type('Enum', (), enums)

    def __init__(self):
        """ Create singleton instance """
        # Check whether we already have an instance
        if GSetting.__instance is None:
            # Create and remember instance
            GSetting.__instance = GSetting.__impl()

        # Store instance reference as the only member in the handle
        self.__dict__['_GSetting__instance'] = GSetting.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)

class SearchPreferences(GObject.Object, PeasGtk.Configurable):
    '''
    Preferences for the CoverArt Browser Plugins. It holds the settings for
    the plugin and also is the responsible of creating the preferences dialog.
    '''
    __gtype_name__ = 'CoverArtSearchProvidersPreferences'
    object = GObject.property(type=GObject.Object)

    EMBEDDED_SEARCH='embedded-search'
    DISCOGS_SEARCH='discogs-search'
    COVERARTARCHIVE_SEARCH='coverartarchive-search'
    LOCAL_SEARCH='local-search'
    CACHE_SEARCH='cache-search'
    LASTFM_SEARCH='lastfm-search'
    MUSICBRAINZ_SEARCH='musicbrainz-search'

    def __init__(self):
        '''
        Initialises the preferences, getting an instance of the settings saved
        by Gio.
        '''
        GObject.Object.__init__(self)

    def do_create_configure_widget(self):
        '''
        Creates the plugin's preferences dialog
        '''

        self.gs = GSetting()
        self.settings = self.gs.get_setting(self.gs.Path.PLUGIN)
        
        self.provider = OrderedDict()
        
        self.provider[self.EMBEDDED_SEARCH] = _("Embedded coverart")
        self.provider[self.LOCAL_SEARCH] = _("Local folder coverart")
        self.provider[self.CACHE_SEARCH] = _("Cached coverart")
        self.provider[self.LASTFM_SEARCH] = _("LastFM Internet Provider")
        self.provider[self.MUSICBRAINZ_SEARCH] = _("MusicBrainz Internet Provider")
        self.provider[self.DISCOGS_SEARCH] = _("Discogs Internet Provider")
        self.provider[self.COVERARTARCHIVE_SEARCH] = _("Coverart Archive Internet Provider")
        
        
        current_providers = copy.deepcopy(self.provider)

        current = self.settings[self.gs.PluginKey.PROVIDERS]
        current_list = current.split(',')
        
        # create the ui
        builder = Gtk.Builder()
        builder.add_from_file(rb.find_plugin_file(self, "ui/coverart_search_providers_prefs.ui"))
        builder.connect_signals(self)
        self.provider_liststore = builder.get_object('provider_liststore')
        self.search_liststore = builder.get_object('search_liststore')
        self.provider_list = builder.get_object('provider_list')
        self.search_list = builder.get_object('search_list')

        for key in current_list:
            del current_providers[key]
            self.search_liststore.append([self.provider[key], key])
            
        for key, value in current_providers.items():
            self.provider_liststore.append( [value, key] )
        
        # return the dialog
        return builder.get_object('maingrid')

    def back_clicked(self, *args):

        if len(self.search_liststore) == 1:
            return   # keep at least one search provider
            
        model, iterval = self.search_list.get_selection().get_selected()

        if iterval:
            key = self.search_liststore[iterval][1]
            self.provider_liststore.append([self.provider[key], key])
            self.search_liststore.remove(iterval)

            self._store_search_providers()

    def forward_clicked(self, *args):
        model, iterval = self.provider_list.get_selection().get_selected()

        if iterval:
            key = self.provider_liststore[iterval][1]
            self.search_liststore.append([self.provider[key], key])
            self.provider_liststore.remove(iterval)

            self._store_search_providers()

    def _store_search_providers(self):
        item = self.search_liststore.get_iter_first ()
        current_providers = []
        
        while ( item != None ):
            current_providers.append (self.search_liststore.get_value (item, 1))
            item = self.search_liststore.iter_next(item)

        self.settings[self.gs.PluginKey.PROVIDERS] = ','.join(current_providers)

    def on_up_button_clicked(self, *args):
        selection = self.search_list.get_selection()
        sel = selection.get_selected()
        if not sel[1] == None:
            previous = self.search_liststore.iter_previous(sel[1])
            if previous:
                self.search_liststore.swap(sel[1], previous)
                self._store_search_providers()
                

    def on_down_button_clicked(self, *args):
        selection = self.search_list.get_selection()
        sel = selection.get_selected()
        if not sel[1] == None:
            next = self.search_liststore.iter_next(sel[1])
            if next:
                self.search_liststore.swap(sel[1], next)
                self._store_search_providers()
