#!/usr/bin/env python

import os, sys

# Exclude paths
EXCLUSIONS = (
    "mirror/i18n",
)

POTFILE_IN = "mirror/i18n/POTFILES.in"

sys.stdout.write("Creating " + POTFILE_IN + " ... \n")
sys.stdout.flush()
to_translate = []
for (dirpath, dirnames, filenames) in os.walk("mirror"):
    for filename in filenames:
        if os.path.splitext(filename)[1] in (".py", ".in") \
                    and dirpath not in EXCLUSIONS:
            to_translate.append(os.path.join(dirpath, filename))

fp = open(POTFILE_IN, "wb")
for line in to_translate:
    fp.write(line + "\n")
fp.close()

print "Done"
