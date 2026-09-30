import sys
import re

with open('static/endpoint.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update dropdown
old_select = '''<select id="timeframe-select" class="time-select" onchange="loadData()">
      <option value="24">Last 24 hours</option>
      <option value="168" selected>Last 7 days</option>
      <option value="720">Last 30 days</option>
    </select>'''
new_select = '''<select id="timeframe-select" class="time-select" onchange="loadData()">
      <option value="1" selected>Last 1 hour</option>
      <option value="24">Last 24 hours</option>
      <option value="168">Last 7 days</option>
      <option value="720">Last 30 days</option>
    </select>'''
if old_select in content:
    content = content.replace(old_select, new_select)
else:
    print("WARNING: Could not find old_select")

# 2. Disable zoom plugin
content = content.replace("pan: { enabled: true", "pan: { enabled: false")
content = content.replace("wheel: { enabled: true }", "wheel: { enabled: false }")
content = content.replace("pinch: { enabled: true }", "pinch: { enabled: false }")

# 3. Fix RPS/Error null crashes
old_rps = "const rpsData = metricsHistory.map(h => h.rps);"
new_rps = "const rpsData = metricsHistory.map(h => h.rps || 0);"
content = content.replace(old_rps, new_rps)

old_err = "const errorData = metricsHistory.map(h => h.error_rate);"
new_err = "const errorData = metricsHistory.map(h => h.error_rate || 0);"
content = content.replace(old_err, new_err)

with open('static/endpoint.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("endpoint.html patched successfully!")
