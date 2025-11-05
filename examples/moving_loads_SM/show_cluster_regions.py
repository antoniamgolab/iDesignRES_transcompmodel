"""
Show detailed information about Germany-Denmark-Sweden cluster regions
"""
from sub_border_regions import SUB_BORDER_REGIONS

cluster = SUB_BORDER_REGIONS['Germany-Denmark-Sweden']

print('='*100)
print('GERMANY-DENMARK-SWEDEN CLUSTER - DETAILED NUTS2 REGION INFORMATION')
print('='*100)

print(f'\nCluster Description: {cluster["description"]}')
print(f'Total Regions: {len(cluster["regions"])}')
print(f'Countries: {", ".join(sorted(cluster["countries"]))}')

print('\n' + '='*100)
print('NUTS2 REGIONS BY COUNTRY:')
print('='*100)

# Denmark regions with names
print('\nDENMARK (All 5 NUTS2 regions):')
print('-' * 100)
dk_regions = {
    'DK01': 'Hovedstaden (Capital Region of Denmark) - includes Copenhagen',
    'DK02': 'Sjaelland (Zealand) - largest island, includes Great Belt Bridge',
    'DK03': 'Syddanmark (Southern Denmark) - includes Funen, borders Germany',
    'DK04': 'Midtjylland (Central Denmark Region) - central Jutland peninsula',
    'DK05': 'Nordjylland (North Denmark Region) - northern Jutland, ferry connections'
}

for code in sorted(dk_regions.keys()):
    print(f'  {code}: {dk_regions[code]}')

# Germany regions
print('\nGERMANY (1 region):')
print('-' * 100)
de_regions = {
    'DEF0': 'Schleswig-Holstein - northernmost German state, directly borders Denmark'
}

for code, name in de_regions.items():
    print(f'  {code}: {name}')

# Sweden regions
print('\nSWEDEN (2 regions):')
print('-' * 100)
se_regions = {
    'SE22': 'Sydsverige (Southern Sweden) - includes Skane County and Malmo',
    'SE23': 'Vastsverige (Western Sweden) - includes Gothenburg area'
}

for code in sorted(se_regions.keys()):
    print(f'  {code}: {se_regions[code]}')

print('\n' + '='*100)
print('KEY TRANSPORT CONNECTIONS:')
print('='*100)
print('''
1. Land Border:     DE (DEF0) <-> DK (DK03, DK05) via Jutland Peninsula
2. Oresund Bridge:  DK (DK01 Copenhagen) <-> SE (SE22 Malmo)
3. Great Belt:      DK (DK02 <-> DK03) - bridge connecting Danish islands
4. Little Belt:     DK (DK03 <-> DK04) - bridge in Denmark
5. Ferry Routes:    Multiple connections between all three countries
6. TEN-T Corridor:  Scandinavian-Mediterranean corridor passes through
''')

print('='*100)
print('SUMMARY:')
print('='*100)
print(f'''
This cluster captures the complete Danish transport system plus adjacent regions:
- All 5 Danish NUTS2 regions (complete country coverage)
- German border region (Schleswig-Holstein)
- Swedish Öresund regions (Copenhagen-Malmö connection)

Total: 8 NUTS2 regions across 3 countries
''')
print('='*100)
