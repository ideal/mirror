#!/bin/sh

PACKAGE="Mirror"
PKG_VERSION=`grep "version\ =\ \"" setup.py | cut -d '"' -f2`
PO_DIR="mirror/i18n"
POTFILES_IN="infiles.list"
POT_FILE=mirror.pot 

echo "Creating $PO_DIR/$POT_FILE ..."
cp $PO_DIR/POTFILES.in $POTFILES_IN

xgettext --from-code=UTF-8 -kN_:1 -f $POTFILES_IN -o $PO_DIR/$POT_FILE --package-name=$PACKAGE \
    --copyright-holder='Mirror at BJTU' --package-version=$PKG_VERSION \
    --msgid-bugs-address=http://mirror.bjtu.edu.cn

# sub the YEAR in the copyright message
# 2 in sed means two places
sed -i -e '2s/YEAR/'`date +%Y`'/' "$PO_DIR/$POT_FILE"

rm -f $POTFILES_IN
echo "Done"
