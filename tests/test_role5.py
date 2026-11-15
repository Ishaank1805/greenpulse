"""Offline smoke/regression checks for Role 5 scripts. Run: python -m unittest discover -s tests -p 'test_role5.py' -v"""
import importlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
role19=importlib.import_module('19_new_checks')
role20=importlib.import_module('20_water_sensitivity')
role21=importlib.import_module('21_night_selection_bias')
role22=importlib.import_module('22_water_square_exclusion')
role23=importlib.import_module('23_finalize_role5')
from role5_utils import main_cooling, water_intensity, spearman

class Role5Tests(unittest.TestCase):
    def test_h6_zero_change(self):
        d=role19.H6.hi_change(np.array([34.,38.]),np.array([16.,22.]),0,[0])[0]
        self.assertEqual(float(d[0]),0.0)

    def test_h6_matches_published_baseline(self):
        rows=[]
        role19.check_h6(rows,main_cooling(),water_intensity())
        baseline={(r['variant'],r['statistic']):r for r in rows}
        self.assertEqual(baseline[('all','spearman_hi_efficiency_vs_rh')]['n_cities'],191)
        self.assertAlmostEqual(baseline[('all','spearman_hi_efficiency_vs_rh')]['value'],.864551,places=5)
        self.assertEqual(baseline[('water_median_le_0.05','spearman_hi_efficiency_vs_rh')]['n_cities'],191)
        self.assertLess(baseline[('water_mean_le_0.05 (extra)','spearman_hi_efficiency_vs_rh')]['n_cities'],191)
        self.assertEqual(baseline[('n_blocks_ge_10','spearman_hi_efficiency_vs_rh')]['n_cities'],80)
        self.assertEqual(baseline[('main_slope_on_no_water_city_set','spearman_hi_efficiency_vs_rh')]['n_cities'],
                         baseline[('no_water_same_city_set','spearman_hi_efficiency_vs_rh')]['n_cities'])

    def test_water_matched_stats(self):
        city,summary=role20.calculate()
        self.assertEqual(len(summary),6)
        pre=summary[(summary.season=='pre')&(summary.time=='day')].iloc[0]
        self.assertEqual(int(pre.n_cities),202)
        self.assertAlmostEqual(pre.median_paired_shift,-.007362,places=4)
        self.assertTrue(city.water_mean.between(0,1).all())

    def test_night_retention_counts(self):
        _,summary=role21.calculate()
        pre=summary[summary.season=='pre'].iloc[0]
        self.assertEqual(int(pre.n_day_cities),202)
        self.assertEqual(int(pre.n_night_cities),135)
        self.assertEqual(int(pre.n_missing_night),67)

    def test_height_with_synthetic_contract(self):
        # Verify future Johar CSV handling now, without writing to the real repo result path.
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)
            vals=[]
            for uc,lo,hi,inter,p in [(10,-1.0,-.5,.5,.02),(11,-1.2,-1.4,-.2,.60),
                                       (12,-.8,-.2,.6,.01)]:
                for label,v in [('low',lo),('mid',(lo+hi)/2),('tall',hi)]:
                    vals.append(dict(uc_id=uc,city=f'C{uc}',season='pre',time='day',tercile=label,
                                     ci_lo=v-.1,ci_hi=v+.1, **{'ce_per_0.1':v},
                                     interaction=inter,interaction_p=p))
            pd.DataFrame(vals).to_csv(path/'height_effect.csv',index=False)
            ce=pd.DataFrame({'uc_id':[10,11,12],'season':['pre']*3,'time':['day']*3,
                             'n_blocks':[9,4,12]})
            water=pd.DataFrame({'uc_id':[10,11,12],
                                'water_median':[0,.1,0], 'water_mean':[0,.11,.06]})
            original_reader=role19.read_csv
            def fake_read(name,required):
                d=pd.read_csv(path/name)
                assert set(required)<=set(d.columns)
                return d
            with patch.object(role19,'RES',path),patch.object(role19,'read_csv',side_effect=fake_read):
                rows=[]
                self.assertTrue(role19.check_height(rows,ce,water,require_height=True))
            target=[r for r in rows if r['variant']=='all' and
                    r['statistic']=='share_positive_interaction_p_lt_0.05'][0]
            self.assertEqual(target['n_cities'],3)
            self.assertAlmostEqual(target['value'],2/3)
            median=[r for r in rows if r['variant']=='all' and
                    r['statistic']=='median_tall_minus_low_ce_per_0.1'][0]
            self.assertAlmostEqual(median['value'],0.5)

    def test_square_exclusion_matches_existing_baseline(self):
        from common import sample_paths
        paths=[p for p in sample_paths() if '10006_vellore' in p.name]
        self.assertEqual(len(paths),1)
        pre=main_cooling()
        pre=pre[(pre.season=='pre')&(pre.time=='day')]
        rows=role22.refit_one(paths[0],pre)
        self.assertEqual(len(rows),2)
        for row in rows:
            self.assertEqual(row['uc_id'],10006)
            self.assertLessEqual(row['restricted_n'],row['baseline_n'])
            self.assertGreaterEqual(row['n_removed_urban'],0)

    def test_square_exclusion_matched_population(self):
        from role5_utils import read_csv
        results=read_csv('role5_water_square_checks.csv',['variant','selection','statistic','n_cities','value'])
        cmp=results[(results.variant=='exclude_water_gt_5pct')&
                    (results.selection=='matched_cooling_cities')&
                    (results.statistic=='spearman_restricted_hi_efficiency_vs_rh')]
        self.assertEqual(len(cmp),1)
        self.assertEqual(int(cmp.iloc[0].n_cities),176)

    def test_finalize_section_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/'docs').mkdir()
            path=root/'docs'/'observations.md'
            path.write_text('## Team\nOther findings.\n\n'
                            '## Role 5 (water and data quality)\nOld role5 results.\n\n'
                            '## Further section\nKeep this unchanged.\n',encoding='utf-8')
            with patch.object(role23.C,'ROOT',root):
                role23.update_observations('Final facts.')
                first=path.read_text(encoding='utf-8')
                role23.update_observations('Final facts.')
                second=path.read_text(encoding='utf-8')
            self.assertEqual(first,second)
            self.assertEqual(second.count(role23.BEGIN),1)
            self.assertIn('Old role5 results.',second)
            self.assertIn('## Further section\nKeep this unchanged.',second)

if __name__=='__main__':unittest.main()
