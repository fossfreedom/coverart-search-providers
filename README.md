coverart-search-providers
=========================

Drop in Rhythmbox replacement for the default CoverArt Search plugin to provide new and updated coverart search providers both local and by internet image hosts

Fixes made for the default ArtSearch

1. jamendo local file names correctly found i.e. $artist - $album covers
2. Pull in RB v2.98 MusicBrainz search patch
3. Fix cover display for "Various Artists" from MusicBrainz
4. test the file size before downloading - ignore files that are less than 100 bytes


Enhancements:

1. Choose which providers that you want to search with
2. When a search provider finds a cover, stop further searches

Search Providers (in the order searched)

 - embedded coverart
 - coverart in the track song folder
 - local cache search (~/.cache/rhythmbox/covers)
 - LastFM (use the LastFM plugin to login)
 - MusicBrainz
 - Discogs
 - Cover Art Archive


Note:

LastFM API usage is as per LastFM licensing.  Do not copy rb_lastfm.py for your own purposes without obtaining your own API key.
