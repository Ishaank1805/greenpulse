"""Final phase, task 4 (gate G-H): add a `height` column to every sample file.

height = GHSL 2018 mean building height (m) in the 1 km MODIS square, weighted by
built-up surface so empty 100 m cells do not dilute tall blocks:
    height_1km = mean(built_height x built_surface) / mean(built_surface)
Both means use reduceResolution(mean) onto the same 1 km grid as 02_sample_city.py.
built_surface is GHSL 2020 (the samples' `built`); height exists only for 2018, the
closest epoch available. Where the weight is 0 (no buildings) height is NaN.

The samples are validated and committed, so only the new layer is sampled (one
sample() call per city) and joined on cell_id. The column is appended to each line
as text, so every existing byte of the file is unchanged; the old columns are
re-read and compared before the original is replaced. A file that already has
`height` is skipped, so reruns resume. Every attempt goes to
data/results/height_log.csv.

Usage:
  python scripts/04e_add_height.py                    # Jodhpur and Kochi (test first)
  python scripts/04e_add_height.py Mumbai 7963        # named cities / uc_ids
  python scripts/04e_add_height.py --all [--limit N]  # every city, largest first
  python scripts/04e_add_height.py --check            # G-H checks, no Earth Engine
"""
import argparse
import csv
import importlib
import json
import math
import subprocess
import time
from datetime import datetime

import numpy as np
import pandas as pd

import config as C

LOG_FILE = C.DATA / 'results' / 'height_log.csv'
LOG_FIELDS = ['time', 'uc_id', 'city', 'status', 'n_cells', 'n_height', 'n_unmatched',
              'seconds', 'error']
ATTEMPTS = 3
WAITS = (30, 120)   # seconds after the 1st and 2nd failed attempt
PAUSE = 2           # seconds between cities; the quota is shared
SAMPLE_COLS = ['city', 'uc_id', 'season', 'cell_id', 'lon', 'lat', 'lst_day', 'lst_night',
               'n_day', 'n_night', 'ndvi', 'evi', 'built', 'pop', 'elev']
PILOT_N = {5315: 254, 9386: 1238}   # data rows in _pilot_v1 (role 1, B1 check)
PILOT_V1 = {5315: 'jodhpur', 9386: 'kochi'}


# --------------------------------------------------------------------------- Earth Engine
def height_image(ee, grid):
    """Built-surface-weighted mean building height on the 1 km MODIS grid."""
    h = ee.Image(C.HEIGHT_ID).select('built_height')
    s = ee.Image(C.BUILT_ID).select('built_surface')
    s = s.updateMask(h.mask())   # numerator and denominator over the same 100 m cells

    def to_grid(img):
        return img.reduceResolution(ee.Reducer.mean(), maxPixels=1024).reproject(grid)

    num, den = to_grid(h.multiply(s)), to_grid(s)
    return num.divide(den).updateMask(den.gt(0)).rename('height')


def sample_height(ee, feature, img, grid):
    """{cell_id: height or NaN} for every 1 km square in the city outline."""
    fc = img.sample(region=ee.Geometry(feature['geometry']), projection=grid,
                    scale=grid.nominalScale(), geometries=True, dropNulls=False)
    out = {}
    for ft in fc.getInfo()['features']:
        lon, lat = ft['geometry']['coordinates']
        out[f'{lon:.5f}_{lat:.5f}'] = ft['properties'].get('height', math.nan)
    return out


# --------------------------------------------------------------------------- file update
def fmt(v):
    """pandas-style CSV value: shortest round-trip float, empty for NaN."""
    return '' if v is None or (isinstance(v, float) and math.isnan(v)) else repr(float(v))


def add_column(path, heights):
    """Append `height` to every line of one sample file. Returns (n_cells, n_height)."""
    old = pd.read_csv(path)
    unmatched = set(old.cell_id) - set(heights)
    if unmatched:
        raise ValueError(f'{len(unmatched)} cells not on the height grid, e.g. {sorted(unmatched)[:3]}')

    lines = path.read_text().splitlines(keepends=True)
    if len(lines) != len(old) + 1:
        raise ValueError(f'{len(lines)} lines for {len(old)} rows; cannot append safely')
    vals = ['height'] + [fmt(heights[c]) for c in old.cell_id]
    new = []
    for line, v in zip(lines, vals):
        body = line.rstrip('\r\n')
        new.append(f'{body},{v}{line[len(body):]}')

    tmp = path.with_suffix('.tmp')
    tmp.write_text(''.join(new))
    back = pd.read_csv(tmp)
    if list(back.columns) != list(old.columns) + ['height']:
        tmp.unlink()
        raise ValueError(f'unexpected columns after append: {list(back.columns)}')
    pd.testing.assert_frame_equal(back[old.columns], old)   # no old value changed
    tmp.replace(path)
    return len(old.cell_id.unique()), int(back.drop_duplicates('cell_id').height.notna().sum())


def log(row):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    new = not LOG_FILE.exists()
    with open(LOG_FILE, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if new:
            w.writeheader()
        w.writerow({'time': datetime.now().isoformat(timespec='seconds'), **row})


def run_city(ee, sampler, feature, img, grid):
    props = feature['properties']
    base = {'uc_id': props['ID_UC_G0'], 'city': props['name']}
    path = sampler.output_path(feature)
    if not path.exists():
        log({**base, 'status': 'failed', 'error': f'no sample file {path.name}'})
        return 'failed', 0.0
    if 'height' in path.open().readline().rstrip('\r\n').split(','):
        return 'skipped', 0.0

    for attempt in range(1, ATTEMPTS + 1):
        t0 = time.time()
        try:
            heights = sample_height(ee, feature, img, grid)
            n_cells, n_height = add_column(path, heights)
            secs = time.time() - t0
            log({**base, 'status': 'ok', 'n_cells': n_cells, 'n_height': n_height,
                 'n_unmatched': 0, 'seconds': round(secs, 1)})
            return 'ok', secs
        except Exception as e:  # ee.EEException, timeouts, network, failed checks
            secs = time.time() - t0
            msg = f'attempt {attempt}: {type(e).__name__}: {e}'[:500]
            last = attempt == ATTEMPTS
            log({**base, 'status': 'failed' if last else 'retry', 'seconds': round(secs, 1),
                 'error': msg})
            print(f'  {props["name"]}: {msg}')
            if last:
                return 'failed', secs
            print(f'  waiting {WAITS[attempt - 1]} s before retrying')
            time.sleep(WAITS[attempt - 1])


def sample_main(args):
    import ee
    sampler = importlib.import_module('02_sample_city')   # also runs ee.Initialize
    grid = ee.ImageCollection(C.LST_ID).first().select('LST_Day_1km').projection()  # as in 02
    img = height_image(ee, grid)

    if args.all:
        with open(C.CITIES_FILE) as f:
            todo = sorted(json.load(f)['features'], key=lambda ft: -ft['properties']['pop_2025'])
    else:
        todo = [sampler.load_city(k) for k in (args.cities or ['Jodhpur', 'Kochi'])]

    counts, timings, attempted, start = {'ok': 0, 'failed': 0, 'skipped': 0}, [], 0, time.time()
    for i, ft in enumerate(todo, 1):
        if args.limit and attempted >= args.limit:
            break
        status, secs = run_city(ee, sampler, ft, img, grid)
        counts[status] += 1
        if status != 'skipped':
            attempted += 1
            timings.append((secs, ft['properties']['name']))
            print(f'[{i}/{len(todo)}] {ft["properties"]["name"]}: {status} ({secs:.1f} s, '
                  f'elapsed {(time.time() - start) / 60:.1f} min)', flush=True)
            time.sleep(PAUSE)
    print(f"\nDone in {(time.time() - start) / 60:.1f} min: {counts['ok']} ok, "
          f"{counts['failed']} failed, {counts['skipped']} skipped")
    if timings:
        print('Slowest:', ', '.join(f'{n} {s:.0f} s' for s, n in sorted(timings, reverse=True)[:5]))


# --------------------------------------------------------------------------- checks (G-H)
def git_head(path):
    """The committed version of a file, or None."""
    r = subprocess.run(['git', 'show', f'HEAD:{path.relative_to(C.ROOT).as_posix()}'],
                       cwd=C.ROOT, capture_output=True)
    return r.stdout.decode() if r.returncode == 0 else None


def check_main():
    paths = sorted(C.SAMPLES_DIR.glob('*.csv'))
    ok, done, frames = True, [], []
    changed, header_bad = [], []
    for p in paths:
        text = p.read_text()
        header = text.split('\n', 1)[0].rstrip('\r').split(',')
        if 'height' not in header:
            continue
        done.append(p)
        if header != SAMPLE_COLS + ['height']:
            header_bad.append(p.name)
        # No old byte changed: dropping the last field gives back the committed file.
        head = git_head(p)
        if head is not None and 'height' not in head.split('\n', 1)[0]:
            stripped = ''.join(l[:l.rstrip('\r\n').rfind(',')] + l[len(l.rstrip('\r\n')):]
                               for l in text.splitlines(keepends=True))
            if stripped != head:
                changed.append(p.name)
        frames.append(pd.read_csv(p))

    print(f'Files with height: {len(done)} of {len(paths)}')
    ok &= len(done) == len(paths) == 303
    print(f'  header = README 3.1 columns + height: {"ok" if not header_bad else f"NO {header_bad}"}')
    print(f'  old columns byte-identical to git HEAD: {"ok" if not changed else f"NO {changed}"}')
    ok &= not header_bad and not changed
    if not frames:
        print('No files with height yet.')
        return False
    s = pd.concat(frames, ignore_index=True)

    cells = s.drop_duplicates(['uc_id', 'cell_id'])
    print(f'  height same in every season: '
          f'{"ok" if s.groupby(["uc_id", "cell_id"]).height.nunique(dropna=False).max() == 1 else "NO"}')
    urban = cells[cells.built >= 0.10]
    h = urban.height.dropna()
    print(f'  urban squares (built >= 0.10): {len(urban)}, height NaN in {urban.height.isna().sum()} '
          f'(expect ~0)')
    print(f'  NaN height where built > 0: {int((cells.built > 0).sum() - cells[cells.built > 0].height.notna().sum())}; '
          f'where built == 0: {int(cells[cells.built == 0].height.isna().sum())} of {int((cells.built == 0).sum())}')
    print(f'  urban height: median {h.median():.1f} m, 3-30 m in {h.between(3, 30).mean():.0%}, '
          f'max {h.max():.1f} m (expect <= 100)')
    ok &= urban.height.isna().sum() <= 0.01 * len(urban) and h.max() <= 100

    med = urban.groupby('uc_id').height.median()
    if {7599, 7963, 5315} <= set(med.index):
        good = med[7599] > med[5315] and med[7963] > med[5315]
        ok &= good
        print(f'  median urban height Mumbai {med[7599]:.1f} m, New Delhi {med[7963]:.1f} m > '
              f'Jodhpur {med[5315]:.1f} m: {"ok" if good else "NO"}')
    top = med.sort_values(ascending=False).head(5)
    names = cells.drop_duplicates('uc_id').set_index('uc_id').city
    print('  tallest median urban height:', ', '.join(f'{names[u]} {v:.1f} m' for u, v in top.items()))

    # B1 check rerun: pre rows still reproduce the v1 pilot exactly.
    for uc, name in PILOT_V1.items():
        new = s[(s.uc_id == uc) & (s.season == 'pre')]
        if new.empty:
            continue
        v1 = pd.read_csv(C.SAMPLES_DIR / '_pilot_v1' / f'{name}.csv')
        v1['cell_id'] = [f'{lon:.5f}_{lat:.5f}' for lon, lat in zip(v1.lon, v1.lat)]
        j = v1.merge(new, on='cell_id', suffixes=('_v1', ''))
        diff = max(np.nanmax(np.abs(j[f'{c}_v1'] - j[c]).to_numpy())
                   for c in ('lst_day', 'lst_night', 'ndvi', 'evi', 'built', 'pop'))
        good = len(j) == len(v1) == PILOT_N[uc] and diff < 1e-6
        ok &= good
        print(f'  pilot {name}: {len(j)}/{PILOT_N[uc]} rows match, max abs diff {diff:.1e}: '
              f'{"ok" if good else "NO"}')

    if LOG_FILE.exists():
        lg = pd.read_csv(LOG_FILE)
        last = lg.groupby('uc_id').tail(1)
        print(f'  height_log: {last.status.value_counts().to_dict()}')
    print('G-H CHECKS PASSED' if ok else 'G-H NOT READY (see above)')
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cities', nargs='*', help='names or uc_ids (default: Jodhpur Kochi)')
    ap.add_argument('--all', action='store_true', help='every city, largest first')
    ap.add_argument('--limit', type=int, help='stop after this many cities are attempted')
    ap.add_argument('--check', action='store_true', help='run the G-H checks only (no Earth Engine)')
    args = ap.parse_args()
    if args.check:
        raise SystemExit(0 if check_main() else 1)
    sample_main(args)


if __name__ == '__main__':
    main()
