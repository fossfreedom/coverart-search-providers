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

import base64
from mimetypes import MimeTypes
import os
import itertools
from PIL import Image
import tempfile
import importlib

def mutagen_library(module_name):
    module = None

    def lookfor(library):
        if module_name == "":
            return library
        else:
            return library + "." + module_name
        
    try:
        module = importlib.import_module(lookfor('mutagen'))
    except ImportError:
        module = importlib.import_module(lookfor('mutagenx'))
        
    return module
  
IGNORED_SCHEMES = ('http', 'cdda', 'daap', 'mms')

def anyTrue(pred,seq):
    '''Returns True if a True predicate is found, False
    otherwise. Quits as soon as the first True is found
    '''
    return True in map(pred,seq)

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
            module = mutagen_library('oggvorbis')
            o = module.OggVorbis(search)
            
            # lets get all tags into a dict
            # lets also remove the deprecated coverart tag and any
            # old pictures
            
            tags = {}
            for orig, values in list(o.tags.items()):
                if orig.lower() != 'coverart' and \
                   orig.lower() != 'metadata_block_picture':
                    tags[orig]=values

            module = mutagen_library('flac')
            image = module.Picture()
            image.type = 3 # Cover image
            image.data = str(open(art_location, "rb").read())
            image.mime = mimetypestr
            image.desc = 'cover description'
            tags.setdefault("METADATA_BLOCK_PICTURE",
                []).append(base64.b64encode(image.write()))
            
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
            module = mutagen_library('')
            music = module.File(search)
            
            # lets remove any old pictures
            music.clear_pictures()
            module = mutagen_library('flac')
            image = module.Picture()
            image.type = 3 # Cover image
            image.data = open(art_location, "rb").read()
            image.mime = mimetypestr
            image.desc = 'cover description'
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
            module = mutagen_library('mp4')
            music = module.MP4(search)

            covr = [] 
            data = open(art_location, "rb").read()
            
            if mimetypestr == "image/jpeg":
                covr.append(module.MP4Cover(data, module.MP4Cover.FORMAT_JPEG))
            elif mimetypestr == "image/png":
                covr.append(module.MP4Cover(data, module.MP4Cover.FORMAT_PNG))
            if covr:
                music.tags[b"covr"] = covr
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
            module = mutagen_library('id3')
            music = module.ID3(search)

            # lets remove any old pictures
            music.delall('APIC')
            
            
            music.add(module.APIC(encoding=0, mime=mimetypestr, type=3,
               desc='', data=open(art_location, "rb").read()))

            music.save()
        except:
            pass

    def embed(self, track_uri, key, resize=-1):
        '''
        embed tracks with the coverart

        :track_uri: nominally RB.RhythmDBPropType.LOCATION
        :key: RB.ExtDBKey containing the lookup for the cover to apply
        :resize: int this is the size of the embedded image to resize to

        returns True or False depending if the routine completed successfully
        '''

        the=anyTrue # for readability

        art_location = RB.ExtDB(name='album-art').lookup(key)

        if not art_location:
            print ("not a valid key to a file containing art")
            return False
            
        image = Image.open(art_location)
        f, art_location = tempfile.mkstemp(suffix=".jpg")
            
        print ("resizing?")
        print (resize)
        if resize > 0:
            tosave = image.resize((resize,resize), Image.ANTIALIAS)
        else:
            tosave = image
            
        print (art_location)
        tosave.save(art_location)
        
        search = Gio.file_new_for_uri(track_uri)
        if search.get_uri_scheme() in IGNORED_SCHEMES:
            print('not a valid scheme %s' % (search.get_uri()))
            return False
 
        if search.get_path().lower().endswith('.ogg'):
            self.embed_ogg(art_location, search.get_path(), 'image/jpeg')

        if search.get_path().lower().endswith('.flac'):
            self.embed_flac(art_location, search.get_path(), 'image/jpeg')

        if search.get_path().lower().endswith('.mp3'):
            self.embed_mp3(art_location, search.get_path(), 'image/jpeg')
        
        if the(search.get_path().lower().endswith,(".m4a", ".m4b", ".m4p", ".mp4")):
            self.embed_mp4(art_location, search.get_path(), 'image/jpeg')

        os.remove(art_location)
        
        return True
