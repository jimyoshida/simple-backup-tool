#!/bin/bash
set -e

PKG_DIR=tmp
PKG_FILE=$1

mkdir -p "$PKG_DIR/DEBIAN" "$PKG_DIR/usr/local/bin" "$PKG_DIR/usr/local/share/man/man1"
cp src/sbt.py "$PKG_DIR/usr/local/bin/sbt"
chmod +x "$PKG_DIR/usr/local/bin/sbt"
gzip -c doc/sbt.1 > "$PKG_DIR/usr/local/share/man/man1/sbt.1.gz"
cp DEBIAN/control "$PKG_DIR/DEBIAN/control"

mkdir -p out
dpkg-deb --build "$PKG_DIR" "$PKG_FILE"
