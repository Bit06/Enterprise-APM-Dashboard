import sys

with open('static/endpoint.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "if(incidents.length === 0) {",
    "if(!Array.isArray(incidents) || incidents.length === 0) {"
)

with open('static/endpoint.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Added Array.isArray check to endpoint.html")
