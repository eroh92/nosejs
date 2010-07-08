#!/bin/sh

# fixme: this is the quick and dirty way I have been testing
# the plugin.  needs self-contained unit tests
source _env/bin/activate
cd ~/dev/fudge/
nosetests -v --with-javascript --rhino-jar  ~/src/rhino1_7R1/js.jar --with-dom --javascript-dir javascript/fudge/tests/ $@