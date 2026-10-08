# Patches

Patches applied at image build time to CKAN core or to extensions installed
in the image (not to the runtime-mounted ones in `src/`).

Layout: `patches/<dir under $SRC_DIR>/<NN>_<name>.patch`, e.g.
`patches/ckan/01_fix.patch` or `patches/datapusher-plus/01_fix.patch`.
Each folder's patches are applied with `patch -p1` in `sort -g` order.
Files directly in `patches/` are ignored.

Keep each patch tied to an upstream commit or issue, and remove it once the
pinned version includes the fix.

| Patch | Upstream | Remove when |
|---|---|---|
| `datapusher-plus/01_pipeline_none_context_logger.patch` | dathere/datapusher-plus@fb6e6c4 | DP+ release after 3.0.0 is pinned |
