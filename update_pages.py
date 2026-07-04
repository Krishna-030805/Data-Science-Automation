import re, glob

files = ["pages/mining.py", "pages/analysis.py", "pages/ml.py", "pages/insights.py"]

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Replace imports
    content = re.sub(r'animated_counter', 'saas_kpi_card', content)
    content = re.sub(r'animated_radial_gauge', 'saas_radial_gauge', content)
    
    # Replace usages of animated_counter(..., color_class="...") with saas_kpi_card
    # Note: saas_kpi_card does not have color_class.
    content = re.sub(r'saas_kpi_card\(([^,]+),\s*([^,]+),\s*color_class="[^"]+"(.*?)\)', r'saas_kpi_card(\1, \2\3)', content)
    content = re.sub(r',\s*\)', ')', content) # cleanup trailing comma
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
        
print("Pages updated")
