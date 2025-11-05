import yaml
import glob

s_dict_files = glob.glob('results/case_20251103_114421/*_s_dict.yaml')
s_dict_file = sorted(s_dict_files)[-1]
print(f'Loading: {s_dict_file}')

with open(s_dict_file, 'r', encoding='utf-8') as f:
    s_data = yaml.safe_load(f)

# Parse the keys properly
print('\nFirst 10 entries after parsing:')
for i, (key_str, value) in enumerate(list(s_data.items())[:10]):
    key = eval(key_str)  # Parse the string representation
    print(f'{i+1}. Key: {key}')
    print(f'   Length: {len(key)}')
    if i < 3:
        print(f'   Elements:')
        for j, elem in enumerate(key):
            print(f'     [{j}] {elem} (type: {type(elem).__name__})')
    print(f'   Value: {value}')
    print()
