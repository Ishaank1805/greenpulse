"""Step 8: one file of Indian urban centres (>= 300k people) with 2020 outlines.

Names and populations come from the regional UCDB file (2025 fixed boundaries);
outlines come from the multi-temporal file's 2020 layer, so they match the 2020
epoch of GHSL built-up and WorldPop. Both are GHS-UCDB R2024A v1.2 and share
the city ID ID_UC_G0.
"""
import geopandas as gpd

import config as C

NAMES_GPKG = (C.RAW / 'GHS_UCDB_REGION_CENTRAL_AND_SOUTHERN_ASIA_R2024A_V1_2'
              / 'GHS_UCDB_REGION_CENTRAL_AND_SOUTHERN_ASIA_R2024A.gpkg')
NAMES_LAYER = 'GHSL_UCDB_THEME_GENERAL_CHARACTERISTICS_GLOBE_R2024A'
OUTLINES_GPKG = (C.RAW / 'GHS_UCDB_MTUC_GLOBE_R2024A_V1_2'
                 / 'GHS_UCDB_MTUC_GLOBE_R2024A.gpkg')
OUTLINES_LAYER = 'GHSL_UCDB_MTUC_2020_GLOBE_R2024'


def main():
    names = gpd.read_file(NAMES_GPKG, layer=NAMES_LAYER, ignore_geometry=True)
    names = names[(names.GC_CNT_GAD_2025 == 'India')
                  & (names.GC_POP_TOT_2025 >= C.MIN_POP)]
    names = names[['ID_UC_G0', 'GC_UCN_MAI_2025', 'GC_POP_TOT_2025']].rename(
        columns={'GC_UCN_MAI_2025': 'name', 'GC_POP_TOT_2025': 'pop_2025'})

    outlines = gpd.read_file(OUTLINES_GPKG, layer=OUTLINES_LAYER)
    cities = outlines.merge(names, on='ID_UC_G0', how='inner')
    missing = set(names.ID_UC_G0) - set(cities.ID_UC_G0)
    if missing:
        raise SystemExit(f'No 2020 outline for city IDs: {sorted(missing)}')

    # 16 source outlines self-intersect where two grid cells touch only at a
    # corner. make_valid repairs them without changing area.
    cities['geometry'] = cities.geometry.make_valid()
    kinds = set(cities.geom_type)
    if not kinds <= {'Polygon', 'MultiPolygon'}:
        raise SystemExit(f'Repair produced non-polygon geometry: {kinds}')

    # Mollweide is equal-area, so measure area before converting to lat/lon.
    cities['area_km2'] = cities.area / 1e6
    cities = cities.to_crs('EPSG:4326')
    centre = cities.representative_point()
    cities['lon'], cities['lat'] = centre.x, centre.y

    cities = cities[['ID_UC_G0', 'name', 'pop_2025', 'area_km2', 'lon', 'lat', 'geometry']]
    cities = cities.sort_values('pop_2025', ascending=False)

    C.CITIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    cities.to_file(C.CITIES_FILE, driver='GeoJSON')
    print(f'{len(cities)} cities -> {C.CITIES_FILE.relative_to(C.ROOT)}')

    dupes = cities[cities.name.duplicated(keep=False)].sort_values('name')
    print('Duplicate names:', 'none' if dupes.empty else '')
    if not dupes.empty:
        print(dupes[['ID_UC_G0', 'name', 'pop_2025', 'lat', 'lon']].to_string(index=False))


if __name__ == '__main__':
    main()
