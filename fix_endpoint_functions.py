import re

with open('static/endpoint.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix old_fetch if it's there
if 'renderTimeline(events, hours);' in content:
    content = content.replace('renderTimeline(events, hours);', '')
    
if 'renderTable(events);' in content:
    content = content.replace('renderTable(events);', 'renderIncidentsTable(incidents);')

# Let's fix the botched renderTable and new_renderTable
# I will find the start of renderTable or renderIncidentsTable and the start of renderChart
start_table = content.find('  function render')
end_table = content.find('  function renderChart')

if start_table != -1 and end_table != -1:
    before = content[:start_table]
    after = content[end_table:]
    
    new_render_table = '''  function renderIncidentsTable(incidents) {
    const tbody = document.getElementById('incidents-body');
    if (!tbody) return;
    tbody.innerHTML = "";
    
    if(incidents.length === 0) {
      tbody.innerHTML = "<tr><td colspan='7' style='text-align:center; color:var(--muted); padding:30px;'>No incidents recorded.</td></tr>";
      return;
    }

    incidents.forEach(inc => {
      const tr = document.createElement('tr');
      const isResolved = inc.status === 'resolved';
      const icon = isResolved ? "✓" : "!";
      const iconClass = isResolved ? "up" : "down";
      const statusBadge = isResolved ? <span class="badge resolved" style="background:rgba(46,204,113,0.15); color:var(--up);">Resolved</span> : <span class="badge open" style="background:rgba(231,76,60,0.15); color:var(--down);">Open</span>;
      const sevColor = inc.severity === 'critical' ? 'var(--down)' : (inc.severity === 'warning' ? 'var(--warn)' : 'var(--text)');
      
      let actions = <button class="btn btn-root-cause" onclick="openRootCause(, '')">Analyze Root Cause</button>;

      tr.innerHTML = 
        <td><div class="status-icon "></div></td>
        <td></td>
        <td></td>
        <td></td>
        <td style="color:; font-weight:600; text-transform:capitalize;"></td>
        <td></td>
        <td style="text-align: right;"></td>
      ;
      tbody.appendChild(tr);
    });
  }

'''
    # Wait, there's also renderTimeline that was between them originally.
    # Let's find the start of renderTimeline
    start_timeline = content.find('  function renderTimeline')
    if start_timeline != -1 and start_timeline < start_table:
        start_table = start_timeline
    
    content = content[:start_table] + new_render_table + content[end_table:]

with open('static/endpoint.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("endpoint.html functions fixed cleanly!")
