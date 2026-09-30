import sys
import re

with open('static/endpoint.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace tabs and table header
old_table = '''  <div class="tabs">
    <div class="tab active">Uptime Changes</div>
  </div>

  <table id="events-table">
    <thead>
      <tr>
        <th width="50"></th>
        <th>From</th>
        <th>To</th>
        <th>Duration</th>
        <th style="text-align: right;">Actions</th>
      </tr>
    </thead>
    <tbody id="events-body">
      <tr><td colspan="5" style="text-align:center; color:var(--muted);">Loading...</td></tr>
    </tbody>
  </table>'''

new_table = '''  <div class="tabs">
    <div class="tab active">Incident History</div>
  </div>

  <table id="incidents-table">
    <thead>
      <tr>
        <th width="50"></th>
        <th>Start Time</th>
        <th>Resolution Time</th>
        <th>Duration</th>
        <th>Severity</th>
        <th>Status</th>
        <th style="text-align: right;">Actions</th>
      </tr>
    </thead>
    <tbody id="incidents-body">
      <tr><td colspan="7" style="text-align:center; color:var(--muted);">Loading...</td></tr>
    </tbody>
  </table>'''
content = content.replace(old_table, new_table)

# Replace the fetching logic in loadData()
old_fetch_events = '''    // Fetch Events (Timeline)
    const evRes = await fetch(/api/endpoints//events?hours=);
    const events = await evRes.json();
    
    renderTimeline(events, hours);
    renderTable(events);'''

new_fetch_incidents = '''    // Fetch Incidents
    const incRes = await fetch(/api/endpoints//incidents?limit=50);
    const incidents = await incRes.json();
    
    renderIncidentsTable(incidents);'''
content = content.replace(old_fetch_events, new_fetch_incidents)

# Remove renderTimeline entirely (replace with empty string or comment)
# Wait, let's keep timeline for now, but just disable it by removing its invocation
content = content.replace('renderTimeline(events, hours);', '')

# Replace renderTable with renderIncidentsTable
old_render_table = '''  function renderTable(events) {
    const tbody = document.getElementById('events-body');
    tbody.innerHTML = "";
    
    if(events.length === 0) {
      tbody.innerHTML = "<tr><td colspan='5' style='text-align:center; color:var(--muted);'>No events found in this timeframe.</td></tr>";
      return;
    }

    events.forEach(ev => {
      const tr = document.createElement('tr');
      const isUp = ev.status === 'up';
      const icon = isUp ? "↑" : "↓";
      
      let actions = <button class="btn" onclick="openTestLog('', '')">Test Log</button>;
      if (!isUp) {
        actions = <button class="btn btn-root-cause" onclick="openRootCause('', '')">Root Cause</button> + actions;
      }

      tr.innerHTML = 
        <td><div class="status-icon "></div></td>
        <td></td>
        <td></td>
        <td></td>
        <td style="text-align: right;"></td>
      ;
      tbody.appendChild(tr);
    });
  }'''

new_render_table = '''  function renderIncidentsTable(incidents) {
    const tbody = document.getElementById('incidents-body');
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
  }'''
content = content.replace(old_render_table, new_render_table)

# Update openRootCause function
old_root_cause = '''    async function openRootCause(fromTime, toTime) {
      document.getElementById('rc-modal').style.display = "flex";
      document.getElementById('rc-body').innerHTML = "Analyzing telemetry...";
      
      const res = await fetch(/api/endpoints//root_cause?from_time=&to_time=);
      const data = await res.json();
      
      let html = <div style="margin-bottom:16px;">
        <span style="color:var(--muted); font-size:12px; text-transform:uppercase;">Identified Causes</span>
      </div>;
      
      data.causes.forEach((cause, idx) => {
        html += 
          <div style="background:var(--panel-bg); border:1px solid rgba(255,255,255,0.1); border-radius:8px; padding:16px; margin-bottom:12px;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
              <h3 style="margin:0; color:var(--warn); font-size:16px;"></h3>
              <span style="background:rgba(255,255,255,0.1); padding:2px 8px; border-radius:12px; font-size:10px; font-weight:bold; color:var(--text);"> CONFIDENCE</span>
            </div>
            <p style="margin:0; color:var(--muted); line-height:1.5;"></p>
          </div>
        ;
      });
      
      document.getElementById('rc-body').innerHTML = html;
    }'''

new_root_cause = '''    async function openRootCause(incidentId, status) {
      document.getElementById('rc-modal').style.display = "flex";
      document.getElementById('rc-body').innerHTML = "<div style='text-align:center; color:var(--muted); padding:30px;'>Analyzing telemetry rules...</div>";
      
      try {
          const res = await fetch(/api/incidents//rca);
          const data = await res.json();
          
          let html = "";
          if (status === 'open') {
              html += <div style="background:rgba(245, 166, 35, 0.1); border:1px solid rgba(245, 166, 35, 0.5); color:var(--warn); padding:10px 16px; border-radius:6px; margin-bottom:16px; font-size:13px; font-weight:500;">⚠️ Incident is still open — analysis is preliminary.</div>;
          }
          
          html += <div style="margin-bottom:12px;">
            <span style="color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:0.5px;">Rule Evaluation</span>
          </div>;
          
          data.rca_analysis.forEach((cause, idx) => {
            html += 
              <div style="background:var(--panel); border:1px solid var(--border); border-radius:8px; padding:16px; margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                  <h3 style="margin:0; color:; font-size:16px;"></h3>
                  <span style="background:rgba(255,255,255,0.05); border:1px solid var(--border); padding:2px 8px; border-radius:12px; font-size:10px; font-weight:bold; color:var(--text);"> CONFIDENCE</span>
                </div>
                <p style="margin:0; color:var(--text); line-height:1.5; font-size:13px;"></p>
              </div>
            ;
          });
          
          html += <div style="margin-top:24px; margin-bottom:12px;">
            <span style="color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:0.5px;">Telemetry Snapshot (Onset & Recovery)</span>
          </div>;
          
          if (data.telemetry_snapshot && data.telemetry_snapshot.length > 0) {
              html += <table style="width:100%; border-collapse:collapse; font-size:12px;">
                <thead>
                  <tr style="border-bottom:1px solid var(--border);">
                    <th style="padding:8px; text-align:left; color:var(--muted);">Time</th>
                    <th style="padding:8px; text-align:left; color:var(--muted);">Status</th>
                    <th style="padding:8px; text-align:left; color:var(--muted);">CPU %</th>
                    <th style="padding:8px; text-align:left; color:var(--muted);">Mem %</th>
                    <th style="padding:8px; text-align:left; color:var(--muted);">Resp (ms)</th>
                    <th style="padding:8px; text-align:left; color:var(--muted);">Error</th>
                  </tr>
                </thead>
                <tbody>;
              
              data.telemetry_snapshot.forEach((snap, idx) => {
                  if (idx === 5 && data.telemetry_snapshot.length > 5) {
                      html += <tr><td colspan="6" style="text-align:center; padding:12px 0; color:var(--muted); border-top:1px dashed var(--border); border-bottom:1px dashed var(--border); background:rgba(255,255,255,0.02);">... incident window ...</td></tr>;
                  }
                  
                  const ts = new Date(snap.timestamp).toLocaleTimeString();
                  const status = snap.status_code || 'Timeout';
                  const cpu = snap.server_cpu_percent !== null ? snap.server_cpu_percent.toFixed(1) : '-';
                  const mem = snap.server_memory_percent !== null ? snap.server_memory_percent.toFixed(1) : '-';
                  const resp = snap.response_time_ms !== null ? snap.response_time_ms.toFixed(0) : '-';
                  const err = snap.error_message ? <span title="" style="color:var(--down); cursor:help;">...</span> : '-';
                  
                  html += <tr style="border-bottom:1px solid rgba(42,51,72,0.5);">
                    <td style="padding:8px;"></td>
                    <td style="padding:8px;"></td>
                    <td style="padding:8px;"></td>
                    <td style="padding:8px;"></td>
                    <td style="padding:8px;"></td>
                    <td style="padding:8px;"></td>
                  </tr>;
              });
              
              html += </tbody></table>;
          } else {
              html += <div style="text-align:center; color:var(--muted); padding:20px; border:1px solid var(--border); border-radius:8px; background:rgba(255,255,255,0.02);">No telemetry captured during outage window.</div>;
          }
          
          document.getElementById('rc-body').innerHTML = html;
      } catch (err) {
          document.getElementById('rc-body').innerHTML = <div style="color:var(--down); padding:20px;">Failed to load RCA: </div>;
      }
    }'''
content = content.replace(old_root_cause, new_root_cause)

with open('static/endpoint.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated endpoint.html")
