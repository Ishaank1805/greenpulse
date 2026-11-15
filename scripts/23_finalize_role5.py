"""Finalize Role 5 results and observations without changing teammates' sections.

Requires the earlier scripts and the new square-exclusion analysis to have run.
Edits only the marked block under '## Role 5 (water and data quality)'. Re-running
it updates that block idempotently. The height conclusion is explicitly pending
until Johar provides height_effect.csv AND script 19 is rerun.

Usage: python scripts/23_finalize_role5.py [--require-height]
"""
import argparse
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import pandas as pd

import config as C
from role5_utils import RES, read_csv

BEGIN = '<!-- BEGIN ROLE5 FINAL VERIFIED OBSERVATIONS -->'
END = '<!-- END ROLE5 FINAL VERIFIED OBSERVATIONS -->'
HEADING = '## Role 5 (water and data quality)'


def one(df, **where):
    sub = df
    for k, v in where.items():
        sub = sub[sub[k].eq(v)]
    if len(sub) != 1:
        raise ValueError(f'Expected exactly one row for {where}; got {len(sub)}')
    return sub.iloc[0]


def fmt(x, digits=3):
    return f'{float(x):+.{digits}f}'


def build():
    h = read_csv('new_checks.csv', ['analysis','variant','statistic','n_cities','value'])
    w = read_csv('role5_water_sensitivity.csv', ['season','time','n_cities','median_paired_shift',
                                                'shift_ci_lo','shift_ci_hi','rho_abs_shift_vs_mean_water'])
    n = read_csv('role5_night_selection.csv', ['season','n_day_cities','n_night_cities',
                                              'rh_adjusted_odds_ratio_10pct','rh_or_ci_lo',
                                              'rh_or_ci_hi','rh_logit_p'])
    d = read_csv('role5_water_square_checks.csv', ['variant','selection','statistic','n_cities','value'])
    cities = read_csv('role5_dry_square_city_slopes.csv', ['uc_id','variant','n_removed_urban',
                                                          'restricted_ce_per_0_1'])
    # Confirm both dry-square variants cover the same 303 input cities.
    variants = set(cities.variant.unique())
    if variants != {'exclude_any_mapped_water','exclude_water_gt_5pct'}:
        raise AssertionError(f'Unexpected square-exclusion variants: {variants}')
    if cities.groupby('variant').uc_id.nunique().nunique()!=1:
        raise AssertionError('Square-exclusion variants do not cover the same city IDs')

    def h6(variant, metric):
        return one(h, analysis='H6', variant=variant,
                   statistic=f'spearman_{metric}_vs_rh')
    def dry(variant, selection, source, metric):
        return one(d, variant=variant, selection=selection,
                   statistic=f'spearman_{source}_{metric}_vs_rh')

    all_eff = h6('all','hi_efficiency'); ten_eff = h6('n_blocks_ge_10','hi_efficiency')
    all_star = h6('all','delta_star'); ten_star = h6('n_blocks_ge_10','delta_star')
    # The original all-city baseline must remain fixed: don't accidentally modify team results.
    if int(all_eff.n_cities)!=191 or abs(float(all_eff.value)-0.864551)>1e-5:
        raise AssertionError('H6 original baseline unexpectedly changed; reconcile inputs first')
    paired_w=one(w, season='pre', time='day')
    night=one(n, season='pre')
    dry_name='exclude_water_gt_5pct'; same='matched_cooling_cities'
    de_old=dry(dry_name,same,'original','hi_efficiency')
    de_new=dry(dry_name,same,'restricted','hi_efficiency')
    ds_old=dry(dry_name,same,'original','delta_star')
    ds_new=dry(dry_name,same,'restricted','delta_star')
    strict_old=dry('exclude_any_mapped_water',same,'original','hi_efficiency')
    strict_new=dry('exclude_any_mapped_water',same,'restricted','hi_efficiency')
    ten_dry=dry(dry_name,'matched_both_ge_10_blocks','restricted','hi_efficiency')
    if int(de_old.n_cities)!=int(de_new.n_cities):
        raise AssertionError('Unmatched water-square comparison groups')
    # Verify an old all-city mean-water filter did not masquerade as excluding squares.
    mean_water=one(h, analysis='H6',variant='water_mean_le_0.05 (extra)',
                   statistic='spearman_hi_efficiency_vs_rh')

    height = h[h.analysis.eq('height')]
    height_file=(RES/'height_effect.csv').exists()
    if height_file and height.empty:
        raise ValueError('height_effect.csv is present but checks are missing: rerun scripts/19_new_checks.py')
    if not height_file and not height.empty:
        raise ValueError('height checks present without source height_effect.csv; rerun script 19')

    lines = [
        '**Final-phase robustness (verified from CSVs):**',
        f'- **H6 (scenario, not measured felt heat):** Pre-monsoon +0.1 NDVI, fixed dewpoint, r=0.08. '
        f'Across {int(all_eff.n_cities)} greener-is-cooler cities, humidity correlates positively with '
        f'felt-heat efficiency (Spearman ρ={fmt(all_eff.value)}) and negatively with break-even dewpoint '
        f'rise (ρ={fmt(all_star.value)}). Restricting to ≥10 spatial blocks leaves '
        f'{int(ten_eff.n_cities)} cities (ρ={fmt(ten_eff.value)} and {fmt(ten_star.value)}, respectively). '
        'The efficiency direction contradicts the original H6 expectation, while break-even fragility supports it.',
        f'- **Actual exclusion of water-covered squares:** Refitting the pre-monsoon NDVI slope after '
        f'excluding squares with >5% OSM mapped water retains {int(de_new.n_cities)} matched cooling '
        f'cities. Humidity-efficiency ρ changes {fmt(de_old.value)} → {fmt(de_new.value)}; '
        f'humidity-break-even ρ changes {fmt(ds_old.value)} → {fmt(ds_new.value)}. '
        f'The ≥10-block restricted comparison contains {int(ten_dry.n_cities)} cities '
        f'(restricted efficiency ρ={fmt(ten_dry.value)}). '
        f'An even stricter exclusion of all positive mapped water gives '
        f'{int(strict_new.n_cities)} matched cities (ρ={fmt(strict_old.value)} → {fmt(strict_new.value)}). '
        'This is a separate within-city refit; excluding entire high-water cities is not the same test.',
        f'- **City-level water sensitivity:** The mean-water >5% city exclusion retains '
        f'{int(mean_water.n_cities)} H6 cities; the median-water >5% city exclusion excludes none. '
        f'Adding water to the city-level LST regression changes the median paired pre-monsoon '
        f'daytime slope by {float(paired_w.median_paired_shift):+.4f} °C per 0.1 NDVI '
        f'(bootstrap 95% interval {float(paired_w.shift_ci_lo):+.4f} to '
        f'{float(paired_w.shift_ci_hi):+.4f}). Absolute slope shifts are associated with '
        f'mean mapped water (Spearman ρ={fmt(paired_w.rho_abs_shift_vs_mean_water)}), '
        'without a causal interpretation.',
        f'- **Nighttime selection check:** Of {int(night.n_day_cities)} pre-monsoon '
        f'daytime-estimable cities, only {int(night.n_night_cities)} also have usable nighttime slopes. '
        f'An exploratory model adjusting for daytime sample count gives an odds ratio '
        f'{float(night.rh_adjusted_odds_ratio_10pct):.2f} per +10 percentage points RH '
        f'(95% CI {float(night.rh_or_ci_lo):.2f}–{float(night.rh_or_ci_hi):.2f}; '
        f'p={float(night.rh_logit_p):.2f}); there is no clear adjusted humidity association. '
        'This tests sample availability, not a pure cloud-only mechanism.',
    ]
    if height_file:
        ha=one(height,variant='all',statistic='share_positive_interaction_p_lt_0.05')
        hm=one(height,variant='all',statistic='median_tall_minus_low_ce_per_0.1')
        ht=one(height,variant='n_blocks_ge_10',statistic='share_positive_interaction_p_lt_0.05')
        lines.append(f'- **Building-height check (Johar input received):** '
                     f'{int(ha.n_cities)} paired pre-monsoon daytime cities; significantly positive '
                     f'interaction share {float(ha.value):.1%}, median tall-minus-low '
                     f'{float(hm.value):+.3f} °C per 0.1 NDVI. '
                     f'Among ≥10-block cities (n={int(ht.n_cities)}), positive-share '
                     f'{float(ht.value):.1%}. Confirm the all-city definition matches Johar’s own headline '
                     'before presenting the comparison.')
    else:
        lines.append('- **Building height: PENDING** Johar’s `data/results/height_effect.csv`. '
                     'The script is tested with synthetic data but no real height result can be claimed yet.')
    lines.append('')
    lines.append('**Interpretation:** LST slopes are observational cross-sectional associations; '
                 'H6 results are modelled Heat Index scenarios based on published conversion ratios and ERA5.')
    return '\n'.join(lines),height_file


def update_observations(block):
    path=C.ROOT/'docs'/'observations.md'
    if not path.exists():raise FileNotFoundError(f'Missing {path}')
    contents=path.read_text(encoding='utf-8')
    if contents.count(HEADING)!=1:
        raise ValueError('Role 5 observations section missing or duplicated; no file changed')
    if (BEGIN in contents)!=(END in contents):
        raise ValueError('Only one Role 5 managed marker exists; no file changed')
    section_start=contents.index(HEADING)
    next_section=contents.find('\n## ', section_start+len(HEADING))
    if next_section==-1:next_section=len(contents)
    lead, role, tail=contents[:section_start],contents[section_start:next_section],contents[next_section:]
    if BEGIN in role:
        a=role.index(BEGIN); b=role.index(END)+len(END)
        role=role[:a].rstrip()+'\n'+role[b:].lstrip('\n')
    # Do not silently delete a stale marked block located outside Role 5.
    if BEGIN in (lead+tail) or END in (lead+tail):
        raise ValueError('Managed markers occur outside Role 5; no file changed')
    role=role.rstrip()+f'\n\n{BEGIN}\n{block}\n{END}\n'
    path.write_text(lead+role+tail,encoding='utf-8')
    return path


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--require-height',action='store_true',help='Fail unless real Johar height CSV and checks exist')
    args=ap.parse_args()
    observations,has_height=build()
    if args.require_height and not has_height:
        raise FileNotFoundError('Height analysis still pending: upload height_effect.csv, rerun 19, retry')
    out=update_observations(observations)
    handoff=C.ROOT/'docs'/'ROLE5_FINAL_HANDOFF.md'
    status='COMPLETE (review against Johar’s numbers before presenting)' if has_height else 'PENDING Johar’s height_effect.csv'
    handoff.write_text('# Role 5 final handoff (outside presentation)\n\n'
                       'This report is generated from local results by `scripts/23_finalize_role5.py`.\n\n'
                       f'**Height check:** {status}.\n\n'
                       '## Verified findings\n\n'+observations+'\n\n'
                       '## Files to keep\n\n'
                       '- `scripts/19_new_checks.py`: original H6 + ≥10 and legacy >5 block checks; height when available\n'
                       '- `scripts/20_water_sensitivity.py`, `scripts/21_night_selection_bias.py`: additional experiments\n'
                       '- `scripts/22_water_square_exclusion.py`: actual removal of water-containing squares and refit\n'
                       '- `scripts/23_finalize_role5.py`: safe observation/handoff update\n'
                       '- `data/results/new_checks.csv`, `role5_water_sensitivity.csv`, `role5_night_selection.csv`, '
                       '`role5_dry_square_city_slopes.csv`, `role5_water_square_checks.csv`\n'
                       '- `figures/R5_h6_checks.png`, `figures/R5_water_sensitivity.png`, '
                       '`figures/R5_night_selection.png`\n\n'
                       '## Remaining dependency (not fabrication)\n\n'
                       '- Ask Johar for `data/results/height_effect.csv`, his height headline count and effect, '
                       'and related figure. Rerun `python scripts/19_new_checks.py --require-height`, '
                       'then `python scripts/23_finalize_role5.py --require-height`.\n'
                       '- Final deck, speaker script, teammate handoffs and group rehearsal are excluded here.\n\n'
                       '## Role 5 handoff points\n\n'
                       '1. The H6 scenario efficiency/humidity association stays positive under stricter '
                       'sample quality and dry-square exclusions, contrary to the originally expected direction.\n'
                       '2. More humid cities reach their modelled moisture break-even earlier; '
                       'the negative correlation survives water-square exclusion.\n'
                       '3. Control-for-water and nighttime selection checks identify possible '
                       'sources of bias but do not justify causal claims.\n',encoding='utf-8')
    files=[
        'data/results/new_checks.csv',
        'data/results/role5_water_sensitivity.csv',
        'data/results/role5_water_city_shifts.csv',
        'data/results/role5_night_selection.csv',
        'data/results/role5_night_city_selection.csv',
        'data/results/role5_dry_square_city_slopes.csv',
        'data/results/role5_water_square_checks.csv',
        'figures/R5_h6_checks.png',
        'figures/R5_water_sensitivity.png',
        'figures/R5_night_selection.png',
        'docs/ROLE5_FINAL_HANDOFF.md',
        'docs/observations.md',
        'docs/ROLE5_FINISH_ADA.md',
        'scripts/19_new_checks.py','scripts/20_water_sensitivity.py',
        'scripts/21_night_selection_bias.py','scripts/22_water_square_exclusion.py',
        'scripts/23_finalize_role5.py','scripts/role5_utils.py',
        'tests/test_role5.py',
        'run_role5_finish.sbatch','run_role5_height.sbatch',
    ]
    bundle=C.ROOT/'role5_handoff_bundle.zip'
    with ZipFile(bundle,'w',ZIP_DEFLATED) as z:
        for name in files:
            path=C.ROOT/name
            if not path.exists():
                raise FileNotFoundError(f'Incomplete handoff bundle, missing {name}')
            z.write(path,arcname=name)
    print('Packaged',bundle)
    print('Updated',out)
    print('Created',handoff)
    print('Height:',status)

if __name__=='__main__':main()
