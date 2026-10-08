#!/usr/bin/env bash
# Smoke test for a running AWSIS CKAN stack: versions, plugins, pages and a
# CSV -> DataPusher+ -> DataStore round-trip.
#
# Usage (from the repo root):
#   CKAN_API_TOKEN=<sysadmin token> scripts/smoke-test.sh
#
# Env:
#   CKAN_API_TOKEN  sysadmin API token (required)
#   CKAN_URL        default http://localhost:5000
#   COMPOSE         default ./dc.sh (e.g. "docker compose -f docker-compose.yml")
#   SERVICE         default ckan-dev (use "ckan" for the prod compose)
#   SMOKE_KEEP      1 = keep the smoke dataset and print KEPT_RESOURCE_ID=<id>
#   EXPECT_DPP      expected datapusher-plus git tag, default 3.0.0
#   EXPECT_QSV      expected qsvdp version, default 13.0.0
#   SMOKE_TIMEOUT   seconds to wait for DataStore ingestion, default 180

set -euo pipefail

: "${CKAN_API_TOKEN:?CKAN_API_TOKEN is required (sysadmin API token)}"
CKAN_URL="${CKAN_URL:-http://localhost:5000}"
COMPOSE="${COMPOSE:-./dc.sh}"
SERVICE="${SERVICE:-ckan-dev}"
SMOKE_KEEP="${SMOKE_KEEP:-0}"
EXPECT_DPP="${EXPECT_DPP:-3.0.0}"
EXPECT_QSV="${EXPECT_QSV:-13.0.0}"
SMOKE_TIMEOUT="${SMOKE_TIMEOUT:-180}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURE="$SCRIPT_DIR/fixtures/smoke.csv"
read -ra COMPOSE_CMD <<< "$COMPOSE"

FAILURES=0
DATASET_NAME=""

pass() { echo "PASS $1"; }
fail() { echo "FAIL $1: $2"; FAILURES=$((FAILURES + 1)); }

in_ckan() { "${COMPOSE_CMD[@]}" exec -T "$SERVICE" "$@"; }

# api <action> [curl args...] -> JSON body; fails unless .success == true
api() {
    local action="$1"; shift
    local body
    body="$(curl -sS -H "Authorization: $CKAN_API_TOKEN" "$@" "$CKAN_URL/api/3/action/$action")"
    if [ "$(jq -r '.success' <<< "$body" 2>/dev/null)" != "true" ]; then
        echo "$action failed: $(jq -c '.error // .' <<< "$body" 2>/dev/null || echo "$body")" >&2
        return 1
    fi
    echo "$body"
}

api_json() { api "$1" -X POST -H 'Content-Type: application/json' -d "$2"; }

cleanup() {
    if [ -n "$DATASET_NAME" ] && [ "$SMOKE_KEEP" != "1" ]; then
        # dataset_purge leaves DataStore tables behind, so drop them first
        for rid in $(api_json package_show "{\"id\":\"$DATASET_NAME\"}" 2>/dev/null | jq -r '.result.resources[].id' || true); do
            api_json datastore_delete "{\"resource_id\":\"$rid\",\"force\":true}" > /dev/null 2>&1 || true
        done
        api_json dataset_purge "{\"id\":\"$DATASET_NAME\"}" > /dev/null || true
    fi
}
trap cleanup EXIT

check_qsv_version() {
    local out
    out="$(in_ckan qsvdp --version 2>&1 || true)"
    if [[ "$out" == "qsvdp $EXPECT_QSV"* ]]; then pass qsv_version
    else fail qsv_version "expected qsvdp $EXPECT_QSV, got '${out%%$'\n'*}'"; fi
}

# Reads the git tag of the editable checkout: DP+ package metadata is not
# reliable (the 3.0.0 tag still declares version 2.0.0 in pyproject.toml).
check_dpp_version() {
    local version
    version="$(in_ckan sh -c 'git -c safe.directory="*" -C "$SRC_DIR/datapusher-plus" describe --tags --exact-match' 2>/dev/null || true)"
    if [ "$version" = "$EXPECT_DPP" ]; then pass dpp_version
    else fail dpp_version "expected $EXPECT_DPP, got '${version:-not installed}'"; fi
}

check_file_bin() {
    if in_ckan test -x /usr/bin/file; then pass file_bin
    else fail file_bin "/usr/bin/file missing in $SERVICE"; fi
}

check_plugins_loaded() {
    local plugins loaded missing=()
    plugins="$(in_ckan printenv CKAN__PLUGINS | tr -d '"')" || { fail plugins_loaded "cannot read CKAN__PLUGINS from $SERVICE"; return; }
    loaded="$(api status_show | jq -r '.result.extensions[]')" || { fail plugins_loaded "status_show failed"; return; }
    for p in $plugins; do
        grep -qx "$p" <<< "$loaded" || missing+=("$p")
    done
    if [ ${#missing[@]} -eq 0 ]; then pass plugins_loaded
    else fail plugins_loaded "not loaded: ${missing[*]}"; fi
}

check_pages_render() {
    local bad=() code
    for path in / /dataset/ /organization/ /about; do
        code="$(curl -s -o /dev/null -w '%{http_code}' "$CKAN_URL$path")"
        [ "$code" = "200" ] || bad+=("$path=$code")
    done
    if [ ${#bad[@]} -eq 0 ]; then pass pages_render
    else fail pages_render "${bad[*]}"; fi
}

# Polls until the resource is in the DataStore; prints DP+ status on timeout.
wait_for_datastore() {
    local resource_id="$1" waited=0
    while [ "$waited" -lt "$SMOKE_TIMEOUT" ]; do
        if [ "$(api_json resource_show "{\"id\":\"$resource_id\"}" | jq -r '.result.datastore_active')" = "true" ]; then
            return 0
        fi
        sleep 5
        waited=$((waited + 5))
    done
    echo "datapusher_status after ${SMOKE_TIMEOUT}s:" >&2
    api_json datapusher_status "{\"resource_id\":\"$resource_id\"}" | jq '.result' >&2 || true
    return 1
}

check_datastore_roundtrip() {
    local org_id resource_id search types
    if ! org_id="$(api_json organization_show '{"id":"smoke-test-org"}' 2>/dev/null | jq -r '.result.id')"; then
        org_id="$(api_json organization_create '{"name":"smoke-test-org","title":"Smoke Test Org"}' | jq -r '.result.id')" \
            || { fail datastore_roundtrip "could not create smoke-test-org"; return; }
    fi

    DATASET_NAME="smoke-test-$(date +%s)"
    api_json package_create "{\"name\":\"$DATASET_NAME\",\"owner_org\":\"$org_id\"}" > /dev/null \
        || { fail datastore_roundtrip "package_create failed"; DATASET_NAME=""; return; }

    resource_id="$(api resource_create -X POST \
        -F "package_id=$DATASET_NAME" -F "name=smoke.csv" -F "format=CSV" \
        -F "upload=@$FIXTURE" | jq -r '.result.id')" \
        || { fail datastore_roundtrip "resource_create failed"; return; }
    [ "$SMOKE_KEEP" = "1" ] && echo "KEPT_RESOURCE_ID=$resource_id"

    wait_for_datastore "$resource_id" \
        || { fail datastore_roundtrip "resource $resource_id not in DataStore after ${SMOKE_TIMEOUT}s"; return; }

    search="$(api_json datastore_search "{\"resource_id\":\"$resource_id\"}")" \
        || { fail datastore_roundtrip "datastore_search failed"; return; }
    types="$(jq -c '[.result.fields[] | {(.id): .type}] | add' <<< "$search")"

    if [ "$(jq -r '.result.total' <<< "$search")" = "3" ] \
        && jq -e '.id == "numeric" and .salinity_ppt == "numeric" and .station == "text"
                  and (.measured_date == "date" or .measured_date == "timestamp")' <<< "$types" > /dev/null; then
        pass datastore_roundtrip
    else
        fail datastore_roundtrip "total=$(jq -r '.result.total' <<< "$search") types=$types"
    fi

    check_resubmit_unchanged "$resource_id"
}

# Re-pushing an unchanged file must finish cleanly (DP+ skips it by hash).
check_resubmit_unchanged() {
    local resource_id="$1" status="" waited=0
    # result false means a pending job was found and nothing new was queued
    [ "$(api_json datapusher_submit "{\"resource_id\":\"$resource_id\"}" | jq -r '.result')" = "true" ] \
        || { fail resubmit_unchanged "datapusher_submit did not queue a new job"; return; }
    while [ "$waited" -lt "$SMOKE_TIMEOUT" ]; do
        sleep 5
        waited=$((waited + 5))
        status="$(api_json datapusher_status "{\"resource_id\":\"$resource_id\"}" | jq -r '.result.status')" || status=""
        [ "$status" = "complete" ] || [ "$status" = "error" ] && break
    done
    if [ "$status" = "complete" ]; then pass resubmit_unchanged
    else
        fail resubmit_unchanged "status=$status $(api_json datapusher_status "{\"resource_id\":\"$resource_id\"}" | jq -c '.result.task_info.error // {}')"
    fi
}

check_qsv_version
check_dpp_version
check_file_bin
check_plugins_loaded
check_pages_render
check_datastore_roundtrip

if [ "$FAILURES" -gt 0 ]; then
    echo "$FAILURES check(s) failed"
    exit 1
fi
echo "All checks passed"
