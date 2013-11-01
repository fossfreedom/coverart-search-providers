coverart-search-providers v0.9.1
=========================

Drop in Rhythmbox replacement for the default CoverArt Search plugin to provide new and updated coverart search providers both local and by internet image hosts

##Authors

 - asermax <asermax@gmail.com>, website - https://github.com/asermax

[![Flattr Button](http://api.flattr.com/button/button-compact-static-100x17.png "Flattr This!")](http://flattr.com/thing/1262052/asermax-on-GitHub "asermax")

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

v0.9.1 Bug-Fixes

 - rate limit musicbrainz and coverart-archive to ensure results are returned
 - various python3 fixups
 - fix discogs searching to ensure artist/album is used to search
 - fix lastfm various-artists albums

Recommended order for Search Providers

 - embedded coverart
 - coverart in the track song folder
 - local cache search (~/.cache/rhythmbox/covers)
 - LastFM (use the LastFM plugin to login)
 - MusicBrainz
 - Discogs
 - Cover Art Archive

*How to install:*

 N.B. - if installing Rhythmbox 3.0 please see the important note 2 below.

for debian & debian-based distros such as Ubuntu & Mint (rhythmbox 2.96 - 2.99):

    sudo apt-get install git gettext python-mako python-mutagen python-requests
    
for debian & debian-based distros such as Ubuntu & Mint (rhythmbox 3.0 or compiled from git):

    sudo apt-get install git gettext python3-mako python3-requests
    

for fedora and similar:

    yum install git gettext python-mako python-mutagen python-requests
    
for opensuse:
 
    sudo zypper in git gettext-runtime python-mako python-mutagen python-requests

Then install the plugin:

<pre>
rm -rf ~/.local/share/rhythmbox/plugins/coverart_search_providers
git clone https://github.com/fossfreedom/coverart-search-providers.git
cd coverart-search-providers
</pre>

For rhythmbox 2.96 to 2.99:

<pre>
./install.sh
</pre>

For rhythmbox 3.0 or compiled from git:

<pre>
./install.sh --rb3
</pre>


*For Ubuntu 12.04, 12.10, 13.04 & 13.10:* 

This is now available in my rhythmbox PPA - installation instructions in this AskUbuntu Q&A:

http://askubuntu.com/questions/147942/how-do-i-install-third-party-rhythmbox-plugins

Note 1 - install the package `rhythmbox-plugin-coverart-search`

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

Note 2:

**PYTHON3 Support IMPORTANT**

Please read this issue for embedded artwork issues with python3

 - https://github.com/fossfreedom/coverart-browser/issues/227

Note 3:

LastFM API usage is as per LastFM licensing.  Do not copy rb_lastfm.py for your own purposes without obtaining your own API key.
