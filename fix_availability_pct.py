import sys

with open('static/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('data.availability_pct_24h', 'data.availability_pct')

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed availability_pct key.")
