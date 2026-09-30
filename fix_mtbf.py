import sys

with open('static/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'data.global_mtbf_hours > 0 ? data.global_mtbf_hours.toFixed(1) + " hrs" : "∞ (No Failures)";',
    'data.total_incidents > 0 ? data.global_mtbf_hours.toFixed(1) + " hrs" : "∞ (No Failures)";'
)

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed MTBF in index.html")
