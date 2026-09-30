import sys

with open('static/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

sla_html = '''
  <div class="panel" id="global-sla-panel" style="background: rgba(46,204,113,0.05); border-color: rgba(46,204,113,0.2); padding: 20px; border-radius: 8px; margin-bottom: 24px; border: 1px solid var(--border);">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
      <h2 style="margin:0; color:var(--up); font-size:12px; letter-spacing:0.05em; text-transform:uppercase;">Global Service Level Agreement (SLA)</h2>
      <select id="sla-month-select" class="time-select" style="padding:4px 8px; border-radius:4px; border:1px solid var(--border); background:var(--bg); color:var(--text); font-size:12px;" onchange="loadGlobalSLA()">
      </select>
    </div>
    <div id="sla-loading" style="color:var(--muted); font-size:14px; text-align:center; padding: 20px;">Loading SLA Report...</div>
    <div id="sla-content" style="display:none; gap:32px; align-items:center; flex-wrap: wrap;">
      <div>
        <div style="color:var(--muted); font-size:12px;">Global Uptime (24h)</div>
        <div id="sla-uptime" style="font-size:28px; font-weight:600; color:var(--up);">--</div>
      </div>
      <div>
        <div style="color:var(--muted); font-size:12px;">MTTR (Mean Time to Resolve)</div>
        <div id="sla-mttr" style="font-size:24px; font-weight:600; color:var(--text);">--</div>
      </div>
      <div>
        <div style="color:var(--muted); font-size:12px;">MTBF (Mean Time Between Failures)</div>
        <div id="sla-mtbf" style="font-size:24px; font-weight:600; color:var(--text);">--</div>
      </div>
      <div>
        <div style="color:var(--muted); font-size:12px;">Total Incidents</div>
        <div id="sla-incidents" style="font-size:16px; font-weight:500; color:var(--muted);">--</div>
      </div>
    </div>
  </div>

  <h2>Service Health</h2>
'''

content = content.replace('<h2>Service Health</h2>', sla_html)

sla_js = '''
function populateSlaMonths() {
    const sel = document.getElementById("sla-month-select");
    sel.innerHTML = "";
    for(let i=0; i<3; i++) {
        let d = new Date();
        d.setMonth(d.getMonth() - i);
        let val = d.getFullYear() + "-" + String(d.getMonth()+1).padStart(2, '0');
        let txt = d.toLocaleString('default', { month: 'long', year: 'numeric' });
        sel.innerHTML += <option value=""></option>;
    }
}

async function loadGlobalSLA() {
    document.getElementById("sla-loading").style.display = "block";
    document.getElementById("sla-loading").textContent = "Loading SLA Report...";
    document.getElementById("sla-content").style.display = "none";
    try {
        const month = document.getElementById("sla-month-select").value;
        const res = await fetch(/api/reports/sla?month=);
        const data = await res.json();
        
        document.getElementById("sla-uptime").textContent = data.availability_pct_24h.toFixed(3) + "%";
        document.getElementById("sla-mttr").textContent = data.global_mttr_minutes > 0 ? data.global_mttr_minutes.toFixed(1) + " min" : "N/A";
        document.getElementById("sla-mtbf").textContent = data.global_mtbf_hours > 0 ? data.global_mtbf_hours.toFixed(1) + " hrs" : "∞ (No Failures)";
        document.getElementById("sla-incidents").textContent = data.total_incidents;
        
        if (data.availability_pct_24h < 99.0) {
            document.getElementById("sla-uptime").style.color = "var(--down)";
            document.getElementById("global-sla-panel").style.borderColor = "rgba(231,76,60,0.2)";
            document.getElementById("global-sla-panel").style.backgroundColor = "rgba(231,76,60,0.05)";
        } else if (data.availability_pct_24h < 99.9) {
            document.getElementById("sla-uptime").style.color = "var(--warn)";
            document.getElementById("global-sla-panel").style.borderColor = "rgba(245,166,35,0.2)";
            document.getElementById("global-sla-panel").style.backgroundColor = "rgba(245,166,35,0.05)";
        } else {
            document.getElementById("sla-uptime").style.color = "var(--up)";
            document.getElementById("global-sla-panel").style.borderColor = "rgba(46,204,113,0.2)";
            document.getElementById("global-sla-panel").style.backgroundColor = "rgba(46,204,113,0.05)";
        }
    } catch(e) {
        document.getElementById("sla-loading").textContent = "Failed to load SLA report.";
        return;
    }
    document.getElementById("sla-loading").style.display = "none";
    document.getElementById("sla-content").style.display = "flex";
}
populateSlaMonths();
loadGlobalSLA();

async function renderStatusGrid() {
'''

content = content.replace('async function renderStatusGrid() {', sla_js)

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated index.html")
