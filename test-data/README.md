# test-data

Sample fixtures used by the automated test suite (`tests/`) and for manual smoke-testing.

- `sample_fixtures.json` — representative asset/alarm/ticket records mirroring the seed
  data in `alarm-api/main.py` and `mcp-servers/ticketing/server.py`. Used by
  `tests/integration/` to assert response shapes without depending on live seed data drifting.

These are synthetic, non-sensitive records safe to commit.
