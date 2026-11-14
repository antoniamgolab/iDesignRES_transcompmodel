"""
Build revision inputs with time-of-day charging prices (reviewer revision, 2026-10-13).

Copies an input scenario folder and rewrites the electricity entries of FuelCost.yaml:
    old:  price = 1.5 * (wholesale + tax) * {1.075 CCS | 0.97 MCS}
    new:  price = 1.3 * (tax + wholesale * f_tod)
with f_tod = night (22-06) / daily mean for CCS (overnight rest stops) and
day (06-22) / daily mean for MCS, per country, from ENTSO-E day-ahead prices 2023-2025.
The 30 % markup matches the manuscript (Lanz et al. 2022).

Usage:  python make_night_inputs.py <src_folder> <dst_folder>   (relative to input_data/)
"""
import os, shutil, sys
import pandas as pd
import yaml

ENTSOE = r'D:\AntoniaMariaG\spatial_arbitrage\model\data\ENTSOE_day_ahead_prices_raw.csv'
OLD_MARKUP, NEW_MARKUP = 1.5, 1.3
OLD_TYPE_FACTOR = {1: 1.075, 2: 0.97}  # fueling_infr_type_id 1 = CCS, 2 = MCS
# av_electricity_tax in SM_preprocessing.py: mean CostElectricityT of the 7 corridor countries
TAX = (0.0277 + 0.1005 + 0.1249 + 0.007 + 0.0787 + 0.01 + 0.0039) / 7


def tod_factors():
    df = pd.read_csv(ENTSOE, parse_dates=['timestamp']).set_index('timestamp').tz_convert('Europe/Berlin')
    df = df[(df.index.year >= 2023) & (df.index.year <= 2025)]
    night = (df.index.hour >= 22) | (df.index.hour < 6)
    zones = {'AT': ['AT'], 'DE': ['DE_LU'], 'DK': ['DK_1', 'DK_2'], 'FI': ['FI'],
             'IT': [c for c in df.columns if c.startswith('IT_')],
             'NO': [c for c in df.columns if c.startswith('NO_')],
             'SE': [c for c in df.columns if c.startswith('SE_')]}
    fac = {}
    for country, z in zones.items():
        s = df[z].mean(axis=1)
        fac[country] = (float(s[night].mean() / s.mean()), float(s[~night].mean() / s.mean()))
    return fac


def main(src, dst):
    src, dst = os.path.join('input_data', src), os.path.join('input_data', dst)
    os.makedirs(dst, exist_ok=True)
    for f in os.listdir(src):
        if f.endswith('.yaml'):
            shutil.copy(os.path.join(src, f), os.path.join(dst, f))
    fac = tod_factors()
    geo = {g['id']: g['country'] for g in yaml.safe_load(open(os.path.join(src, 'GeographicElement.yaml')))}
    fc = yaml.safe_load(open(os.path.join(src, 'FuelCost.yaml')))
    n = 0
    for c in fc:
        t = c.get('fueling_infr_type_id')
        if c.get('fuel') != 'electricity' or t not in OLD_TYPE_FACTOR:
            continue
        r = fac[geo[c['location']]][0 if t == 1 else 1]
        new = []
        for p in c['cost_per_kWh']:
            wholesale = p / OLD_MARKUP / OLD_TYPE_FACTOR[t] - TAX
            assert wholesale > 0, (c['id'], p)
            new.append(float(NEW_MARKUP * (TAX + wholesale * r)))
        c['cost_per_kWh'] = new
        n += 1
    yaml.safe_dump(fc, open(os.path.join(dst, 'FuelCost.yaml'), 'w'), sort_keys=False)
    print(f'{src} -> {dst}: {n} electricity price entries rewritten')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
