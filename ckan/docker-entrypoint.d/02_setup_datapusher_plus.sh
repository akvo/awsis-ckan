#!/bin/sh

case "$CKAN__PLUGINS" in
  *"datapusher_plus"*)
    # DP+ caches its settings (and ckan.datastore.write_url) at import time,
    # before CKAN applies env vars, so they have to be in the ini file
    if [ -n "$CKAN_DATASTORE_WRITE_URL" ]; then
      echo "Setting ckan.datastore.write_url for datapusher_plus"
      ckan config-tool "$CKAN_INI" "ckan.datastore.write_url=$CKAN_DATASTORE_WRITE_URL"
    fi
    if [ -n "$CKANEXT__DATAPUSHER_PLUS__QSV_DATES_WHITELIST" ]; then
      echo "Setting ckanext.datapusher_plus.qsv_dates_whitelist"
      ckan config-tool "$CKAN_INI" "ckanext.datapusher_plus.qsv_dates_whitelist=$CKANEXT__DATAPUSHER_PLUS__QSV_DATES_WHITELIST"
    fi
    echo "datapusher_plus db upgrade"
    ckan --config="$CKAN_INI" db upgrade -p datapusher_plus
    ;;
  *)
    echo "Not configuring datapusher_plus"
    ;;
esac
