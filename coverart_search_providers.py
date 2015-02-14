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

# define plugin

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import RB
from gi.repository import Peas

from coverart_search_providers_prefs import GSetting
from coverart_search_providers_prefs import CoverLocale
from coverart_album_search import CoverAlbumSearch
from coverart_album_search import CoverSearch
from coverart_album_search import CoverartArchiveSearch
from coverart_artist_search import ArtistCoverSearch
from coverart_artist_search import LastFMArtistSearch
from coverart_album_search import SpotifySearch
from coverart_artist_search import user_has_account
from coverart_extdb import CoverArtExtDB
from rb_oldcache import OldCacheSearch
from rb_local import LocalSearch
from rb_lastfm import LastFMSearch
from rb_musicbrainz import MusicBrainzSearch
from rb_embedded import EmbeddedSearch
from coverart_search_providers_prefs import SearchPreferences
import rb3compat


def lastfm_connected():
    '''
    returns True/False if connected to lastfm
    '''
    return user_has_account()


def get_search_providers():
    '''
    returns an array of search providers
    '''
    gs = GSetting()
    setting = gs.get_setting(gs.Path.PLUGIN)
    current_providers = setting[gs.PluginKey.PROVIDERS]

    return current_providers.split(',')


class CoverArtAlbumSearchPlugin(GObject.Object, Peas.Activatable):
    '''
    Main class of the plugin. Manages the activation and deactivation of the
    plugin.
    '''
    __gtype_name = 'CoverArtAlbumSearchPlugin'
    object = GObject.property(type=GObject.Object)

    def __init__(self):
        '''
        Initialises the plugin object.
        '''
        GObject.Object.__init__(self)
        if not rb3compat.compare_pygobject_version('3.9'):
            GObject.threads_init()

    def do_activate(self):
        '''
        Called by Rhythmbox when the plugin is activated. It creates the
        plugin's source and connects signals to manage the plugin's
        preferences.
        '''

        cl = CoverLocale()
        cl.switch_locale(cl.Locale.LOCALE_DOMAIN)

        # define .plugin text strings used for translation
        plugin = _('CoverArt Browser Search Providers')
        desc = _('Additional coverart search providers for Rhythmbox')

        print("CoverArtBrowser DEBUG - do_activate")
        self.shell = self.object
        self.db = self.shell.props.db

        self.art_store = RB.ExtDB(name="album-art")
        self.req_id = self.art_store.connect("request", self.album_art_requested)

        self.artist_store = CoverArtExtDB(name="artist-art")
        self.artist_req_id = self.artist_store.connect("request", self.artist_art_requested)

        self.peas = Peas.Engine.get_default()
        loaded_plugins = self.peas.get_loaded_plugins()

        self.peas_id = self.peas.connect_after('load-plugin', self.deactivate_plugin)

        if 'artsearch' in loaded_plugins:
            artsearch_info = self.peas.get_plugin_info('artsearch')
            self._unload_artsearch(self.peas, artsearch_info)

        self.csi_id = self.shell.connect("create_song_info", self.create_song_info)

        print("CoverArtBrowser DEBUG - end do_activate")

    def deactivate_plugin(self, engine, info):
        if info.get_module_name() == 'artsearch':
            self._unload_artsearch(engine, info)

    def _unload_artsearch(self, engine, info):
        engine.unload_plugin(info)
        dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.WARNING,
                                   Gtk.ButtonsType.OK,
                                   _("Conflicting plugin found."))
        dialog.format_secondary_text(
            _("The ArtSearch plugin has been deactivated"))
        dialog.run()
        dialog.destroy()


    def do_deactivate(self):
        '''
        Called by Rhythmbox when the plugin is deactivated. It makes sure to
        free all the resources used by the plugin.
        '''
        print("CoverArtBrowser DEBUG - do_deactivate")

        self.shell.disconnect(self.csi_id)
        self.csi_id = 0
        del self.shell
        del self.db
        self.art_store.disconnect(self.req_id)
        self.artist_store.disconnect(self.artist_req_id)
        self.peas.disconnect(self.peas_id)
        self.req_id = 0
        self.peas_id = 0
        self.art_store = None
        self.artist_store = None
        self.peas = None

        print("CoverArtBrowser DEBUG - end do_deactivate")

    def create_song_info(self, shell, song_info, is_multiple):
        if is_multiple is False:
            # following only valid for rhythmbox 3.2
            try:
                import sys

                artsearch_dir = self.peas.get_plugin_info('artsearch').get_module_dir()
                sys.path.append(artsearch_dir)
                from songinfo import AlbumArtPage

                x = AlbumArtPage(shell, song_info)
            except:
                pass

    def album_art_requested(self, store, key, last_time):
        searches = []

        current_list = get_search_providers()

        for provider in current_list:
            if provider == SearchPreferences.EMBEDDED_SEARCH:
                searches.append(EmbeddedSearch())
                searches.append(CoverAlbumSearch())
            if provider == SearchPreferences.LOCAL_SEARCH:
                searches.append(LocalSearch())
            if provider == SearchPreferences.CACHE_SEARCH:
                searches.append(OldCacheSearch())
            if provider == SearchPreferences.LASTFM_SEARCH:
                searches.append(LastFMSearch())
            if provider == SearchPreferences.MUSICBRAINZ_SEARCH:
                searches.append(MusicBrainzSearch())
            if provider == SearchPreferences.SPOTIFY_SEARCH:
                searches.append(SpotifySearch())
            # if provider == SearchPreferences.DISCOGS_SEARCH:
            #    searches.append(DiscogsSearch())
            if provider == SearchPreferences.COVERARTARCHIVE_SEARCH:
                searches.append(CoverartArchiveSearch())

        s = CoverSearch(store, key, last_time, searches)

        return s.next_search(True)

    def artist_art_requested(self, store, key, last_time):
        print("artist_art_requested")

        print(store)
        print(key)
        print(last_time)

        searches = []

        searches.append(LastFMArtistSearch())
        # searches.append(DiscogsSearch())

        s = ArtistCoverSearch(store, key, last_time, searches)

        print("finished artist_art_requested")
        return s.next_search(True)
