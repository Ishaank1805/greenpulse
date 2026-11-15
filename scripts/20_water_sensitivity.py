"""Role 5 extension A: paired water-control sensitivity in all three seasons.

Matched by city/season/time, same NDVI threshold and built/elevation controls;
only difference is inclusion of OSM water fraction. Uses pre-urban OSM water
intensity as a city-level descriptive covariate. No refitting of the main model.
Usage: python scripts/20_water_sensitivity.py
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from role5_utils import RES, read_csv, water_intensity, spearman, median_ci
from style import apply_style, save


def calculate():
    d=read_csv('cooling_efficiency.csv',['uc_id','season','time','index','built_min',
                                         'control','ce','ci_lo','ci_hi'])
    d=d[(d['index']=='ndvi')&np.isclose(d.built_min,0.1)&
        d.control.isin(['built_elev','built_elev_water'])]
    d=d.dropna(subset=['ce'])
    if d.duplicated(['uc_id','season','time','control']).any():
        raise ValueError('Non-unique matched control rows')
    d=d.assign(slope=d.ce / 10)
    pivot=d.pivot(index=['uc_id','season','time'],columns='control',values='slope').dropna()
    pivot=pivot.reset_index().merge(water_intensity(),on='uc_id',validate='many_to_one')
    pivot['shift']=pivot.built_elev_water-pivot.built_elev
    pivot['absolute_shift']=pivot['shift'].abs()
    pivot.to_csv(RES/'role5_water_city_shifts.csv',index=False)

    rows=[]
    for (season,time),g in pivot.groupby(['season','time']):
        med,lo,hi=median_ci(g['shift'])
        rho_n,rho,p=spearman(g.water_mean,g.absolute_shift)
        nz=g['shift'][g['shift']!=0]
        wil_p=float(stats.wilcoxon(nz).pvalue) if len(nz)>=5 else np.nan
        a=g[g.water_mean>0.05].absolute_shift
        b=g[g.water_mean<=0.05].absolute_shift
        mw_p=float(stats.mannwhitneyu(a,b).pvalue) if len(a)>=2 and len(b)>=2 else np.nan
        rows.append(dict(season=season,time=time,n_cities=len(g),
                         median_without_water=float(g.built_elev.median()),
                         median_with_water=float(g.built_elev_water.median()),
                         median_paired_shift=med,shift_ci_lo=lo,shift_ci_hi=hi,
                         wilcoxon_p=wil_p,median_absolute_shift=float(g.absolute_shift.median()),
                         rho_abs_shift_vs_mean_water=rho,rho_p=p,
                         n_high_water=len(a),n_low_water=len(b),
                         median_abs_shift_high_water=float(a.median()) if len(a) else np.nan,
                         median_abs_shift_low_water=float(b.median()) if len(b) else np.nan,
                         high_vs_low_mannwhitney_p=mw_p))
    out=pd.DataFrame(rows).sort_values(['season','time'])
    out.to_csv(RES/'role5_water_sensitivity.csv',index=False)
    return pivot,out


def plot(city):
    apply_style()
    fig,axes=plt.subplots(2,3,figsize=(12,6.5),sharex=True,sharey=True)
    for j,season in enumerate(['pre','post','winter']):
        for i,time in enumerate(['day','night']):
            ax=axes[i,j]
            g=city[(city.season==season)&(city.time==time)]
            # Water shares near 0 are common; x-axis uses a percentage, not a log scale.
            ax.scatter(100*g.water_mean,g['shift'],s=14,alpha=.65,
                       c='#1F4D3A' if time=='day' else '#C8640A',rasterized=True)
            ax.axhline(0,color='black',lw=.8,alpha=.7)
            ax.set_title(f'{season.title()} - {time} (n={len(g)})')
            ax.text(.98,.97,f'Median shift {g["shift"].median():+.3f} °C',
                    transform=ax.transAxes,ha='right',va='top',fontsize=9)
            if i==1:ax.set_xlabel('Mean mapped water in urban squares (%)')
            if j==0:ax.set_ylabel('Slope change after water control\n(°C per 0.1 NDVI)')
    fig.suptitle('Matched city slope shifts: adding the water control\n'
                 'Positive = slope becomes less negative; association, not causation',fontsize=13)
    fig.tight_layout()
    save(fig,'R5_water_sensitivity')
    plt.close(fig)


def main():
    city,out=calculate();plot(city)
    print('Water-control sensitivity, paired slopes (°C per 0.1 NDVI):')
    print(out[['season','time','n_cities','median_paired_shift','shift_ci_lo',
               'shift_ci_hi','rho_abs_shift_vs_mean_water','rho_p','n_high_water']].to_string(index=False))
    print(f'Saved {len(city)} matched city-season-time shifts, {len(out)} season-time summaries')

if __name__=='__main__':main()
