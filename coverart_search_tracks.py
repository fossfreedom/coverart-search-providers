# -*- Mode: python; coding: utf-8; tab-width: 4; indent-tabs-mode: nil; -*-
#
# Copyright (C) 2012 - fossfreedom
# Copyright (C) 2012 - Agustin Carrasco
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of thie GNU General Public License as published by
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
from gi.repository import Gio

from mutagen.oggvorbis import OggVorbis
import mutagen.flac
from mutagen import File
from mutagen.id3 import ID3
from mutagen.mp4 import MP4
from mutagen.mp4 import MP4Cover
from mutagen.id3 import APIC

import base64
from mimetypes import MimeTypes
import os,itertools

IGNORED_SCHEMES = ('http', 'cdda', 'daap', 'mms')

def anyTrue(pred,seq):
    '''Returns True if a True predicate is found, False
    otherwise. Quits as soon as the first True is found
    '''
    return True in itertools.imap(pred,seq)

class CoverArtTracks(object):
    def __init__(self):
        pass

    def get_mimetype(self, art_location):
        mime = MimeTypes()
        mimetype = mime.guess_type(art_location)
        return mimetype[0]

    def embed_ogg(self, art_location, search, mimetypestr):
        '''
        :art_location: file path to the picture to embed
        :search: file path to the music track file
        :mimetypestr: mimetype of the picture to embed
        '''
        try:
            o = OggVorbis(search)
            
            # lets get all tags into a dict
            # lets also remove the deprecated coverart tag and any
            # old pictures
            
            tags = {}
            for orig, values in o.tags.items():
                if orig.lower() != 'coverart' and \
                   orig.lower() != 'metadata_block_picture':
                    tags[orig]=values

            image = mutagen.flac.Picture()
            image.type = 3 # Cover image
            image.data = open(art_location).read()
            image.mime = mimetypestr
            image.desc = u'cover description'
            tags.setdefault(u"METADATA_BLOCK_PICTURE",
                []).append(base64.standard_b64encode(image.write()))
            
            o.tags.update(tags)
            o.save()
        except:
            pass

    def embed_flac(self, art_location, search, mimetypestr):
        '''
        :art_location: file path to the picture to embed
        :search: file path to the music track file
        :mimetypestr: mimetype of the picture to embed
        '''
        try:
            music = File(search)
            
            # lets remove any old pictures
            music.clear_pictures()
            image = mutagen.flac.Picture()
            image.type = 3 # Cover image
            image.data = open(art_location).read()
            image.mime = mimetypestr
            image.desc = u'cover description'
            music.add_picture(image)
            music.save()
        except:
            pass

    def embed_mp4(self, art_location, search, mimetypestr):
        '''
        :art_location: file path to the picture to embed
        :search: file path to the music track file
        :mimetypestr: mimetype of the picture to embed
        '''
        try:
            music = MP4(search)

            covr = []
            data = open(art_location).read()
            if mimetypestr == "image/jpeg":
                covr.append(MP4Cover(data, MP4Cover.FORMAT_JPEG))
            elif mimetypestr == "image/png":
                covr.append(MP4Cover(data, MP4Cover.FORMAT_PNG))
            if covr:
                music.tags["covr"] = covr
                music.save()
        except:
            pass

    def embed_mp3(self, art_location, search, mimetypestr):
        '''
        :art_location: file path to the picture to embed
        :search: file path to the music track file
        :mimetypestr: mimetype of the picture to embed
        '''
        try:
            music = ID3(search)

            # lets remove any old pictures
            music.delall('APIC')
            
            music.add(APIC(encoding=0, mime=mimetypestr, type=3,
               desc='', data=open(art_location).read()))

            music.save()
        except:
            pass

    def embed(self, track_uri, key):
        '''
        embed tracks with the coverart

        :track_uri: nominally RB.RhythmDBPropType.LOCATION
        :key: RB.ExtDBKey containing the lookup for the cover to apply

        returns True or False depending if the routine completed successfully
        '''

        the=anyTrue # for readability

        art_location = RB.ExtDB(name='album-art').lookup(key)

        #print key
        print art_location
        
        search = Gio.file_new_for_uri(track_uri)
        if search.get_uri_scheme() in IGNORED_SCHEMES:
            print 'not a valid scheme %s' % (search.get_uri())
            return False
 
        if search.get_path().lower().endswith('.ogg'):
            self.embed_ogg(art_location, search.get_path(), 'image/jpeg')

        if search.get_path().lower().endswith('.flac'):
            self.embed_flac(art_location, search.get_path(), 'image/jpeg')

        if search.get_path().lower().endswith('.mp3'):
            self.embed_mp3(art_location, search.get_path(), 'image/jpeg')
        
        if the(search.get_path().lower().endswith,(".m4a", ".m4b", ".m4p", ".mp4")):
            self.embed_mp4(art_location, search.get_path(), 'image/jpeg')

        return True
