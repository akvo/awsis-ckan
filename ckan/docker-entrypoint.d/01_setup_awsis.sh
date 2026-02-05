#!/bin/sh

case "$CKAN__PLUGINS" in
  *"awsis"*)
    echo "Installing awsis theme extension..."
    pip install -e /srv/app/src_extensions/ckanext-awsis
    echo "awsis theme extension installed"
    ;;
  *)
    echo "Not configuring awsis theme"
    ;;
esac
