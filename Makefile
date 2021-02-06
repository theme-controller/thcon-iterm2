SOURCE_FILE := thcon.py
IT2_AUTOLAUNCH := $(HOME)/Library/Application\ Support/iTerm2/Scripts/AutoLaunch
DEST_FILE := $(IT2_AUTOLAUNCH)/$(SOURCE_FILE)

nop:
	@echo "Nothing to build; you probably want to install with 'make install'"

install: $(SOURCE_FILE) $(IT2_AUTOLAUNCH)
	ln -sf $(PWD)/$(SOURCE_FILE) $(DEST_FILE)

$(IT2_AUTOLAUNCH):
	mkdir -p $(IT2_AUTOLAUNCH)

uninstall:
	rm -rf $(DEST_FILE)
