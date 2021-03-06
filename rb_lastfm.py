# -*- Mode: python; coding: utf-8; tab-width: 8; indent-tabs-mode: t; -*-
#
# Copyright (C) 2009 Jonathan Matthew  <jonathan@d14n.org>
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

import xml.dom.minidom as dom
import re

import rb3compat
from coverart_album_search import BaseSearch

if rb3compat.PYVER >= 3:
    import configparser
else:
    import ConfigParser as configparser

import os

import rb
from gi.repository import RB

import gettext

gettext.install('rhythmbox', RB.locale_dir())

# allow repeat searches once a week
REPEAT_SEARCH_PERIOD = 86400 * 7

# this API key belongs to foss.freedom@gmail.com
# and was generated specifically for this use
API_KEY = '844353bce568b93accd9ca47674d6c3e'
API_URL = 'http://ws.audioscrobbler.com/2.0/'

# LASTFM_LOGO = "lastfm_red_small.png"
# LASTFM_TOOLTIP = (LASTFM_LOGO, _("Image provided by Last.fm"))

DISC_NUMBER_REGEXS = (
    "\(disc *[0-9]+\)",
    "\(cd *[0-9]+\)",
    "\[disc *[0-9]+\]",
    "\[cd *[0-9]+\]",
    " - disc *[0-9]+$",
    " - cd *[0-9]+$",
    " disc *[0-9]+$",
    " cd *[0-9]+$"
)


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


class LastFMSearch(BaseSearch):
    def __init__(self):
        super(LastFMSearch, self).__init__()

    def search_url(self, artist, album, album_mbid):
        # Remove variants of Disc/CD [1-9] from album title before search
        orig_album = album
        for exp in DISC_NUMBER_REGEXS:
            p = re.compile(exp, re.IGNORECASE)
            album = p.sub('', album)

        album.strip()

        print("searching for (%s, %s, %s)" % (artist, album, album_mbid))
        url = API_URL + "?method=album.getinfo&"
        if artist != None:
            url = url + "artist=%s&" % (rb3compat.quote_plus(artist))
        if album != None:
            url = url + "album=%s&" % (rb3compat.quote_plus(album))
        if album_mbid != None:
            url = url + "mbid=%s&" % (rb3compat.quote_plus(album_mbid))

        url = url + "api_key=%s" % API_KEY
        print("last.fm query url = %s" % url)
        return url

    def album_info_cb(self, data):
        if data is None:
            print("last.fm query returned nothing")
            self.search_next()
            return

        parsed = dom.parseString(data)

        # find image URLs
        image_urls = []
        for tag in parsed.getElementsByTagName('image'):
            if tag.firstChild is None:
                print("got useless image tag")
                continue

            url = tag.firstChild.data
            url.strip()
            if url != "":
                print("found image url: %s" % url)
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
                print(size)

                self.store.store_uri(self.current_key, RB.ExtDBSourceType.SEARCH, url)
                self.callback(False)
            else:
                self.search_next()
        else:
            self.search_next()

    def search_next(self):
        if len(self.searches) == 0:
            self.callback(True)
            return
        print("search_next")
        print(self.searches)
        (artist, album, album_mbid) = self.searches.pop(0)
        self.current_key = RB.ExtDBKey.create_storage("album", album)
        key_artist = self.key.get_field("artist")
        if key_artist is None:
            self.current_key.add_field("artist", artist)
        else:
            self.current_key.add_field("artist", key_artist)

        url = self.search_url(artist, album, album_mbid)

        l = rb.Loader()
        self.rate_limit(l.get_url, (url, self.album_info_cb), 5)

    def search(self, key, last_time, store, callback, args):

        if user_has_account() == False:
            print("can't search: no last.fm account details")
            callback(True)
            return

        album = key.get_field("album")
        artists = key.get_field_values("artist")
        album_mbid = key.get_info("musicbrainz-albumid")
        self.key = key

        artists = [x for x in artists if x not in (None, "", _("Unknown"))]
        if album in ("", _("Unknown")):
            album = None

        if album == None or len(artists) == 0:
            print("can't search: no useful details")
            callback(True)
            return

        self.searches = []
        for a in artists:
            self.searches.append([a, album, album_mbid])
        self.searches.append(["Various Artists", album, album_mbid])

        self.store = store
        self.callback = callback
        self.callback_args = args
        self.search_next()
