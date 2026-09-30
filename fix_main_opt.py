with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('month: Optional[str] = None', 'month: str = None')

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed main.py")
