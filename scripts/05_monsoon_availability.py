"""Role 5 / Task M: monthly MODIS LST data availability for six cities.

For each city and calendar month (2019--2024), compute the fraction of Aqua
MYD11A2 8-day composites whose QC flag passes the *same* rule as
02_sample_city.py.  The 24 monthly day/night fraction bands are reduced with
one reduceRegion call per city, so the complete default run uses six spatial
reductions.

Outputs
-------
data/results/lst_availability_by_month.csv
figures/M_lst_availability.png

Usage
-----
# Full six-city run (the intended final run)
python scripts/05_monsoon_availability.py

# Quota-safe smoke test first
python scripts/05_monsoon_availability.py --cities 5315 9386

# Rebuild the figure from an existing CSV without Earth Engine
python scripts/05_monsoon_availability.py --plot-only
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import date, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

import config as C
from style import apply_style, save

# Role file, Step 2: fixed six-city monsoon check.
DEFAULT_CITY_IDS = [5315, 7963, 9524, 7599, 11352, 9386]
OUT_CSV = C.DATA / "results" / "lst_availability_by_month.csv"


# Keep this logic identical to scripts/02_sample_city.py::bits/lst_mean.
def _bits(img, start: int, end: int):
    """Extract bits start..end (inclusive) from an Earth Engine QA image."""
    width = end - start + 1
    return img.rightShift(start).bitwiseAnd((1 << width) - 1)


def _qc_ok(img, qc_band: str):
    """Binary 1/0 image for the QC rule copied from 02_sample_city.py.

    QC bits 0-1: keep 0 (good), or 1 (other quality) only when bits 6-7 <= 1
    (estimated LST error <= 2 K).  unmask(0) makes a missing QA value count as
    unusable rather than disappearing from the denominator.
    """
    qc = img.select(qc_band)
    qa, err = _bits(qc, 0, 1), _bits(qc, 6, 7)
    return qa.eq(0).Or(qa.eq(1).And(err.lte(1))).unmask(0)


def _monthly_fraction_stack(ee):
    """Return 24 bands: frac_day_01..12 and frac_night_01..12."""
    base = ee.ImageCollection(C.LST_ID).filterDate(C.START, C.END)
    bands = []
    for month in range(1, 13):
        coll = base.filter(ee.Filter.calendarRange(month, month, "month"))
        n_all = coll.size()

        day_ok = coll.map(lambda img: _qc_ok(img, "QC_Day")).sum().divide(n_all)
        night_ok = coll.map(lambda img: _qc_ok(img, "QC_Night")).sum().divide(n_all)
        bands.extend(
            [
                day_ok.rename(f"frac_day_{month:02d}"),
                night_ok.rename(f"frac_night_{month:02d}"),
            ]
        )
    return ee.Image.cat(bands)


def _load_city_features(city_ids: list[int]) -> list[dict]:
    with open(C.CITIES_FILE, encoding="utf-8") as f:
        features = json.load(f)["features"]
    by_id = {int(ft["properties"]["ID_UC_G0"]): ft for ft in features}
    missing = [uc_id for uc_id in city_ids if uc_id not in by_id]
    if missing:
        raise ValueError(f"Unknown uc_id(s): {missing}")
    return [by_id[uc_id] for uc_id in city_ids]


def _getinfo_with_backoff(obj, attempts: int = 4):
    """Back off rather than hammering Earth Engine on quota/transient errors."""
    delays = [20, 40, 80]
    for attempt in range(attempts):
        try:
            return obj.getInfo()
        except Exception as exc:  # EE raises several exception classes here.
            msg = str(exc).lower()
            retryable = any(
                token in msg
                for token in (
                    "429",
                    "too many concurrent aggregations",
                    "quota",
                    "rate",
                    "timeout",
                    "temporarily unavailable",
                    "internal error",
                )
            )
            if not retryable or attempt == attempts - 1:
                raise
            delay = delays[min(attempt, len(delays) - 1)]
            print(f"Earth Engine transient/quota error; retrying in {delay}s: {exc}")
            time.sleep(delay)
    raise RuntimeError("unreachable")


def _run_earth_engine(city_ids: list[int]) -> pd.DataFrame:
    try:
        import ee
    except ImportError as exc:
        raise SystemExit(
            "earthengine-api is not installed. Run: pip install -r requirements.txt"
        ) from exc

    ee.Initialize(project=C.PROJECT)
    features = _load_city_features(city_ids)
    stack = _monthly_fraction_stack(ee)
    # Align the reduction to the native MODIS sinusoidal grid.
    grid = ee.ImageCollection(C.LST_ID).first().select("QC_Day").projection()

    rows: list[dict] = []
    for idx, feature in enumerate(features, start=1):
        props = feature["properties"]
        uc_id = int(props["ID_UC_G0"])
        city = props["name"]
        region = ee.Geometry(feature["geometry"])

        # Exactly one spatial reduction per city: 24 bands in one call.
        reduced = stack.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region,
            scale=1000,
            crs=grid,
            maxPixels=10_000_000,
        )
        values = _getinfo_with_backoff(reduced)

        for month in range(1, 13):
            rows.append(
                {
                    "city": city,
                    "uc_id": uc_id,
                    "month": month,
                    "frac_day_ok": values.get(f"frac_day_{month:02d}"),
                    "frac_night_ok": values.get(f"frac_night_{month:02d}"),
                }
            )
        print(f"[{idx}/{len(features)}] {city}: monthly availability complete")

    return pd.DataFrame(rows)


def _merge_results(new: pd.DataFrame, path: Path = OUT_CSV) -> pd.DataFrame:
    """Replace rows for rerun cities while preserving any already-computed cities."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        old = pd.read_csv(path)
        old = old[~old["uc_id"].isin(new["uc_id"].unique())]
        out = pd.concat([old, new], ignore_index=True)
    else:
        out = new.copy()
    out = out.sort_values(["uc_id", "month"]).reset_index(drop=True)
    out.to_csv(path, index=False)
    return out


def _expected_month_counts() -> dict[int, int]:
    """Count starts of the nominal 8-day MODIS periods in 2019--2024.

    MYD11A2 periods restart at day-of-year 1 each year. This local calculation
    avoids an extra Earth Engine metadata request just for the Jodhpur check.
    """
    counts = {m: 0 for m in range(1, 13)}
    for year in range(2019, 2025):
        d = date(year, 1, 1)
        while d.year == year:
            counts[d.month] += 1
            d += timedelta(days=8)
    return counts


def _run_checks(df: pd.DataFrame) -> None:
    required = {"city", "uc_id", "month", "frac_day_ok", "frac_night_ok"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Availability CSV is missing columns: {sorted(missing)}")

    subset = df[df["uc_id"].isin(DEFAULT_CITY_IDS)].copy()
    if subset.empty:
        return

    bad_range = subset[["frac_day_ok", "frac_night_ok"]].stack().dropna()
    if ((bad_range < 0) | (bad_range > 1)).any():
        raise ValueError("Availability fractions must lie in [0, 1]")

    # Role-file directional check: Jun--Sep should be below Apr--May.
    print("\nMonsoon-vs-pre-monsoon check (day/night means):")
    for uc_id, g in subset.groupby("uc_id"):
        city = g["city"].iloc[0]
        pre = g[g.month.isin([4, 5])][["frac_day_ok", "frac_night_ok"]].mean()
        mon = g[g.month.isin([6, 7, 8, 9])][["frac_day_ok", "frac_night_ok"]].mean()
        status = "PASS" if (mon < pre).all() else "CHECK MASK/DATA"
        print(
            f"  {city:<12} pre={pre.frac_day_ok:.3f}/{pre.frac_night_ok:.3f}  "
            f"monsoon={mon.frac_day_ok:.3f}/{mon.frac_night_ok:.3f}  {status}"
        )

    # Role-file check: Mumbai and Kochi should be the cloudiest of the six in monsoon.
    complete = subset.groupby(["uc_id", "city"], as_index=False).filter(lambda g: set(g.month) >= {6, 7, 8, 9})
    if not complete.empty:
        ranks = (complete[complete.month.isin([6, 7, 8, 9])]
                 .groupby(["uc_id", "city"])["frac_day_ok"].mean().sort_values())
        if len(ranks) >= 2:
            lowest = [city for (_, city) in ranks.index[:2]]
            expected = {"Mumbai", "Kochi"}
            status = "PASS" if set(lowest) == expected else "CHECK MASK/DATA"
            print(f"Lowest monsoon daytime availability: {lowest}  {status}")

    # Independent cross-check requested in the role file: Jodhpur Apr+May should
    # imply a passed-composite count near the pilot median n_day=41.
    j = subset[subset.uc_id == 5315]
    pilot = C.SAMPLES_DIR / "_pilot_v1" / "jodhpur.csv"
    if not j.empty and pilot.exists():
        counts = _expected_month_counts()
        est = 0.0
        for month in (4, 5):
            val = j.loc[j.month == month, "frac_day_ok"]
            if len(val) == 1 and pd.notna(val.iloc[0]):
                est += float(val.iloc[0]) * counts[month]
        pilot_median = pd.read_csv(pilot)["n_day"].median()
        diff = abs(est - pilot_median)
        status = "PASS" if diff <= 2 else "CHECK MASK"
        print(
            f"Jodhpur pilot cross-check: monthly fractions imply ~{est:.1f} "
            f"passing Apr-May composites vs pilot median {pilot_median:.1f} "
            f"(diff {diff:.1f}) {status}"
        )

    # Print the exact Role-5 slide/observation number when Mumbai is available.
    mumbai = subset[subset.uc_id == 7599]
    if set(mumbai.month) >= {4, 5, 6, 7, 8, 9}:
        pre = mumbai[mumbai.month.isin([4, 5])]["frac_day_ok"].mean()
        mon = mumbai[mumbai.month.isin([6, 7, 8, 9])]["frac_day_ok"].mean()
        print(
            "Slide line: In June–September only about "
            f"{100*mon:.0f}% of daytime 8-day composites are usable in Mumbai, "
            f"versus {100*pre:.0f}% in April–May."
        )


def _plot(df: pd.DataFrame) -> Path:
    if df.empty:
        raise ValueError("No availability rows to plot")
    apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharex=True, sharey=True)
    panels = [("frac_day_ok", "Day (~13:30)"), ("frac_night_ok", "Night (~01:30)")]

    for ax, (col, title) in zip(axes, panels):
        for city, g in df.sort_values("month").groupby("city", sort=False):
            ax.plot(g["month"], g[col], marker="o", linewidth=1.7, label=city)
        ax.axvspan(5.5, 9.5, alpha=0.10)
        ax.set_title(title)
        ax.set_xlabel("Calendar month")
        ax.set_xticks(range(1, 13))
        ax.set_ylim(0, 1.02)
    axes[0].set_ylabel("Fraction of usable 8-day composites")
    axes[1].legend(fontsize=8, ncol=2)
    fig.suptitle("MODIS LST availability falls during the monsoon (2019–2024)")
    fig.tight_layout()
    out = save(fig, "M_lst_availability")
    plt.close(fig)
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cities",
        nargs="+",
        type=int,
        default=DEFAULT_CITY_IDS,
        help="uc_id values to run (default: the six Role-5 cities)",
    )
    parser.add_argument(
        "--plot-only",
        action="store_true",
        help="skip Earth Engine and rebuild the figure/checks from the existing CSV",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.plot_only:
        if not OUT_CSV.exists():
            raise SystemExit(f"Missing {OUT_CSV.relative_to(C.ROOT)}")
        df = pd.read_csv(OUT_CSV)
    else:
        new = _run_earth_engine(args.cities)
        df = _merge_results(new)
        print(f"Wrote {OUT_CSV.relative_to(C.ROOT)}")

    _run_checks(df)
    out = _plot(df[df.uc_id.isin(DEFAULT_CITY_IDS)])
    print(f"Wrote {out.relative_to(C.ROOT)}")


if __name__ == "__main__":
    main()
