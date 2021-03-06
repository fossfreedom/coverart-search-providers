# -*- Mode: python; coding: utf-8; tab-width: 4; indent-tabs-mode: nil; -*-
# Copyright (C) 2012 - fossfreedom
# Copyright (C) 2012 - Agustin Carrasco
# # adapted from artsearch plugin - Copyright (C) 2012 Jonathan Matthew
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# The Rhythmbox authors hereby grant permission for non-GPL compatible
# GStreamer plugins to be used and distributed together with GStreamer
# and Rhythmbox. This permission is above and beyond the permissions granted
# by the GPL license by which Rhythmbox is covered. If you modify this code
# you may extend this exception to your version of the code, but you are not
# obligated to do so. If you do not wish to do so, delete this exception
# statement from your version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

import os
import json
import gettext

from gi.repository import RB
import chardet

import rb
import rb3compat

gettext.install('rhythmbox', RB.locale_dir())

if rb3compat.PYVER >= 3:
    import configparser
else:
    import ConfigParser as configparser

ITEMS_PER_NOTIFICATION = 10
IGNORED_SCHEMES = ('http', 'cdda', 'daap', 'mms')
REPEAT_SEARCH_PERIOD = 86400 * 7


def file_root(f_name):
    return os.path.splitext(f_name)[0].lower()


# this API key belongs to foss.freedom@gmail.com
# and was generated specifically for this use
API_KEY = '844353bce568b93accd9ca47674d6c3e'
API_URL = 'http://ws.audioscrobbler.com/2.0/'


def user_has_account():
    session_file = os.path.join(RB.user_data_dir(), "audioscrobbler", "sessions")

    if os.path.exists(session_file) == False:
        return False

    sessions = configparser.RawConfigParser()
    sessions.read(session_file)
    try:
        return (sessions.get('Last.fm', 'username') != "")
    except:
        return False


class ArtistCoverSearch(object):
    def __init__(self, store, key, last_time, searches):
        self.store = store
        self.key = key.copy()
        self.last_time = last_time
        self.searches = searches

    def next_search(self, continue_search):
        """
        main routine that calls the search routine for each search provider
        unless one of the searches has found something

        outputs - return False means that nothing found
        inputs - True means continue with searching
               - False means a search routine recommends no more searching
        """

        if len(self.searches) == 0 and continue_search:
            key = RB.ExtDBKey.create_storage("artist", self.key.get_field("artist"))
            self.store.store(key, RB.ExtDBSourceType.NONE, None)
            return False

        if continue_search:
            search = self.searches.pop(0)
            search.search(self.key, self.last_time, self.store, self.search_done, None)
            return True
        else:
            return False

    def search_done(self, args):
        self.next_search(args)


class LastFMArtistSearch(object):
    def __init__(self):
        pass

    def search_url(self, artist):

        print("searching for (%s)" % (artist))
        url = API_URL + "?method=artist.getinfo&"
        url = url + "artist=%s&" % (rb3compat.quote_plus(artist))
        url = url + "format=json&"
        url = url + "api_key=%s" % API_KEY
        print(("last.fm query url = %s" % url))
        return url

    def artist_info_cb(self, data):
        if data is None:
            print("last.fm query returned nothing")
            self.callback(True)
            return

        encoding = chardet.detect(data)['encoding']
        encoded = data.decode(encoding)
        json_data = json.loads(encoded)

        if 'artist' not in json_data:
            print("no artists found in data returned")
            self.callback(True)
            return

        artist = json_data['artist']

        # find image URLs
        image_urls = []

        if 'image' not in artist:
            print("no images found for artist")
            self.callback(True)
            return

        for key in artist['image']:
            for url in list(key.values()):
                url.strip()
                if url.endswith('.png') or url.endswith('.jpg'):
                    image_urls.append(url)

        if len(image_urls) > 0:
            # images tags appear in order of increasing size, and we want the largest.  probably.
            url = image_urls.pop()

            # last check - ensure the size is relatively large to hide false positives
            site = rb3compat.urlopen(url)
            meta = site.info()

            if rb3compat.PYVER >= 3:
                size = meta.get_all('Content-Length')[0]
            else:
                size = meta.getheaders("Content-Length")[0]

            if int(size) > 1000:
                self.store.store_uri(self.current_key, RB.ExtDBSourceType.SEARCH, str(url))
                self.callback(False)
                return

        self.callback(True)

    def search_next(self, artist):
        print("search_next")
        artist = str(artist)
        self.current_key = RB.ExtDBKey.create_storage("artist", artist)

        url = self.search_url(artist)

        l = rb.Loader()
        l.get_url(url, self.artist_info_cb)

    def search(self, key, last_time, store, callback, args):
        # if last_time > (time.time() - REPEAT_SEARCH_PERIOD):
        #    print("we already tried this one")
        #    callback (True)
        #    return

        if not user_has_account():
            print("can't search: no last.fm account details")
            callback(True)
            return

        artist = key.get_field("artist")
        self.key = key

        if artist is None:
            print("can't search: no useful details")
            callback(True)
            return

        self.store = store
        self.callback = callback
        self.callback_args = args
        self.search_next(artist)
