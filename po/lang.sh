#!/bin/sh
echo "installing languages to $1"
lang=`echo $LANG | cut -d'.' -f 1`

if [ ! -f $lang.po ]; then
   lang=`echo $lang | cut -d'_' -f 1`

    if [ ! -f $lang.po ]; then
        echo "no $lang.po to install"
        exit
    fi
fi

echo "installing $lang"
install -d $1$lang/LC_MESSAGES
msgfmt -c $lang.po -o $1$lang/LC_MESSAGES/coverart_search_providers.mo
