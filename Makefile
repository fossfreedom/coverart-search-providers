DESTDIR=
SUBDIR=/usr/lib/rhythmbox/plugins/coverart_search_providers/
DATADIR=/usr/share/rhythmbox/plugins/coverart_search_providers/
LOCALEDIR=/usr/share/locale/
GLIB_SCHEME=org.gnome.rhythmbox.plugins.coverart_search_providers.gschema.xml
GLIB_DIR=/usr/share/glib-2.0/schemas/


all:
clean:
	- rm *.pyc

install:
	install -d $(DESTDIR)$(SUBDIR)
	install -m 644 *.py $(DESTDIR)$(SUBDIR)
	install -d $(DESTDIR)$(DATADIR)ui
	install -m 644 ui/*.ui $(DESTDIR)$(DATADIR)ui/
	install -m 644 coverart_search_providers.plugin* $(DESTDIR)$(SUBDIR)
	install -d $(DESTDIR)$(GLIB_DIR)
	install -m 644 schema/$(GLIB_SCHEME) $(DESTDIR)$(GLIB_DIR) 
	cd po;./install_all.sh $(DESTDIR)$(LOCALEDIR)
