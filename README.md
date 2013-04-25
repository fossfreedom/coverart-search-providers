coverart-search-providers
=========================

Drop in Rhythmbox replacement for the default CoverArt Search plugin to provide new and updated coverart search providers both local and by internet image hosts

##Authors

 - asermax <asermax@gmail.com>, website - https://github.com/asermax

[![Flattr Button](http://api.flattr.com/button/button-compact-static-100x17.png "Flattr This!")](http://flattr.com/thing/1262052/asermax-on-GitHub "asermax")

 - fossfreedom <foss.freedom@gmail.com>, website - https://github.com/fossfreedom

[![Flattr Button](http://api.flattr.com/button/button-compact-static-100x17.png "Flattr This!")](https://flattr.com/thing/1238849/fossfreedom-at-Flattr "fossfreedom")  [![paypaldonate](https://www.paypalobjects.com/en_GB/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=KBV682WJ3BDGL)

-------------

Fixes made for the default ArtSearch

1. jamendo local file names correctly found i.e. $artist - $album covers
2. Pull in RB v2.98 MusicBrainz search patch
3. Fix cover display for "Various Artists" from MusicBrainz
4. test the file size before downloading - ignore files that are less than 100 bytes


Enhancements:

1. Choose which providers that you want to search with
2. Choose the search provider order
2. When a search provider finds a cover, stop further searches
3. find and extract embedded covers in MP3, M4A, FLAC & Ogg files
4. API to embed coverart in MP3, M4A, FLAC & Ogg files

Recommended order for Search Providers

 - embedded coverart
 - coverart in the track song folder
 - local cache search (~/.cache/rhythmbox/covers)
 - LastFM (use the LastFM plugin to login)
 - MusicBrainz
 - Discogs
 - Cover Art Archive

*How to install:*

for debian & debian-based distros such as Ubuntu & Mint

    sudo apt-get install git gettext python-mako python-mutagen python-requests

for fedora and similar:

    yum install git gettext python-mako python-mutagen python-requests

Then install the plugin:

<pre>
rm -rf ~/.local/share/rhythmbox/plugins/coverart_search_providers
git clone https://github.com/fossfreedom/coverart-search-providers.git
cd coverart-search-providers
sh ./install.sh
</pre>

*For Ubuntu 12.04 & 12.10:* 

This is now available in my rhythmbox PPA - installation instructions in this AskUbuntu Q&A:

http://askubuntu.com/questions/147942/how-do-i-install-third-party-rhythmbox-plugins

Note - install the package `rhythmbox-plugin-coverart-search`

*installation for embedded coverart*

The plugin makes use of the package `python-mutagen`.  For most distros, the default package is v1.20 which was released in 2010.

Since then, lots of bug fixes have been resolved.  If you know that there is coverart embedded, but is not displayed
in our plugin, then you should install the very latest package:

<pre>
hg clone https://code.google.com/p/mutagen/
</pre>

Then following the instructions in the README (slightly modified)

<pre>
./setup.py build
sudo su
./setup.py install 
</pre>

Note:

LastFM API usage is as per LastFM licensing.  Do not copy rb_lastfm.py for your own purposes without obtaining your own API key.
