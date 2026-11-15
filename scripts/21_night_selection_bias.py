"""Role 5 extension B: selection bias from missing nighttime MODIS observations.

Question: is night LST availability nonrandom with respect to humidity/rainfall,
after accounting for the number of urban squares? City-level descriptive test,
not a causal explanation of cloud cover.
Usage: python scripts/21_night_selection_bias.py
"""
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import matplotlib.pyplot as plt
from role5_utils import RES, main_cooling, read_csv, median_ci
from style import apply_style, save


def calculate():
    main=main_cooling()
    climate=read_csv('city_climate.csv',['uc_id','season','rh_pct','rain_annual_mm'])
    # Denominator: cities with a valid daytime estimate under same main specification.
    day=main[main.time=='day'][['uc_id','city','season','n','n_blocks']].copy()
    if day.duplicated(['uc_id','season']).any():raise ValueError('Duplicate day city-season estimates')
    night=main[main.time=='night'][['uc_id','season']].copy()
    night['retained_night']=1
    d=day.merge(night,on=['uc_id','season'],how='left',validate='one_to_one')
    d['retained_night']=d.retained_night.fillna(0).astype(int)
    d=d.merge(climate[['uc_id','season','rh_pct','rain_annual_mm']],
              on=['uc_id','season'],validate='one_to_one')
    d['log_day_n']=np.log(d['n'].clip(lower=1))
    if d[['rh_pct','rain_annual_mm','log_day_n']].isna().any().any():
        raise ValueError('Missing climate/sample covariates in night-retention analysis')
    d.to_csv(RES/'role5_night_city_selection.csv',index=False)

    rows=[]
    for season,g in d.groupby('season'):
        keep=g[g.retained_night==1]
        drop=g[g.retained_night==0]
        row=dict(season=season,n_day_cities=len(g),n_night_cities=len(keep),
                 n_missing_night=len(drop),retention_pct=100*len(keep)/len(g),
                 median_rh_retained=float(keep.rh_pct.median()),
                 median_rh_missing=float(drop.rh_pct.median()),
                 median_rain_retained=float(keep.rain_annual_mm.median()),
                 median_rain_missing=float(drop.rain_annual_mm.median()),
                 median_day_cells_retained=float(keep.n.median()),
                 median_day_cells_missing=float(drop.n.median()),
                 mw_rh_p=float(stats.mannwhitneyu(keep.rh_pct,drop.rh_pct).pvalue),
                 mw_rain_p=float(stats.mannwhitneyu(keep.rain_annual_mm,drop.rain_annual_mm).pvalue),
                 mw_cells_p=float(stats.mannwhitneyu(keep.n,drop.n).pvalue))
        # Separate descriptive adjusted association: retention ~ humidity + sample size.
        # 10 percentage point humidity change; log-day-n accounts for city sample size.
        X=sm.add_constant(pd.DataFrame({'rh_10':g.rh_pct / 10,
                                        'log_day_n':g.log_day_n}),has_constant='add')
        try:
            model=sm.Logit(g.retained_night.astype(float),X).fit(disp=False,maxiter=200)
            ci=model.conf_int().loc['rh_10']
            row.update(rh_adjusted_odds_ratio_10pct=float(np.exp(model.params['rh_10'])),
                       rh_or_ci_lo=float(np.exp(ci.iloc[0])),
                       rh_or_ci_hi=float(np.exp(ci.iloc[1])),
                       rh_logit_p=float(model.pvalues['rh_10']))
        except (ValueError,np.linalg.LinAlgError) as e:
            print(f'WARNING: logistic regression unavailable in {season}: {e}')
            row.update(rh_adjusted_odds_ratio_10pct=np.nan,rh_or_ci_lo=np.nan,
                       rh_or_ci_hi=np.nan,rh_logit_p=np.nan)
        rows.append(row)
    out=pd.DataFrame(rows).sort_values('season')
    out.to_csv(RES/'role5_night_selection.csv',index=False)
    return d,out


def plot(d):
    apply_style()
    fig,axes=plt.subplots(1,3,figsize=(11.5,4.3),sharey=True)
    for ax,season in zip(axes,['pre','post','winter']):
        g=d[d.season==season]
        keep=g[g.retained_night==1]
        drop=g[g.retained_night==0]
        # Horizontal jitter is display-only; never used in statistics.
        rng=np.random.default_rng(53)
        for name,sub,color in [('Has night slope',keep,'#1F4D3A'),
                               ('Missing night slope',drop,'#C8640A')]:
            x=0 if name=='Has night slope' else 1
            ax.scatter(x+rng.uniform(-.16,.16,len(sub)),sub.rh_pct,
                       s=12,alpha=.4,c=color,label=f'{name} (n={len(sub)})')
            if len(sub):ax.hlines(sub.rh_pct.median(),x-.23,x+.23,color='black',lw=2)
        ax.set_xticks([0,1],['Retained','Missing'])
        ax.set_title(f'{season.title()} (day n={len(g)})')
        ax.legend(fontsize=7,loc='lower right')
        ax.set_xlim(-.4,1.4)
    axes[0].set_ylabel('City-season ERA5 relative humidity (%)')
    fig.suptitle('Selection into valid nighttime cooling slopes\n'
                 'Daytime-estimable cities only; each point is a city',fontsize=13)
    fig.tight_layout()
    save(fig,'R5_night_selection')
    plt.close(fig)


def main():
    d,out=calculate();plot(d)
    print('Nighttime availability and potential climate selection:')
    print(out[['season','n_day_cities','n_night_cities','median_rh_retained',
               'median_rh_missing','mw_rh_p','rh_adjusted_odds_ratio_10pct',
               'rh_or_ci_lo','rh_or_ci_hi','rh_logit_p']].to_string(index=False))
    print('All comparisons are associations. Missing nighttime estimates reflect both clear-sky '
          'availability and the minimum-sample requirement.')

if __name__=='__main__':main()
