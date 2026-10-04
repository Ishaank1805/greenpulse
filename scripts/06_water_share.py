"""Role 5 / Task G: OpenStreetMap water share for each sampled MODIS square.

The script downloads water polygons for each city's GHS-UCDB outline with
OSMnx/Overpass, projects them to the native MODIS sinusoidal CRS, and computes
the fraction of each 926.625 m MODIS square covered by mapped water.

Outputs
-------
data/water/{uc_id}_{slug}.csv              uc_id, cell_id, water_frac
raw/osm/{uc_id}.gpkg                       regenerable OSM cache (git-ignored)
figures/G_water_effect.png                  after Role 3 produces water-control slopes

Usage
-----
# Pilot first (default):
python scripts/06_water_share.py

# Specific cities by name or uc_id:
python scripts/06_water_share.py Jodhpur Kochi
python scripts/06_water_share.py 5315 9386

# Process every currently sampled city, skipping finished water files:
python scripts/06_water_share.py --all

# Run role checks once water files exist:
python scripts/06_water_share.py --check

# Build water-effect figure after Role 3 reruns script 03:
python scripts/06_water_share.py --effect
"""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely.geometry import box
from shapely.ops import unary_union

import config as C
from style import CE_LABEL, apply_style, save

MODIS_SINU = "+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +R=6371007.181 +units=m +no_defs"
MODIS_PIXEL_M = 926.625
MODIS_HALF_PIXEL_M = MODIS_PIXEL_M / 2
TAGS = {
    "natural": ["water", "wetland"],
    "water": True,
    "waterway": ["riverbank", "dock"],
    "landuse": ["reservoir", "basin"],
}
WATER_DIR = C.DATA / "water"
RAW_OSM_DIR = C.RAW / "osm"
COOLING_CSV = C.DATA / "results" / "cooling_efficiency.csv"


def _city_table() -> gpd.GeoDataFrame:
    cities = gpd.read_file(C.CITIES_FILE)
    if cities.crs is None:
        cities = cities.set_crs("EPSG:4326")
    else:
        cities = cities.to_crs("EPSG:4326")
    return cities


def _slug(name: str) -> str:
    return name.lower().replace(" ", "_")


def _resolve_cities(keys: list[str], all_cities: bool) -> gpd.GeoDataFrame:
    cities = _city_table()
    sample_ids = {
        int(p.name.split("_", 1)[0]) for p in C.SAMPLES_DIR.glob("*.csv") if p.name[0].isdigit()
    }
    cities = cities[cities["ID_UC_G0"].astype(int).isin(sample_ids)].copy()
    if all_cities:
        return cities.sort_values("ID_UC_G0")

    if not keys:
        keys = ["Jodhpur", "Kochi"]
    wanted = []
    for key in keys:
        if str(key).isdigit():
            match = cities[cities["ID_UC_G0"].astype(int) == int(key)]
        else:
            match = cities[cities["name"].str.casefold() == str(key).casefold()]
        if len(match) != 1:
            raise ValueError(f"Expected one sampled city for {key!r}, found {len(match)}")
        wanted.append(match.index[0])
    return cities.loc[wanted].copy()


def _sample_path(uc_id: int) -> Path:
    matches = list(C.SAMPLES_DIR.glob(f"{uc_id}_*.csv"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one sample CSV for uc_id={uc_id}, found {len(matches)}")
    return matches[0]


def _water_path(uc_id: int, name: str) -> Path:
    return WATER_DIR / f"{uc_id}_{_slug(name)}.csv"


def _polygon_parts(geom):
    """Yield polygonal pieces only, discarding points/lines from intersections."""
    if geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [geom]
    if geom.geom_type == "MultiPolygon":
        return list(geom.geoms)
    if geom.geom_type == "GeometryCollection":
        out = []
        for part in geom.geoms:
            out.extend(_polygon_parts(part))
        return out
    return []


def _quadrants(city_geom):
    minx, miny, maxx, maxy = city_geom.bounds
    midx, midy = (minx + maxx) / 2, (miny + maxy) / 2
    boxes = [
        box(minx, miny, midx, midy),
        box(midx, miny, maxx, midy),
        box(minx, midy, midx, maxy),
        box(midx, midy, maxx, maxy),
    ]
    pieces = []
    for q in boxes:
        pieces.extend(_polygon_parts(city_geom.intersection(q)))
    return [p for p in pieces if not p.is_empty and p.area > 0]


def _configure_osmnx(ox, timeout: int, overpass_url: str | None = None) -> None:
    # Role-file default is 300 s. CLI can lower this for recovery runs when a
    # public Overpass instance is overloaded. requests_timeout is OSMnx 2.x.
    if hasattr(ox.settings, "timeout"):
        ox.settings.timeout = timeout
    if hasattr(ox.settings, "requests_timeout"):
        ox.settings.requests_timeout = timeout
    if overpass_url and hasattr(ox.settings, "overpass_url"):
        ox.settings.overpass_url = overpass_url.rstrip("/")
    ox.settings.use_cache = True
    if hasattr(ox.settings, "cache_folder"):
        ox.settings.cache_folder = str(C.ROOT / "cache")


def _exc_text(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}".lower()


def _is_no_features(exc: Exception) -> bool:
    return "no matching features" in _exc_text(exc)


def _is_connect_timeout(exc: Exception) -> bool:
    msg = _exc_text(exc)
    return any(
        token in msg
        for token in (
            "connecttimeouterror",
            "failed to establish a new connection",
            "connection timed out",
        )
    )


def _is_query_timeout(exc: Exception) -> bool:
    msg = _exc_text(exc)
    if _is_connect_timeout(exc):
        return False
    return any(token in msg for token in ("readtimeout", "timed out", "timeout", "504", "gateway timeout"))


def _download_osm(
    city_geom,
    uc_id: int,
    timeout: int = 300,
    overpass_url: str | None = None,
) -> gpd.GeoDataFrame:
    """Download mapped inland-water polygons.

    Empty OSM results are valid and become zero water share. Connection
    failures are not split into quadrants because geometry splitting cannot
    fix an unreachable endpoint. Query timeouts/504s still use the required
    four-quadrant fallback.
    """
    raw_path = RAW_OSM_DIR / f"{uc_id}.gpkg"
    if raw_path.exists():
        cached = gpd.read_file(raw_path)
        if cached.crs is None:
            cached = cached.set_crs("EPSG:4326")
        return cached.to_crs("EPSG:4326")

    try:
        import osmnx as ox
    except ImportError as exc:
        raise SystemExit("osmnx is not installed. Run: pip install -r requirements.txt") from exc

    _configure_osmnx(ox, timeout=timeout, overpass_url=overpass_url)

    try:
        gdf = ox.features_from_polygon(city_geom, TAGS)
    except Exception as exc:
        if _is_no_features(exc):
            gdf = gpd.GeoDataFrame({"geometry": []}, geometry="geometry", crs="EPSG:4326")
        elif _is_connect_timeout(exc):
            raise RuntimeError(
                f"Overpass connection failed for uc_id={uc_id}; "
                "retry later or use a different Overpass endpoint"
            ) from exc
        elif _is_query_timeout(exc):
            print(f"Overpass query timed out for {uc_id}; retrying as four city quadrants")
            parts = []
            for idx, geom in enumerate(_quadrants(city_geom), start=1):
                try:
                    part = ox.features_from_polygon(geom, TAGS)
                except Exception as part_exc:
                    if _is_no_features(part_exc):
                        continue
                    raise RuntimeError(
                        f"Overpass failed for uc_id={uc_id}, quadrant {idx}: {part_exc}"
                    ) from part_exc
                if not part.empty:
                    parts.append(part)
                time.sleep(1)
            if parts:
                gdf = gpd.GeoDataFrame(pd.concat(parts), crs="EPSG:4326")
            else:
                gdf = gpd.GeoDataFrame({"geometry": []}, geometry="geometry", crs="EPSG:4326")
        else:
            raise

    if gdf.empty:
        water = gpd.GeoDataFrame({"geometry": []}, geometry="geometry", crs="EPSG:4326")
    else:
        gdf = gdf.to_crs("EPSG:4326")
        water = gdf[gdf.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
        water = water[~water.geometry.is_empty & water.geometry.notna()].copy()
        if hasattr(water.geometry, "make_valid"):
            water.geometry = water.geometry.make_valid()
        else:
            water.geometry = water.geometry.buffer(0)
        water = water[water.geom_type.isin(["Polygon", "MultiPolygon"])].copy()

    RAW_OSM_DIR.mkdir(parents=True, exist_ok=True)
    if not water.empty:
        raw = water.reset_index()
        for col in raw.columns:
            if col == raw.geometry.name:
                continue
            if raw[col].dtype == "object":
                raw[col] = raw[col].map(
                    lambda v: json.dumps(v, sort_keys=True)
                    if isinstance(v, (list, tuple, dict, set))
                    else v
                )
        raw.to_file(raw_path, driver="GPKG")

    return water[["geometry"]]


def _sample_cells(uc_id: int) -> tuple[pd.DataFrame, gpd.GeoDataFrame]:
    sample_path = _sample_path(uc_id)
    df = pd.read_csv(sample_path)
    required = {"uc_id", "season", "cell_id", "lon", "lat"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{sample_path.name} missing columns {sorted(missing)}")
    pre = (
        df[df["season"] == "pre"][["uc_id", "cell_id", "lon", "lat"]]
        .drop_duplicates("cell_id")
        .copy()
    )
    if pre.empty:
        raise ValueError(f"{sample_path.name} has no pre-monsoon rows")
    if pre["cell_id"].duplicated().any():
        raise ValueError(f"Duplicate cell_id in {sample_path.name}")
    points = gpd.GeoDataFrame(
        pre[["uc_id", "cell_id"]].copy(),
        geometry=gpd.points_from_xy(pre["lon"], pre["lat"]),
        crs="EPSG:4326",
    ).to_crs(MODIS_SINU)
    return pre, points


def _compute_water_share(uc_id: int, water_ll: gpd.GeoDataFrame) -> pd.DataFrame:
    pre, points = _sample_cells(uc_id)
    squares = points.copy()
    squares.geometry = [
        box(
            pt.x - MODIS_HALF_PIXEL_M,
            pt.y - MODIS_HALF_PIXEL_M,
            pt.x + MODIS_HALF_PIXEL_M,
            pt.y + MODIS_HALF_PIXEL_M,
        )
        for pt in points.geometry
    ]

    if water_ll.empty:
        frac = np.zeros(len(squares), dtype=float)
    else:
        water = water_ll.to_crs(MODIS_SINU)
        water = water[~water.geometry.is_empty & water.geometry.notna()]
        if water.empty:
            frac = np.zeros(len(squares), dtype=float)
        else:
            # Dissolve first, so overlapping OSM polygons are not double counted.
            water_union = unary_union(list(water.geometry))
            inter_area = squares.geometry.intersection(water_union).area.to_numpy()
            square_area = MODIS_PIXEL_M * MODIS_PIXEL_M
            frac = np.clip(inter_area / square_area, 0.0, 1.0)

    out = pd.DataFrame(
        {
            "uc_id": pre["uc_id"].astype(int).to_numpy(),
            "cell_id": pre["cell_id"].astype(str).to_numpy(),
            "water_frac": frac,
        }
    )
    if len(out) != len(pre) or out["cell_id"].duplicated().any():
        raise RuntimeError("Water output does not have exactly one row per sample cell")
    return out


def _process_city(
    row,
    overwrite: bool = False,
    timeout: int = 300,
    overpass_url: str | None = None,
) -> Path:
    uc_id = int(row["ID_UC_G0"])
    city = str(row["name"])
    out_path = _water_path(uc_id, city)
    if out_path.exists() and not overwrite:
        print(f"SKIP {city}: {out_path.relative_to(C.ROOT)} already exists")
        return out_path

    water = _download_osm(
        row.geometry, uc_id, timeout=timeout, overpass_url=overpass_url
    )
    result = _compute_water_share(uc_id, water)
    WATER_DIR.mkdir(parents=True, exist_ok=True)
    result.to_csv(out_path, index=False)
    n_any = int((result.water_frac > 0).sum())
    n_major = int((result.water_frac > 0.5).sum())
    print(
        f"OK   {city}: {len(result)} cells, {n_any} with any mapped water, "
        f"{n_major} >50% -> {out_path.relative_to(C.ROOT)}"
    )
    return out_path


def _run_water_checks() -> None:
    """Role-file checks that can be evaluated once pilot/all-city water CSVs exist."""
    print("\nRole 5 water checks")
    summaries = []
    for uc_id, city in [(9386, "Kochi"), (5315, "Jodhpur")]:
        sample = _sample_path(uc_id)
        water_path = _water_path(uc_id, city)
        if not water_path.exists():
            print(f"  {city}: PENDING (missing {water_path.relative_to(C.ROOT)})")
            continue
        s = pd.read_csv(sample)
        s = s[s.season == "pre"].copy()
        w = pd.read_csv(water_path)
        d = s.merge(w, on=["uc_id", "cell_id"], how="left", validate="one_to_one")
        if d.water_frac.isna().any():
            raise ValueError(f"{city}: water file does not cover every pre-season cell")

        if city == "Kochi":
            no_lst = d["lst_day"].isna()
            n_no_lst = int(no_lst.sum())
            n_major = int((no_lst & (d.water_frac > 0.5)).sum())
            pct = 100 * n_major / n_no_lst if n_no_lst else math.nan
            wet_with_lst = d[(d.water_frac > 0.5) & d.lst_day.notna()]
            ndvi_median = wet_with_lst.ndvi.median()
            coastal_gap = int(((d.built >= 0.10) & d.lst_day.isna() & (d.water_frac <= 0.05)).sum())
            print(
                f"  Kochi open-water check: {n_major}/{n_no_lst} missing-LST cells "
                f"({pct:.1f}%) have water_frac > 0.5"
            )
            ndvi_state = "PASS" if pd.notna(ndvi_median) and ndvi_median < 0.2 else "WARN"
            print(
                f"  Kochi low-NDVI check: median pre NDVI={ndvi_median:.3f} among "
                f"{len(wet_with_lst)} cells with water_frac > 0.5 and valid LST  {ndvi_state}"
            )
            print(
                f"  Kochi sea-gap proxy: {coastal_gap} built>=0.10, missing-LST cells "
                f"have mapped water_frac <= 0.05"
            )
            summaries.append(("kochi_sea_gap", coastal_gap))
        else:
            n_any = int((d.water_frac > 0).sum())
            n_1pct = int((d.water_frac >= 0.01).sum())
            max_frac = float(d.water_frac.max())
            print(
                f"  Jodhpur dry-city check: {n_any}/{len(d)} cells have any mapped water; "
                f"{n_1pct} have >=1%; max={max_frac:.3f}"
            )
    # Across every processed city, count the known sea-gap proxy: urban cells with
    # no LST but almost no mapped OSM polygon water. Coastal sea is a coastline
    # line in OSM, so it contributes ~0 to water_frac. This count is deliberately
    # reported as a proxy/limitation rather than claiming every such cell is sea.
    sea_gap_total = 0
    sea_gap_cities = 0
    for water_path in sorted(WATER_DIR.glob("*.csv")):
        try:
            uc_id = int(water_path.name.split("_", 1)[0])
            sample_path = _sample_path(uc_id)
            s = pd.read_csv(sample_path)
            s = s[s.season == "pre"]
            w = pd.read_csv(water_path)
            d = s.merge(w, on=["uc_id", "cell_id"], how="left", validate="one_to_one")
            n = int(((d.built >= 0.10) & d.lst_day.isna() & (d.water_frac <= 0.05)).sum())
            if n:
                sea_gap_total += n
                sea_gap_cities += 1
        except Exception as exc:
            print(f"  Sea-gap check skipped {water_path.name}: {exc}")
    if list(WATER_DIR.glob("*.csv")):
        print(
            f"  Sea-gap proxy across processed cities: {sea_gap_total} built>=0.10, "
            f"missing-LST cells have water_frac<=0.05 ({sea_gap_cities} cities)"
        )
        summaries.append(("sea_gap_proxy_all", sea_gap_total))

    return summaries


def _main_spec_rows_for_effect(ce: pd.DataFrame) -> pd.DataFrame:
    required = {
        "city",
        "uc_id",
        "season",
        "time",
        "index",
        "built_min",
        "control",
        "ce_per_0.1",
    }
    missing = required - set(ce.columns)
    if missing:
        raise ValueError(f"cooling_efficiency.csv missing columns: {sorted(missing)}")
    built_num = pd.to_numeric(ce["built_min"], errors="coerce")
    return ce[
        (ce["season"] == "pre")
        & (ce["index"] == "ndvi")
        & np.isclose(built_num, 0.10, equal_nan=False)
        & ce["control"].isin(["built_elev", "built_elev_water"])
    ].copy()


def _water_effect_data(ce: pd.DataFrame) -> pd.DataFrame:
    d = _main_spec_rows_for_effect(ce)
    pivot = d.pivot_table(
        index=["uc_id", "city", "time"],
        columns="control",
        values="ce_per_0.1",
        aggfunc="first",
    ).reset_index()
    needed = {"built_elev", "built_elev_water"}
    missing = needed - set(pivot.columns)
    if missing:
        raise ValueError(
            "Role 3 has not yet produced both water-effect controls. Missing: "
            + ", ".join(sorted(missing))
        )
    return pivot.dropna(subset=["built_elev", "built_elev_water"])


def _plot_water_effect() -> Path:
    if not COOLING_CSV.exists():
        raise FileNotFoundError(COOLING_CSV)
    ce = pd.read_csv(COOLING_CSV)
    d = _water_effect_data(ce)
    if d.empty:
        raise ValueError("No matched pre-monsoon water-effect rows to plot")

    apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.5), sharex=True, sharey=True)
    vals = d[["built_elev", "built_elev_water"]].to_numpy(float)
    lo = np.nanmin(vals)
    hi = np.nanmax(vals)
    pad = max((hi - lo) * 0.08, 0.15)
    lims = (lo - pad, hi + pad)

    for ax, time_name in zip(axes, ["day", "night"]):
        panel = d[d.time == time_name]
        ax.scatter(panel["built_elev"], panel["built_elev_water"], alpha=0.75)
        ax.plot(lims, lims, linestyle="--", linewidth=1)
        for city in ["Jodhpur", "Kochi"]:
            row = panel[panel.city.str.casefold() == city.casefold()]
            if len(row) == 1:
                x = float(row.iloc[0]["built_elev"])
                y = float(row.iloc[0]["built_elev_water"])
                ax.annotate(city, (x, y), xytext=(4, 4), textcoords="offset points", fontsize=9)
        ax.set_title(time_name.capitalize())
        ax.set_xlabel("Without water control\n" + CE_LABEL)
        ax.set_xlim(lims)
        ax.set_ylim(lims)
    axes[0].set_ylabel("With water control\n" + CE_LABEL)
    fig.suptitle("Effect of controlling for mapped water share (pre-monsoon)")
    fig.tight_layout()
    out = save(fig, "G_water_effect")
    plt.close(fig)

    # Numeric summary used directly in Role 5's observation/slide line.
    day = d[d.time == "day"]
    if not day.empty:
        med_before = day["built_elev"].median()
        med_after = day["built_elev_water"].median()
        print(
            f"Median daytime slope: {med_before:.3f} without water -> "
            f"{med_after:.3f} with water (n={len(day)} cities)"
        )
    j = d[(d.time == "night") & (d.city.str.casefold() == "jodhpur")]
    if len(j) == 1:
        before = float(j.iloc[0]["built_elev"])
        after = float(j.iloc[0]["built_elev_water"])
        state = "remains warming" if after > 0 else "no longer warms"
        print(
            f"Jodhpur night: {before:.3f} -> {after:.3f} °C per 0.1 NDVI; {state} after water control"
        )
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cities", nargs="*", help="city names or uc_id values (default: Jodhpur Kochi)")
    parser.add_argument("--all", action="store_true", help="process all currently sampled cities")
    parser.add_argument("--overwrite", action="store_true", help="recompute existing data/water files")
    parser.add_argument("--check", action="store_true", help="run Role-5 water quality checks")
    parser.add_argument("--effect", action="store_true", help="build G_water_effect.png from Role-3 results")
    parser.add_argument(
        "--sleep",
        type=float,
        default=1.5,
        help="seconds between cities for an all-city Overpass run (default 1.5)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Overpass HTTP/query timeout in seconds (Role-5 default: 300)",
    )
    parser.add_argument(
        "--overpass-url",
        default=None,
        help="alternate Overpass base API URL, e.g. https://overpass.private.coffee/api",
    )
    parser.add_argument(
        "--stop-after-failures",
        type=int,
        default=5,
        help="stop an --all run after this many consecutive failed cities; 0 disables",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.effect:
        out = _plot_water_effect()
        print(f"Wrote {out.relative_to(C.ROOT)}")
        if args.check:
            _run_water_checks()
        return

    if args.check and not args.cities and not args.all:
        _run_water_checks()
        return

    cities = _resolve_cities(args.cities, args.all)
    failures = []
    consecutive_failures = 0
    for i, (_, row) in enumerate(cities.iterrows(), start=1):
        city = str(row["name"])
        uc_id = int(row["ID_UC_G0"])
        already_done = _water_path(uc_id, city).exists() and not args.overwrite
        try:
            _process_city(
                row,
                overwrite=args.overwrite,
                timeout=max(int(args.timeout), 1),
                overpass_url=args.overpass_url,
            )
            consecutive_failures = 0
        except Exception as exc:
            failures.append((uc_id, city, str(exc)))
            consecutive_failures += 1
            print(f"FAIL {city} ({uc_id}): {exc}")
            if (
                args.all
                and args.stop_after_failures > 0
                and consecutive_failures >= args.stop_after_failures
            ):
                print(
                    f"Stopping after {consecutive_failures} consecutive failures; "
                    "completed city CSVs are preserved. Retry later to resume."
                )
                break
        # Pace only actual Overpass work. A resume with many finished cities should
        # skip quickly rather than sleeping for several minutes.
        if args.all and not already_done and i < len(cities):
            time.sleep(max(args.sleep, 0))

    if args.check:
        _run_water_checks()

    if failures:
        print("\nFailures:")
        for uc_id, city, err in failures:
            print(f"  {uc_id} {city}: {err}")
        raise SystemExit(1)

    if args.all:
        expected = len(cities)
        done = sum(
            _water_path(int(row.ID_UC_G0), str(row["name"])).exists()
            for _, row in cities.iterrows()
        )
        if done == expected:
            print(f"G complete: water files exist for all {expected} sampled cities")
        else:
            print(f"G incomplete: {done}/{expected} sampled cities have water files")


if __name__ == "__main__":
    main()
