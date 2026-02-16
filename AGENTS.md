# Repository Guidelines

## Project Structure & Module Organization
`src/` contains the MicroPython runtime deployed to the Pico. `src/main.py` is the entrypoint; supporting modules handle sampling, dip detection, logging, storage, and stats.  
`tools/` contains host-side Python utilities (serial monitoring, CSV download/validation, plotting, simulation).  
`docs/` contains setup, wiring, architecture, and troubleshooting guides.  
`examples/` includes sample CSV files for quick checks.  
`data/` is for local outputs. Do not commit generated data files (`*.csv`, `*.log`, `*.txt` are ignored).

## Build, Test, and Development Commands
There is no package build step; development is script-based.

```powershell
pip install -r requirements.txt
python tools/live_monitor.py --port COM9
python tools/download_from_pico.py --port COM9 --output ./data
python tools/simulate_dips.py --duration 60 --dips 10
python tools/validate_csv.py data/pico_dips.csv
```

- `pip install -r requirements.txt`: installs PC-side dependencies.
- `live_monitor.py`: reads Pico serial stream, optionally writes to InfluxDB.
- `download_from_pico.py`: pulls CSV logs from device flash.
- `simulate_dips.py`: generates synthetic dips to test logic without hardware.
- `validate_csv.py`: validates output file integrity and data quality.

For firmware runs, copy `src/*.py` to the Pico (Thonny recommended) and run `main.py`.

## Coding Style & Naming Conventions
Use Python with 4-space indentation and follow existing naming:
- `snake_case` for files, functions, and variables.
- `UPPER_CASE` for config constants (see `src/config.py`).
- Small, single-purpose modules (match current `src/` organization).

Keep changes MicroPython-compatible in `src/` (avoid desktop-only libraries there). No formatter/linter is enforced in-repo, so match surrounding style exactly.

## Testing Guidelines
This repository currently relies on functional/manual testing instead of a full pytest suite.
- On-device debug checks: run `src/test_breakpoints.py` on Pico (`run_all_tests()`).
- Logic checks without hardware: `python tools/simulate_dips.py ...`.
- Data quality checks: `python tools/validate_csv.py <file>`.

When modifying detection or logging logic, test at least one real or simulated dip flow and include the commands used in your PR.

## Commit & Pull Request Guidelines
Recent history uses short, imperative messages, with some Conventional Commit prefixes (`feat:`, `docs:`). Prefer:
- `feat: ...`, `fix: ...`, `docs: ...`, `chore: ...`
- One focused change per commit.

PRs should include:
- Clear summary of behavior changes.
- Test evidence (exact commands run).
- Hardware/runtime context (Pico model, logging mode, serial setup).
- Screenshots only when changing dashboards/plots.
