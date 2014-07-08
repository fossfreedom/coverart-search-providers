# -*- Mode: python; coding: utf-8; tab-width: 4; indent-tabs-mode: nil; -*-
# Copyright (C) 2012 - fossfreedom
# Copyright (C) 2012 - Agustin Carrasco
## adapted from artsearch plugin - Copyright (C) 2012 Jonathan Matthew
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

from gi.repository import RB
from gi.repository import GLib
from gi.repository import Gdk
from gi.repository import Gio
import rb3compat

import os, time,re
import threading
import discogs_client as discogs
import json
import chardet
import rb
import time
import base64

from coverart_search_tracks import mutagen_library

ITEMS_PER_NOTIFICATION = 10
IGNORED_SCHEMES = ('http', 'cdda', 'daap', 'mms')
REPEAT_SEARCH_PERIOD = 86400 * 7

DISC_NUMBER_REGEXS = (
    "\(disc *[0-9]+\)",
    "\(cd *[0-9]+\)",
    "\[disc *[0-9]+\]",
    "\[cd *[0-9]+\]",
    " - disc *[0-9]+$",
    " - cd *[0-9]+$",
    " disc *[0-9]+$",
    " cd *[0-9]+$",
    " volume *[0-9]")
    
SPOTIFY_API_URL = "https://api.spotify.com/v1/"


def file_root (f_name):
    return os.path.splitext (f_name)[0].lower ()

class CoverSearch(object):
    def __init__(self, store, key, last_time, searches):
        self.store = store
        self.key = key.copy()
        self.last_time = last_time
        self.searches = searches

    def next_search(self, continue_search):
        '''
        main routine that calls the search routine for each search provider
        unless one of the searches has found something

        outputs - return False means that nothing found
        inputs - True means continue with searching
               - False means a search routine recommends no more searching
        '''
        
        print("next search")
        print(continue_search)
        if len(self.searches) == 0 and continue_search:
            print("no more searches")
            key = RB.ExtDBKey.create_storage("album", self.key.get_field("album"))
            key.add_field("artist", self.key.get_field("artist"))
            self.store.store(key, RB.ExtDBSourceType.NONE, None)
            print("end of next_search False")
            return False

        if continue_search:
            search = self.searches.pop(0)
            print("calling search")
            print(search)
            search.search(self.key, self.last_time, self.store, self.search_done, None)
            print("end of next_search TRUE")
            return True
        else:
            return False

    def search_done(self, args):
        self.next_search(args)

class CoverAlbumSearch:
    def __init__ (self):
        self.current_time = time.time()

    def finished(self, results):
        parent = self.file.get_parent()

        continue_search = True
        base = file_root (self.file.get_basename())
        for f_name in results:
            if file_root (f_name) == base:
                uri = parent.resolve_relative_path(f_name).get_parse_name()
                found = self.get_embedded_image(uri)
                if found:
                    continue_search = False
                    break

        
        self.callback(continue_search)

    def _enum_dir_cb(self, fileenum, result, results):
        try:
            files = fileenum.next_files_finish(result)
            if files is None or len(files) == 0:
                #print "okay, done; got %d files" % len(results)
                self.finished(results)
                return

            for f in files:
                ct = f.get_attribute_string("standard::content-type")
                # assume readable unless told otherwise
                readable = True
                if f.has_attribute("access::can-read"):
                    readable = f.get_attribute_boolean("access::can-read")
                
                if ct is not None and ct.startswith("audio/") and readable:
                    #print "_enum_dir_cb %s " % f.get_name()
                    results.append(f.get_name())

            fileenum.next_files_async(ITEMS_PER_NOTIFICATION, GLib.PRIORITY_DEFAULT, None, self._enum_dir_cb, results)
        except Exception as e:
            print("okay, probably done: %s" % e)
            import sys
            sys.excepthook(*sys.exc_info())
            self.finished(results)


    def _enum_children_cb(self, parent, result, data):
        try:
            enumfiles = parent.enumerate_children_finish(result)
            enumfiles.next_files_async(ITEMS_PER_NOTIFICATION, GLib.PRIORITY_DEFAULT, None, self._enum_dir_cb, [])
        except Exception as e:
            print("okay, probably done: %s" % e)
            import sys
            sys.excepthook(*sys.exc_info())
            self.callback(True)


    def search (self, key, last_time, store, callback, args):
        if time.time() - self.current_time < 1:
            #enforce 1 second delay between requests otherwise musicbrainz will reject calls
            time.sleep(1)
            
        self.current_time = time.time()
        
        # ignore last_time
        print("calling search")
        location = key.get_info("location")
        if location is None:
            print("not searching, we don't have a location")
            callback(True)
            return

        self.file = Gio.file_new_for_uri(location)
        if self.file.get_uri_scheme() in IGNORED_SCHEMES:
            print('not searching for local art for %s' % (self.file.get_uri()))
            callback(True)
            return

        self.album = key.get_field("album")
        self.artists = key.get_field_values("artist")
        self.store = store
        self.callback = callback

        print('searching for local art for %s' % (self.file.get_uri()))
        parent = self.file.get_parent()
        enumfiles = parent.enumerate_children_async("standard::content-type,access::can-read,standard::name",
            0, 0, None, self._enum_children_cb, None)

    def get_embedded_image(self, search):
        print("get_embedded_image")
        import tempfile
        imagefilename = tempfile.NamedTemporaryFile(delete=False)
        
        key = RB.ExtDBKey.create_storage("album", self.album)
        key.add_field("artist", self.artists[0])
        parent = self.file.get_parent()
        print(parent)
        print("possible mp4")
        try:
            module = mutagen_library('mp4')
            mp = module.MP4(search)
        
            if len(mp[b'covr']) >= 1:
                imagefilename.write(mp[b'covr'][0])
                uri = parent.resolve_relative_path(imagefilename.name).get_uri()
                imagefilename.close()
                self.store.store_uri(key, RB.ExtDBSourceType.USER, uri)
                return True 
        except:
            pass

        print("possible flac")
        try:
            #flac 
            module = mutagen_library('')
            music = module.File(search)
            imagefilename.write(music.pictures[0].data)
            imagefilename.close()
            uri = parent.resolve_relative_path(imagefilename.name).get_uri()
            self.store.store_uri(key, RB.ExtDBSourceType.USER, uri)
            return True 
        except:
            pass

        print("possible ogg")
        try:
            module = mutagen_library('oggvorbis')
            o = module.OggVorbis(search)
            
            try:
                pic=o['COVERART'][0]
            except:
                pic=o['METADATA_BLOCK_PICTURE'][0]
                
            y=base64.b64decode(pic)
            imagefilename.write(y)
            imagefilename.close()
            uri = parent.resolve_relative_path(imagefilename.name).get_uri()
            self.store.store_uri(key, RB.ExtDBSourceType.USER, uri)
            return True 
        except:
            pass

        print("possible mp3")
        try:
            module = mutagen_library('id3')
            i = module.ID3(search)

            apic = i.getall('APIC')[0]
            imagefilename.write(apic.data)
            imagefilename.close()
            uri = parent.resolve_relative_path(imagefilename.name).get_uri()
            self.store.store_uri(key, RB.ExtDBSourceType.USER, uri)
            return True 
        except:
            pass

        print("dont know")
        imagefilename.delete=True
        imagefilename.close()
        
        return False


class DiscogsSearch (object):
    def __init__(self):
        discogs.user_agent = 'CoverartBrowserSearch/1.0 +https://github.com/fossfreedom/coverart-browser'

    def search_url (self, artist, album):
        # Remove variants of Disc/CD [1-9] from album title before search
        for exp in DISC_NUMBER_REGEXS:
            p = re.compile (exp, re.IGNORECASE)
            album = p.sub ('', album)

        album.strip()
        url = "%s/%s" % (artist,album)
        print("discogs url = %s" % url)
        return url

    def get_release_cb(self, store, key, searches, cbargs, callback):
        last_url = ""
        continue_search = True
        for search in searches:
            album = search[1]
            artist = search[0]
            url = self.search_url(artist, album)
            print("album %s artist %s url %s" % (album, artist, url))

            if url == last_url:
                continue
            last_url = url
            try:    
                s = discogs.Search(url)
                url = s.results()[0].data['images'][0]['uri']
                current_key = RB.ExtDBKey.create_storage("album", album)
                print(key.get_field("artist"))
                print(key.get_field_names())
                current_key.add_field("artist", key.get_field("artist"))
                store.store_uri(current_key, RB.ExtDBSourceType.SEARCH, url)
                print("found picture %s " % url)
                continue_search = False
                break
            except:
                pass

        self.callback(continue_search)
        return False
    
    def search(self, key, last_time, store, callback, args):
        #if last_time > (time.time() - REPEAT_SEARCH_PERIOD):
        #    callback (True)
        #    return

        album = key.get_field("album")
        artists = key.get_field_values("artist")
        artists = [x for x in artists if x not in (None, "", _("Unknown"))]
        if album in ("", _("Unknown")):
            album = None

        if album == None or len(artists) == 0:
            callback (True)
            return

        self.searches = []
        for a in artists:
            self.searches.append([a, album])

        self.searches.append(["Various Artists", album])

        self.callback = callback
        self.callback_args = args

        threading.Thread( target=self.get_release_cb, args=(store, key, self.searches, args, callback)).start()
        
class CoverartArchiveSearch(object):

    def __init__(self):
        # coverartarchive URL
        self.url = "http://coverartarchive.org/release/%s/"

    def get_release_cb (self, data, args):
        (key, store, callback, cbargs) = args
        if data is None:
            print("coverartarchive release request returned nothing")
            callback(True)
            return
        try:
            resp = json.loads(data.decode('utf-8'))
            image_url = resp['images'][0]['image']
            print(image_url)
            
            storekey = RB.ExtDBKey.create_storage('album', key.get_field('album'))
            storekey.add_field("artist", key.get_field("artist"))
            store.store_uri(storekey, RB.ExtDBSourceType.SEARCH, image_url)
            
            callback(False)
        except Exception as e:
            print("exception parsing coverartarchive response: %s" % e)
            callback(True)

    def search(self, key, last_time, store, callback, *args):
        key = key.copy()    # ugh
        album_id = key.get_info("musicbrainz-albumid")
        if album_id is None:
            print("no musicbrainz release ID for this track")
            callback(True)
            return

        url = self.url % (album_id)
        print(url)
        loader = rb.Loader()
        loader.get_url(url, self.get_release_cb, (key, store, callback, args))
        
class SpotifySearch (object):
    def __init__(self):
        self.current_time = time.time()

    def search_url (self, artist, album):
        # Remove variants of Disc/CD [1-9] from album title before search
        orig_album = album
        for exp in DISC_NUMBER_REGEXS:
            p = re.compile (exp, re.IGNORECASE)
            album = p.sub ('', album)

        album.strip()

        print("searching for (%s, %s)" % (artist, album))
        url = SPOTIFY_API_URL + "search?query="
        url = url + "album:%s" % (rb3compat.quote_plus(album))
        if artist:
            url = url + " artist:%s" % (rb3compat.quote_plus(artist))
        url = url + "&offset=0&limit=10&type=album"
        print("spotify query url = %s" % url)
        return url


    def album_info_cb (self, data, album_name):
        if data is None:
            print("spotify query returned nothing")
            self.search_next()
            return

        encoding = chardet.detect(data)['encoding']
        encoded = data.decode(encoding)
        json_data = json.loads(encoded)
        
        print (json_data['albums'])
        print (json_data['albums']['items'])
        
        albums = json_data['albums']['items']
        
        print (albums)
        for album in albums:
            print (album)
            print (album['name'])
            print (album_name)
            if album['name'] in album_name or \
               album_name in album['name']:
                print ('matching album  names')
                print (album['images'])
                print (album['images'][0])
                url = album['images'][0]['url']
                print (url)
                self.store.store_uri(self.current_key, RB.ExtDBSourceType.SEARCH, url)
                self.callback(False)
                print ('exited')
                return
        
        print ('getting next search')
        self.search_next()

    def search_next (self):
        if len(self.searches) == 0:
            self.callback(True)
            print ('no more searches')
            return
        print ("search_next")
        print (self.searches)
        (artist, album) = self.searches.pop(0)
        self.current_key = RB.ExtDBKey.create_storage("album", album)
        key_artist = self.key.get_field("artist")
        if key_artist is not None:
            self.current_key.add_field("artist", artist)

        print("####artist")
        print(artist)

        url = self.search_url(artist, album)

        l = rb.Loader()
        l.get_url(url, self.album_info_cb, album)


    def search(self, key, last_time, store, callback, args):
        if time.time() - self.current_time < 1:
            #enforce 0.5 second delay between requests otherwise spotify will reject calls
            time.sleep(0.5)
            
        self.current_time = time.time()
        
        album = key.get_field("album")
        artists = key.get_field_values("artist")
        self.key = key

        artists = [x for x in artists if x not in (None, "", _("Unknown"))]
        if album in ("", _("Unknown")):
            album = None

        if album == None or len(artists) == 0:
            print("can't search: no useful details")
            callback (True)
            return

        self.searches = []
        for a in artists:
            self.searches.append([a, album])
        self.searches.append(["Various Artists", album])

        self.store = store
        self.callback = callback
        self.callback_args = args
        self.search_next()
