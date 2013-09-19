#!/bin/sh
echo "updating po files"
for i in *.po; do
	lang=`basename $i .po`
	echo "updating $lang"
    intltool-update --dist $lang -g coverartsearchproviders
done

echo "update plugin file"

intltool-merge -d . ../coverart_search_providers.plugin.in ../coverart_search_providers.plugin
intltool-merge -d . ../coverart_search_providers.plugin3.in ../coverart_search_providers.plugin3
