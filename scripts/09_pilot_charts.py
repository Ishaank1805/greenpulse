"""Task A: pilot charts, Jodhpur vs Kochi, pre-monsoon (Apr-May), built >= 0.10.

A_pilot_scatter.png        2 x 2 (Jodhpur, Kochi) x (day, night). Partial-residual
                           (added-variable) plots, Frisch-Waugh-Lovell:
                             y = resid(lst ~ built) + mean(lst)
                             x = resid(ndvi ~ built) + mean(ndvi)
                           The slope of each cloud equals script 03's ce exactly (checked).
A_pilot_raw_vs_adjusted.png  Jodhpur by day: raw scatter vs adjusted, to show why the
                           built-up control matters.
A_pilot_seasons.png        Adjusted day plots for pre, post and winter, both cities
                           (new long-format files).

Data: data/samples/_pilot_v1/{jodhpur,kochi}.csv (old wide format = pre-monsoon).
Numbers in the text boxes come from data/results/cooling_efficiency.csv
(index = ndvi, built_min = 0.10, control = built, season = pre).
Night: squares with n_night >= 10, as in script 03.

Usage: python scripts/09_pilot_charts.py
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

import config as C
from style import CE_LABEL, MUTED, SEASON_COLORS, SEASON_LABELS, SEASONS, apply_style, save

BUILT_MIN = 0.10
MIN_NIGHTS = 10
PILOT = {'Jodhpur': ('jodhpur', '5315_jodhpur'), 'Kochi': ('kochi', '9386_kochi')}
EXPECTED_N_DAY = {'Jodhpur': 203, 'Kochi': 617}
X_LAB = 'Greenness (NDVI), adjusted for built-up share'
Y_LAB = 'Land-surface temperature (°C),\nadjusted for built-up share'


def pilot_frame(city):
    return pd.read_csv(C.SAMPLES_DIR / '_pilot_v1' / f'{PILOT[city][0]}.csv')


def urban(df, time):
    d = df[df.built >= BUILT_MIN].dropna(subset=[f'lst_{time}', 'ndvi', 'built'])
    return d[d.n_night >= MIN_NIGHTS] if time == 'night' else d


def partial(d, time):
    """FWL partial residuals (+ means, so axes keep real units) and their slope."""
    Z = sm.add_constant(d[['built']])
    y = d[f'lst_{time}']
    ry = sm.OLS(y, Z).fit().resid + y.mean()
    rx = sm.OLS(d.ndvi, Z).fit().resid + d.ndvi.mean()
    slope = np.polyfit(rx, ry, 1)
    return rx, ry, slope


def ce_row(ce, uc_id, season, time):
    r = ce[(ce.uc_id == uc_id) & (ce.season == season) & (ce.time == time) & (ce['index'] == 'ndvi')
           & ((ce.built_min - BUILT_MIN).abs() < 1e-9) & (ce.control == 'built')]
    return r.iloc[0]


def draw(ax, d, time, row, cmap_norm=None, label=True):
    rx, ry, b = partial(d, time)
    sc = ax.scatter(rx, ry, c=d.built, cmap='viridis', s=12, alpha=0.8, linewidths=0,
                    vmin=BUILT_MIN, vmax=0.6)
    xs = np.linspace(rx.quantile(0.01), rx.quantile(0.99), 50)
    ax.plot(xs, np.polyval(b, xs), color='crimson', lw=2)
    sig = '' if row.ci_hi < 0 or row.ci_lo > 0 else ' (n.s.)'
    ax.text(0.03, 0.04, f"{row['ce_per_0.1']:+.2f} °C per 0.1 NDVI{sig}\n"
            f"(95%: {row.ci_lo / 10:+.2f} to {row.ci_hi / 10:+.2f}), n = {int(row.n)}",
            transform=ax.transAxes, fontsize=9, va='bottom',
            bbox=dict(fc='white', ec='none', alpha=0.85))
    return sc, b[0]


def main():
    apply_style()
    ce = pd.read_csv(C.DATA / 'results' / 'cooling_efficiency.csv')
    ok = True

    # --- A_pilot_scatter --------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 8.5), layout='constrained')
    for i, city in enumerate(PILOT):
        df = pilot_frame(city)
        for j, time in enumerate(('day', 'night')):
            d = urban(df, time)
            row = ce_row(ce, df.uc_id.iloc[0], 'pre', time)
            sc, b = draw(axes[i, j], d, time, row)
            match = abs(b - row.ce) < 5e-5 and len(d) == row.n
            ok &= match
            print(f'  {city:8s} {time:5s} FWL slope {b:+.4f} vs ce {row.ce:+.4f}, '
                  f'n {len(d)} vs {int(row.n)}: {"ok" if match else "FAIL"}')
            if time == 'day':
                ok &= len(d) == EXPECTED_N_DAY[city]
            axes[i, j].set_title(f'{city} · {"day (~13:30)" if time == "day" else "night (~01:30)"}')
            axes[i, j].set_xlabel(X_LAB)
            axes[i, j].set_ylabel(Y_LAB)
    fig.colorbar(sc, ax=axes, shrink=0.6, label='Built-up share')
    fig.suptitle('Pilot, Apr–May 2019–2024: greener squares are cooler by day '
                 '(each dot = one 1 km urban square)')
    print(' ', save(fig, 'A_pilot_scatter').relative_to(C.ROOT))
    plt.close(fig)

    # --- A_pilot_raw_vs_adjusted (Jodhpur day) ---------------------------------------
    df = pilot_frame('Jodhpur')
    d = urban(df, 'day')
    raw = ce_row(ce, 5315, 'pre', 'day')
    raw_none = ce[(ce.uc_id == 5315) & (ce.season == 'pre') & (ce.time == 'day') & (ce['index'] == 'ndvi')
                  & ((ce.built_min - BUILT_MIN).abs() < 1e-9) & (ce.control == 'none')].iloc[0]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.6), layout='constrained')
    a1.scatter(d.ndvi, d.lst_day, c=d.built, cmap='viridis', s=12, alpha=0.8, linewidths=0,
               vmin=BUILT_MIN, vmax=0.6)
    bb = np.polyfit(d.ndvi, d.lst_day, 1)
    ok &= abs(bb[0] - raw_none.ce) < 5e-5
    xs = np.linspace(d.ndvi.quantile(0.01), d.ndvi.quantile(0.99), 50)
    a1.plot(xs, np.polyval(bb, xs), color=MUTED, lw=2, ls='--')
    sig = '' if raw_none.ci_hi < 0 else ' (not significant)'
    a1.text(0.03, 0.04, f"{raw_none['ce_per_0.1']:+.2f} °C per 0.1 NDVI{sig}\n"
            f"(95%: {raw_none.ci_lo / 10:+.2f} to {raw_none.ci_hi / 10:+.2f}), n = {int(raw_none.n)}",
            transform=a1.transAxes, fontsize=9, bbox=dict(fc='white', ec='none', alpha=0.85))
    a1.set_title('Raw: NDVI only')
    a1.set_xlabel('Greenness (NDVI)')
    a1.set_ylabel('Land-surface temperature (°C)')
    sc, _ = draw(a2, d, 'day', raw)
    a2.set_title('Adjusted: built-up share held fixed')
    a2.set_xlabel(X_LAB)
    a2.set_ylabel(Y_LAB)
    fig.colorbar(sc, ax=[a1, a2], shrink=0.8, label='Built-up share')
    fig.suptitle('Jodhpur, Apr–May by day: bare desert outskirts are hot, so the raw picture '
                 'hides the cooling')
    print(' ', save(fig, 'A_pilot_raw_vs_adjusted').relative_to(C.ROOT))
    plt.close(fig)

    # --- A_pilot_seasons (new long-format files, day, built control) ----------------
    fig, axes = plt.subplots(2, 3, figsize=(13, 8), layout='constrained', sharey='row')
    for i, city in enumerate(PILOT):
        dfl = pd.read_csv(C.SAMPLES_DIR / f'{PILOT[city][1]}.csv')
        for j, s in enumerate(SEASONS):
            d = urban(dfl[dfl.season == s], 'day')
            row = ce_row(ce, dfl.uc_id.iloc[0], s, 'day')
            sc, b = draw(axes[i, j], d, 'day', row)
            ok &= abs(b - row.ce) < 5e-5
            axes[i, j].set_title(f'{city} · {SEASON_LABELS[s]}', color=SEASON_COLORS[s])
            axes[i, j].set_xlabel(X_LAB if i == 1 else '')
        axes[i, 0].set_ylabel(Y_LAB)
    fig.colorbar(sc, ax=axes, shrink=0.5, label='Built-up share')
    fig.suptitle('Pilot cities by day in all three seasons (built-up share held fixed)')
    print(' ', save(fig, 'A_pilot_seasons').relative_to(C.ROOT))
    plt.close(fig)

    print('checks:', 'ALL OK' if ok else 'FAILED')
    return ok


if __name__ == '__main__':
    raise SystemExit(0 if main() else 1)
