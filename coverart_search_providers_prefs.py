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
                EMBEDDED_SEARCH='embedded-search',
                DISCOGS_SEARCH='discogs-search',
                COVERARTARCHIVE_SEARCH='coverartarchive-search',
                LOCAL_SEARCH='local-search',
                CACHE_SEARCH='cache-search',
                LASTFM_SEARCH='lastfm-search',
                MUSICBRAINZ_SEARCH='musicbrainz-search')

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

    def __init__(self):
        '''
        Initialises the preferences, getting an instance of the settings saved
        by Gio.
        '''
        GObject.Object.__init__(self)
        gs = GSetting()
        self.settings = gs.get_setting(gs.Path.PLUGIN)

    def do_create_configure_widget(self):
        '''
        Creates the plugin's preferences dialog
        '''
        # create the ui
        self.builder = Gtk.Builder()
        self.builder.add_from_file(rb.find_plugin_file(self, "ui/coverart_search_providers_prefs.ui"))
        #self.builder.connect_signals(self)
        gs = GSetting()
        # bind the toggles to the settings
        self.search = {}
        self._checkboxbind('embedded_checkbox', gs.PluginKey.EMBEDDED_SEARCH)
        self._checkboxbind('discogs_checkbox', gs.PluginKey.DISCOGS_SEARCH)
        self._checkboxbind('archive_checkbox', gs.PluginKey.COVERARTARCHIVE_SEARCH)
        self._checkboxbind('local_checkbox', gs.PluginKey.LOCAL_SEARCH)
        self._checkboxbind('cache_checkbox', gs.PluginKey.CACHE_SEARCH)
        self._checkboxbind('lastfm_checkbox', gs.PluginKey.LASTFM_SEARCH)
        self._checkboxbind('musicbrainz_checkbox', gs.PluginKey.MUSICBRAINZ_SEARCH)

        # return the dialog
        return self.builder.get_object('maingrid')

    def _checkboxbind(self, field, key):
        self.search[field] = self.builder.get_object(field)
        self.settings.bind(key,
            self.search[field], 'active', Gio.SettingsBindFlags.DEFAULT)
