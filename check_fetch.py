import sys
with open('static/endpoint.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix fetch logic explicitly
if 'const evRes = await fetch(/api/endpoints//events?hours=);' in c:
    old = 'const evRes = await fetch(/api/endpoints//events?hours=);\n    const events = await evRes.json();'
    new = 'const incRes = await fetch(/api/endpoints//incidents?limit=50);\n    const incidents = await incRes.json();'
    c = c.replace(old, new)
    
with open('static/endpoint.html', 'w', encoding='utf-8') as f:
    f.write(c)
print("fetch logic double-checked.")
