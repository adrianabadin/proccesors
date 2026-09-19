
import json
import glob
import os

files = [
    r"C:\Users\Adria\.local\share\opencode\tool-output\tool_c777ddcb10017R7RhoqQBlU3Nc",
    r"C:\Users\Adria\.local\share\opencode\tool-output\tool_c778272c0001NGA3YJ2GtHXm5c"
]

unique_ordinances = {}

for f_path in files:
    if os.path.exists(f_path):
        with open(f_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                results = data.get('results', [])
                for ord_info in results:
                    ord_id = ord_info.get('id')
                    if ord_id and ord_id not in unique_ordinances:
                        unique_ordinances[ord_id] = {
                            'id': ord_id,
                            'numero': ord_info.get('numero'),
                            'anio': ord_info.get('anio'),
                            'titulo': ord_info.get('titulo'),
                            'resumen': ord_info.get('resumen'),
                            'estado': ord_info.get('estado')
                        }
            except Exception as e:
                print(f"Error parsing {f_path}: {e}")

# Also add the ones from smaller searches in the previous messages if any missing
# (Manually identifying some from history if not in files)

print(f"Total unique ordinances found: {len(unique_ordinances)}")
with open('unique_health_ids.json', 'w', encoding='utf-8') as f:
    json.dump(list(unique_ordinances.values()), f, indent=2)
