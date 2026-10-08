# DataPusher+ 3.0 & CKAN 2.11 Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade DataPusher+ from 1.0.4 to 3.0.0 (with a matching qsv), pin every image and extension to an exact version, and remove ckan-docker template leftovers, while staying on CKAN 2.11.

**Architecture:** Everything is wired through `ckan/Dockerfile` (prod), `ckan/Dockerfile.dev` (dev), the `.env*.example` files and `docker-compose*.yml`. This repo has no unit tests, so a host-side smoke script (`scripts/smoke-test.sh`) is the test. It checks installed versions and loaded plugins, renders the key pages, and pushes a CSV round-trip through DP+ into the DataStore. Each task ends with that script passing on a rebuilt dev stack.

**Tech Stack:** CKAN 2.11.6 (`ckan/ckan-base`, `ckan/ckan-dev`, Python 3.10), DataPusher+ 3.0.0, qsv 13.0.0 (`qsvdp`), Solr 9 (`ckan/ckan-solr`), Redis, Docker Compose, bash + curl + jq.

**Issue:** #3. **Spec:** No separate spec. This plan comes from the audit done on 2026-10-08 (see Background).

## Background (decisions already made)

- **Why stay on CKAN 2.11 instead of moving to 2.12.0:** the `ckan-2.12` base image runs **Python 3.14**. DP+ 3.0.0 pins `pandas==2.2.3`, `fiona==1.10.1` and `shapely==2.1.0`, and none of those publish cp314 wheels (the newest are cp313). Moving to 2.12 means compiling them, which needs GDAL headers for fiona. Several of our extensions (basiccharts 2022, visualize 2021, mapviews 2023) are also unmaintained, and 2.12 removes Bootstrap 3 and `ckan.csrf_protection.ignore_extensions`. 2.12 gets its own plan later (see "Out of scope").
- **qsv 13.0.0:** DP+ 3.0.0 requires qsv ≥ 4.0.0 (`MINIMUM_QSV_VERSION`). qsv 13.0.0 came out on the same day as DP+ 3.0.0 (2026-01-06), so it is the version DP+ was most likely tested against. The latest qsv (24.x) is not used.
- **API token:** DP+ 3.0 reads `ckanext.datapusher_plus.api_token` and falls back to `ckan.datapusher.api_token`. We keep the existing `CKAN__DATAPUSHER__API_TOKEN` env var so the server's `.env` does not have to change.
- **Formats:** DP+ reads `ckan.datapusher.formats` **before** `ckanext.datapusher_plus.formats`. That means `CKAN__DATAPUSHER__FORMATS` in `.env` decides which formats are ingested.
- **Patches:** `ckan/patches/00_test_test.patch` is a template placeholder (its content is just `test`). It sits at the top level, so the Dockerfile loop skips it. The mechanism itself stays.

## Global Constraints

- Work on a branch. **A push to `main` deploys to the test server** (`.github/workflows/deploy.yml`).
- Base images: `ckan/ckan-base:2.11.6` and `ckan/ckan-dev:2.11.6`. Do not use `2.12`.
- DP+: `git+https://github.com/dathere/datapusher-plus.git@3.0.0#egg=datapusher-plus`.
- qsv: `https://github.com/dathere/qsv/releases/download/13.0.0/qsv-13.0.0-x86_64-unknown-linux-gnu.zip`. The binary that matters is `/usr/local/bin/qsvdp`.
- Solr image: `ckan/ckan-solr:2.11-solr9-spatial`.
- `ckan/Dockerfile` and `ckan/Dockerfile.dev` must install the same extensions at the same versions.
- No `@master` refs in either Dockerfile after Task 3.

## Review Focus

1. **The `site_packages` volume hides the new image's packages.** Both compose files mount a named volume at `/usr/lib/python3.10/site-packages`. If that path is live, a rebuilt image keeps running DP+ 1.0.4 from the old volume. Pinned by: smoke check `dpp_version` (Task 1) and the site-packages path check in Task 2, Step 4.
2. **The API token is missing or still `CHANGE_ME`.** In that case jobs fail inside the worker and nothing shows in the browser. Expected: the smoke script reports the `datapusher_status` error rather than just "timed out". Pinned in Task 1 (`wait_for_datastore` prints the status on failure).
3. **Resources already ingested by DP+ 1.0.4 get re-pushed under 3.0.** Expected: resubmitting replaces the table and `datastore_search` still works. Pinned in Task 2, Steps 1 and 6 (`SMOKE_KEEP=1` before the upgrade, `datapusher_submit` after it).
4. **DP+ 3.0 loads without ckanext-scheming.** The README lists scheming as a requirement, but only DRUF uses it, and we don't enable DRUF. Expected: CKAN starts and the plugin is listed. Pinned by: smoke check `plugins_loaded` (Task 1).
5. **The `file` binary is missing from the image.** DP+ 3.0 shells out to `/usr/bin/file` (`ckanext.datapusher_plus.file_bin`). Expected: ingestion works. Pinned by: smoke check `file_bin` (Task 1).

---

### Task 1: Smoke test script (baseline on current stack)

**Files:**
- Create: `scripts/smoke-test.sh` (executable)
- Create: `scripts/fixtures/smoke.csv`

**Interfaces:**
- Produces: `scripts/smoke-test.sh`, run from the repo root. Env: `CKAN_API_TOKEN` (required, sysadmin token), `CKAN_URL` (default `http://localhost:5000`), `COMPOSE` (default `./dc.sh`), `SERVICE` (default `ckan-dev`), `SMOKE_KEEP` (when `1`, skip cleanup and print `KEPT_RESOURCE_ID=<id>`), `EXPECT_DPP` (default `3.0.0`), `EXPECT_QSV` (default `13.0.0`). Prints one `PASS <name>` / `FAIL <name>: <detail>` line per check. Exits 0 only if every check passes.

- [ ] **Step 1: Write the fixture** `scripts/fixtures/smoke.csv`:

```csv
id,station,measured_on,salinity_ppt
1,Khulna,2024-01-15,12.5
2,Satkhira,2024-02-20,8.25
3,Bagerhat,2024-03-05,10
```

- [ ] **Step 2: Write `scripts/smoke-test.sh`** (`set -euo pipefail`, curl + jq, a `check <name> <cmd>` helper that records failures and keeps going). Checks, in this order:
  - `qsv_version`: `$COMPOSE exec -T $SERVICE qsvdp --version` starts with `qsvdp $EXPECT_QSV`
  - `dpp_version`: `$COMPOSE exec -T $SERVICE pip show datapusher-plus` has `Version: $EXPECT_DPP`
  - `file_bin`: `$COMPOSE exec -T $SERVICE test -x /usr/bin/file`
  - `plugins_loaded`: every word in the container's `$CKAN__PLUGINS` appears in `GET /api/3/action/status_show` → `.result.extensions`
  - `pages_render`: `/`, `/dataset/`, `/organization/`, `/about` each return HTTP 200
  - `datastore_roundtrip`: create (or reuse) organization `smoke-test-org`, `package_create` `smoke-test-<epoch>`, `resource_create` as a multipart upload of the fixture with `format=CSV`, then `wait_for_datastore <resource_id>`. That function polls `resource_show` → `.result.datastore_active == true` every 5 s for up to 180 s. On timeout it prints `datapusher_status` → `.result` and fails. Then `datastore_search?resource_id=…` must show `total == 3`, the types of `id` and `salinity_ppt` must be `numeric`, the type of `station` must be `text`, and the type of `measured_on` must be `date` or `timestamp`.
  - Cleanup in an EXIT `trap`, unless `SMOKE_KEEP=1`: `dataset_purge` the smoke dataset.

- [ ] **Step 3: Run it against the current (unchanged) dev stack**

Run: `./dc.sh up -d --build && CKAN_API_TOKEN=<token> scripts/smoke-test.sh`
Expected: `FAIL qsv_version` (0.133.1) and `FAIL dpp_version` (1.0.4). Record whether `datastore_roundtrip` passes on 1.0.4; that result is the baseline. If it fails because of the token, follow README § API token first.

- [ ] **Step 4: Commit**

```bash
git add scripts/smoke-test.sh scripts/fixtures/smoke.csv
git commit -m "Add smoke test for plugins, pages and DP+ DataStore ingestion"
```

### Task 2: Upgrade DP+ to 3.0.0 and qsv to 13.0.0; pin CKAN 2.11.6

**Files:**
- Modify: `ckan/Dockerfile` (lines 1, 19-22, 33)
- Modify: `ckan/Dockerfile.dev` (lines 1, 48-51, 61)
- Modify (possibly): `docker-compose.yml`, `docker-compose.dev.yml` (the `site_packages` volume, see Step 4)

**Interfaces:**
- Consumes: `scripts/smoke-test.sh` from Task 1.
- Produces: images with `qsvdp` 13.0.0 and `datapusher-plus` 3.0.0, used by Tasks 3-5.

- [ ] **Step 1: Keep a pre-upgrade resource.** On the stack from Task 1, run `SMOKE_KEEP=1 EXPECT_DPP=1.0.4 EXPECT_QSV=0.133.1 CKAN_API_TOKEN=<token> scripts/smoke-test.sh` and note `KEPT_RESOURCE_ID`.

- [ ] **Step 2: Edit both Dockerfiles.**
  - `FROM ckan/ckan-base:2.11.6` and `FROM ckan/ckan-dev:2.11.6`.
  - Add `ARG QSV_VERSION=13.0.0` and `ARG DPP_VERSION=3.0.0` after `USER root`.
  - Replace the four qsv `RUN` lines with one `RUN` that uses `${QSV_VERSION}`: download, unzip to `/tmp/qsv`, `mv /tmp/qsv/qsv* /usr/local/bin/`, then clean up.
  - Change the DP+ line to `@${DPP_VERSION}`, keeping `&& pip3 install -r ${APP_DIR}/src/datapusher-plus/requirements.txt`.
  - Add `file` to the `apt-get install` list, which also covers Review Focus 5.

- [ ] **Step 3: Rebuild.** `./dc.sh build --no-cache ckan-dev && ./dc.sh up -d`. Expected: the logs show `datapusher_plus db upgrade` with no traceback (`./dc.sh logs ckan-dev | grep -iA5 datapusher_plus`).

- [ ] **Step 4: Remove the `site_packages` volume** (Review Focus 1). First record where Python actually installs packages: `./dc.sh exec ckan-dev python3 -c "import site;print(site.getsitepackages())"`, and put the result in the commit message. Whatever it prints, the volume is either dead or a source of stale packages, so remove it. Delete the `site_packages` volume and its mount from both compose files, run `./dc.sh down && docker volume rm awsis-ckan_site_packages`, then `./dc.sh up -d`.

- [ ] **Step 5: Run the smoke test.** `CKAN_API_TOKEN=<token> scripts/smoke-test.sh`. Expected: every check prints `PASS` and the exit code is 0.

- [ ] **Step 6: Re-push the pre-upgrade resource** (Review Focus 3). `curl -H "Authorization: $CKAN_API_TOKEN" -X POST -H 'Content-Type: application/json' -d '{"resource_id":"<KEPT_RESOURCE_ID>"}' $CKAN_URL/api/3/action/datapusher_submit`. Then poll `datapusher_status` until it reports `complete`, and confirm `datastore_search` returns `total == 3`. Purge that dataset afterwards.

- [ ] **Step 7: Manual Excel check.** In the UI, upload a real AWSIS `.xlsx` file to a scratch dataset. Confirm the DataStore tab shows the rows and the Data Explorer view renders. Then delete the dataset.

- [ ] **Step 8: Commit**

```bash
git add ckan/Dockerfile ckan/Dockerfile.dev docker-compose.yml docker-compose.dev.yml
git commit -m "Upgrade DataPusher+ to 3.0.0 and qsv to 13.0.0; pin CKAN 2.11.6"
```

### Task 3: Pin extensions and supporting images

**Files:**
- Modify: `ckan/Dockerfile` (lines 25-32), `ckan/Dockerfile.dev` (lines 53-60)
- Modify: `.env.example`, `.env.dev.example` (`SOLR_IMAGE_VERSION`, `REDIS_VERSION`, `CKAN_VERSION`)
- Modify: `docker-compose.dev.yml` (pgAdmin image)

**Interfaces:**
- Consumes: the Task 2 images and the smoke script.

- [ ] **Step 1: Pin the extensions** in both Dockerfiles:

| Extension | Pin |
|---|---|
| ckanext-spatial | `@v2.3.2` |
| ckanext-hierarchy | `@v1.2.2` |
| ckanext-geoview | stays `@v0.2.0` (moving to v0.3.2 is out of scope) |
| ckanext-basiccharts | `@dfe2c4f5859c` |
| ckanext-visualize | `@eb53fd00b6a9` |
| ckanext-mapviews | `@caf1d0f6ab41` |
| ckanext-pdfview / ckanext-contact | `ckanext-pdfview==0.0.6 ckanext-contact==2.4.4` |

- [ ] **Step 2: Images and env.** `SOLR_IMAGE_VERSION=2.11-solr9-spatial`, `REDIS_VERSION=7`, `CKAN_VERSION=2.11.6`, pgAdmin `dpage/pgadmin4:9`. Also fix the pgAdmin mount path: it points at `./pgadmin4/servers.json`, but the file lives at `./pgadmin/servers.json`.

- [ ] **Step 3: Rebuild and reindex.** `./dc.sh build ckan-dev && ./dc.sh up -d && ./dc.sh exec ckan-dev ckan search-index rebuild`. Expected: the rebuild finishes without errors.

- [ ] **Step 4: Verify.** `scripts/smoke-test.sh` exits 0. Then do a manual spatial check: the dataset search page map widget renders, and a bbox search returns results.

- [ ] **Step 5: Confirm nothing is left on master.** `grep -n "@master" ckan/Dockerfile ckan/Dockerfile.dev` should output nothing.

- [ ] **Step 6: Commit**

```bash
git add ckan/Dockerfile ckan/Dockerfile.dev .env.example .env.dev.example docker-compose.dev.yml
git commit -m "Pin CKAN extensions, Solr, Redis and pgAdmin versions"
```

### Task 4: Remove template leftovers and document DP+ config

**Files:**
- Delete: `ckan/patches/00_test_test.patch`, `ckan/setup/start_ckan.sh.override`, `ckan/setup/prerun.py.override`
- Create: `ckan/patches/README.md`
- Modify: `.env.example`, `.env.dev.example` (Datapusher block)
- Modify: `README.md` (API token section)

**Interfaces:**
- Consumes: the Task 3 stack and the smoke script.

- [ ] **Step 1: Confirm the files to delete aren't used.** `grep -rnE "prerun\.py\.override|start_ckan\.sh\.override( |$)|00_test_test" ckan docker-compose*.yml` should print nothing. `start_ckan.sh.override.2.11` is in use and stays.

- [ ] **Step 2: Delete the three files** and add `ckan/patches/README.md`. The Dockerfile still needs `COPY patches`, so the folder has to exist. The README states the layout: `patches/<package-dir-under-$SRC_DIR>/<NN>_<name>.patch`, applied with `patch -p1` in `sort -g` order at build time; top-level files are ignored.

- [ ] **Step 3: Rewrite the Datapusher block** in both env examples. Remove `DATAPUSHER_VERSION`, `CKAN_DATAPUSHER_URL` and `CKAN__DATAPUSHER__CALLBACK_URL_BASE`. Keep `CKAN__DATAPUSHER__API_TOKEN` and add a comment that DP+ reads it as a fallback for `ckanext.datapusher_plus.api_token`. Set `CKAN__DATAPUSHER__FORMATS = csv tsv xls xlsx ods zip`, with a comment that this setting takes precedence over `ckanext.datapusher_plus.formats`. Keep `CKAN__RESOURCE_PROXY__MAX_FILE_SIZE`.

- [ ] **Step 4: Update the README** API token section to call it "DataPusher+" and to say the token user must be a sysadmin.

- [ ] **Step 5: Verify.** Copy `.env.dev.example` to `.env`, fill in the token, rebuild, and run `scripts/smoke-test.sh`. It should exit 0. Then upload a `.zip` holding one CSV to a scratch dataset and confirm it ingests (`auto_unzip_one_file` defaults to true).

- [ ] **Step 6: Commit**

```bash
git add -A ckan/patches ckan/setup .env.example .env.dev.example README.md
git commit -m "Remove ckan-docker template leftovers and document DP+ config"
```

### Task 5: Prod image parity check and deploy notes

**Files:**
- Modify: `README.md` (add an "Upgrading" section)

- [ ] **Step 1: Build and start the prod compose locally.** `docker compose -f docker-compose.yml build ckan && docker compose -f docker-compose.yml up -d`. Then run `SERVICE=ckan COMPOSE="docker compose -f docker-compose.yml" CKAN_URL=<traefik url> CKAN_API_TOKEN=<token> scripts/smoke-test.sh`. It should exit 0.

- [ ] **Step 2: Write the "Upgrading" section in the README** as the deploy checklist for the test server:
  1. Back up `pg_data` (`pg_dump` of the CKAN and DataStore DBs).
  2. On the server, update `.env`: `SOLR_IMAGE_VERSION`, `REDIS_VERSION`, `CKAN__DATAPUSHER__FORMATS`.
  3. Remove the `site_packages` volume.
  4. Merge, which triggers the deploy.
  5. Run `ckan search-index rebuild`.
  6. Run the smoke test against the test server.
  7. Resubmit existing resources: `ckan datapusher-plus resubmit --yes`.

- [ ] **Step 3: Commit, then open a PR. Do not push to `main` directly.**

```bash
git add README.md
git commit -m "Document upgrade and deploy checklist"
```

## Out of scope (follow-up plan: CKAN 2.12)

Start this once one of two things is true: DP+ releases with dependency pins that have Python 3.14 wheels, or a 2.12 image appears on an older Python (as of 2026-10-08, only 2.11 has `-py3.10` tags). The follow-up covers:
- Re-test or replace basiccharts, visualize and mapviews against CSRF-required, Bootstrap-3-free 2.12.
- Check `ckanext-awsis` templates against the Midnight Blue / 2.12 template changes.
- Run `ckan db duplicate_emails` before upgrading.
- Use Solr `2.12-solr9-spatial`.
