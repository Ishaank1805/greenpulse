"""B2: sample every city with 02_sample_city.py, one city at a time.

Cities run largest first (pop_2025), so partial results cover the important
cities. A city whose output file exists is skipped, so a rerun resumes where
the last one stopped and retries only failures. Every attempt is appended to
data/results/run_log.csv.

Usage:
  python scripts/04_run_all_cities.py               # all cities
  python scripts/04_run_all_cities.py --limit 10    # first 10 not yet done
  python scripts/04_run_all_cities.py Bankura 9386  # named cities / uc_ids
"""
import argparse
import csv
import importlib
import json
import time
from datetime import datetime

import config as C

sampler = importlib.import_module('02_sample_city')

LOG_FILE = C.DATA / 'results' / 'run_log.csv'
LOG_FIELDS = ['time', 'uc_id', 'city', 'status', 'n_rows', 'seconds', 'error']
BACKOFF = (30, 120, 300)  # wait after the 1st, 2nd and 3rd failed attempt
PAUSE = 2                 # seconds between cities; the quota is shared


def log(row):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    new = not LOG_FILE.exists()
    with open(LOG_FILE, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if new:
            w.writeheader()
        w.writerow({'time': datetime.now().isoformat(timespec='seconds'), **row})


def cities(keys):
    with open(C.CITIES_FILE) as f:
        features = json.load(f)['features']
    if keys:
        return [sampler.load_city(k) for k in keys]
    return sorted(features, key=lambda ft: ft['properties']['pop_2025'], reverse=True)


def run_city(feature, stack, grid):
    """Sample one city with retries. Returns (status, seconds)."""
    props = feature['properties']
    base = {'uc_id': props['ID_UC_G0'], 'city': props['name']}
    out = sampler.output_path(feature)
    if out.exists():
        log({**base, 'status': 'skipped', 'n_rows': '', 'seconds': '', 'error': ''})
        return 'skipped', 0.0

    for attempt, wait in enumerate(BACKOFF, start=1):
        t0 = time.time()
        try:
            df = sampler.sample_one(feature, stack, grid)
            # Write to a temp name first, so a crash never leaves a partial
            # file that a rerun would wrongly skip.
            tmp = out.with_suffix('.tmp')
            df.to_csv(tmp, index=False)
            tmp.replace(out)
            secs = time.time() - t0
            log({**base, 'status': 'ok', 'n_rows': len(df), 'seconds': round(secs, 1), 'error': ''})
            return 'ok', secs
        except Exception as e:  # ee.EEException, timeouts, network errors
            secs = time.time() - t0
            msg = f'attempt {attempt}: {type(e).__name__}: {e}'[:500]
            last = attempt == len(BACKOFF)
            log({**base, 'status': 'failed' if last else 'retry', 'n_rows': '',
                 'seconds': round(secs, 1), 'error': msg})
            print(f'  {props["name"]}: {msg}')
            if last:
                return 'failed', secs
            print(f'  waiting {wait} s before retrying')
            time.sleep(wait)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cities', nargs='*', help='names or uc_ids (default: all)')
    ap.add_argument('--limit', type=int, help='stop after this many cities are attempted')
    args = ap.parse_args()

    C.SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    stack, grid = sampler.build_stack()
    todo = cities(args.cities)
    counts, timings, attempted = {'ok': 0, 'failed': 0, 'skipped': 0}, [], 0
    start = time.time()

    for i, feature in enumerate(todo, start=1):
        if args.limit and attempted >= args.limit:
            break
        status, secs = run_city(feature, stack, grid)
        counts[status] += 1
        if status != 'skipped':
            attempted += 1
            timings.append((secs, feature['properties']['name']))
            print(f'[{i}/{len(todo)}] {feature["properties"]["name"]}: {status} '
                  f'({secs:.1f} s, elapsed {(time.time() - start) / 60:.1f} min)', flush=True)
            time.sleep(PAUSE)

    print(f"\nDone in {(time.time() - start) / 60:.1f} min: "
          f"{counts['ok']} ok, {counts['failed']} failed, {counts['skipped']} skipped")
    if timings:
        print('Slowest:', ', '.join(f'{n} {s:.0f} s' for s, n in sorted(timings, reverse=True)[:5]))


if __name__ == '__main__':
    main()
