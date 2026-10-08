#!/bin/sh

case "$CKAN__PLUGINS" in
  *"datapusher_plus"*)
    # DP+ caches ckan.datastore.write_url at import time, before CKAN applies
    # CKAN_DATASTORE_WRITE_URL, so it has to be in the ini file
    echo "Setting ckan.datastore.write_url for datapusher_plus"
    ckan config-tool "$CKAN_INI" "ckan.datastore.write_url=$CKAN_DATASTORE_WRITE_URL"
    echo "datapusher_plus db upgrade"
    ckan --config="$CKAN_INI" db upgrade -p datapusher_plus
    ;;
  *)
    echo "Not configuring datapusher_plus"
    ;;
esac
