# Historical source drop zone

The empirical pipeline accepts authoritative exports through environment variables or local files. Do not place synthetic scenario data here.

Recommended filenames for a repository/manual validation run:

- `bom_rainfall.csv` — timestamp/date, rainfall amount, optional `beach_id`.
- `waternsw_hydrometric.csv` — timestamp, discharge/flow, turbidity where available, optional `beach_id`.
- `beachwatch.csv` — sample date/time, pilot `beach_id`, water temperature, conductivity, enterococci, turbidity only if the source actually contains it.
- `imos_marine.csv` — timestamp, `beach_id`, SST, upwelling index, optional seasonal acoustic-density percentile.
- `asid_incidents.csv` or `.json` — Taronga ASID / NSW DPI incident export with timestamp, location, species, coordinates and source record fields where available.

The GitHub workflow maps these files into `scripts/ingest_historical.py`. Missing files remain missing; the pipeline does not generate substitute values.
