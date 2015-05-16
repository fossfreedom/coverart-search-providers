coverart-search-providers v1.2.1
=========================

Drop in Rhythmbox replacement for the default CoverArt Search plugin to provide new and updated coverart search providers both local and by internet image hosts

##Author

 - fossfreedom <foss.freedom@gmail.com>, website - https://github.com/fossfreedom

[![Flattr Button](http://api.flattr.com/button/button-compact-static-100x17.png "Flattr This!")](http://flattr.com/thing/1811718/ "fossfreedom")  [![paypaldonate](https://www.paypalobjects.com/en_GB/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=KBV682WJ3BDGL)

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
5. External interface to find covers for artists

v0.9.1 Bug-Fixes

 - rate limit musicbrainz and coverart-archive to ensure results are returned
 - various python3 fixups
 - fix discogs searching to ensure artist/album is used to search
 - fix lastfm various-artists albums
 
v1.0

 - external API to retrieve artists
 - support for embedded artwork for RB3 and later (Note 2)
 
v1.1

 - made installation default to RB3
 - install only locale specific to the environment rather than all locales
 - added uninstall routine
 - tidied preferences window
 - fix crash for RB2.99
 - removed Discogs since they now require oauth2 support
 - add Spotify as an coverart provider
 - fix bug to carry on search after binning poor MusicBrainz image download
 - restructure rate-limits to ensure faster downloads whilst keeping to providers rate-limits

v1.2
 - support song-info dialog for Rhythmbox 3.2
 - use RB's own embedded art search method as well as mutagen for wider embedded-art coverage
 
v1.2.1
 - bug fix - for locales not found, exit the language installer gracefully

Recommended order for Search Providers

 - embedded coverart
 - coverart in the track song folder
 - local cache search (~/.cache/rhythmbox/covers)
 - LastFM (rate-limit: 5 requests per second) N.B. use the LastFM plugin to login
 - Spotify (rate-limit: 2 requests per second)
 - Cover Art Internet Archive (rate-limit: 1 request per second)
 - MusicBrainz (rate-limit: 1 request per second)

*How to install - Rhythmbox 2.96 to 2.99.1:*

for debian & debian-based distros such as Ubuntu & Mint (rhythmbox 2.96 - 2.99):

    sudo apt-get install git gettext python-mako python-mutagen python-requests python-gdbm python-imaging

for fedora and similar:

    sudo yum install git gettext python-mako python-mutagen python-requests
    
for opensuse:
 
    sudo zypper in git gettext-runtime python-mako python-mutagen python-requests

Then install the plugin:

<pre>
rm -rf ~/.local/share/rhythmbox/plugins/coverart_search_providers
git clone https://github.com/fossfreedom/coverart-search-providers.git
cd coverart-search-providers
./install.sh --rb2
</pre>

*How to install - Rhythmbox 3.0 and later:*

for ubuntu 13.10 & ubuntu-based distros such as Mint based on 13.10:

    sudo apt-get install git gettext python3-mako python3-requests python3-gdbm python3-imaging python3-lxml
    
for debian and other debian derived distros (such as ubuntu 14.04 & Mint based on 14.04):

    sudo apt-get install git gettext python3-mako python3-requests python3-gdbm python3-pil python3-lxml
   
for fedora and similar:

    sudo yum install git gettext python3-mako python3-requests python3-pillow python3-lxml

For other distro's please raise an issue and let me know what the installation instructions are.  Thanks.

<pre>
rm -rf ~/.local/share/rhythmbox/plugins/coverart_search_providers
git clone https://github.com/fossfreedom/coverart-search-providers.git
cd coverart-search-providers
./install.sh
</pre>

*To Uninstall:*

<pre>
cd coverart-search-providers
./install.sh --uninstall
</pre>

*IMPORTANT NOTE FOR ALL DISTRO's - Requirement for the installation of Mutagen*

*For Ubuntu 12.04 to 14.04:* 

This is now available in my rhythmbox PPA - installation instructions in this AskUbuntu Q&A:

http://askubuntu.com/questions/147942/how-do-i-install-third-party-rhythmbox-plugins

install the package `rhythmbox-plugin-coverart-search`

*Note 1:*

*support for embedded coverart - rhythmbox 2.96 to 2.99.1*

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

*Note 2:*

*support for embedded coverart - rhythmbox 3.0 and later*

The plugin requires python3-mutagen (v1.25 or later) which is available from PyPi

 - https://pypi.python.org/pypi/mutagen
 
python3-mutagen is Debian packaged from my PPA:

 - https://launchpad.net/~fossfreedom/+archive/rhythmbox-plugins
 
Some distro's such as Arch have python3-mutagen already packaged.  Debian Sid also contains a python3-mutagen debian installer.

*Note 3:*

LastFM API usage is as per LastFM licensing.  Do not copy rb_lastfm.py for your own purposes without obtaining your own API key.
