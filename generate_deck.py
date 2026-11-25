import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Colors matching the reference Covenant University presentation
    C_BG = RGBColor(255, 255, 255)
    C_DARK = RGBColor(18, 18, 18)
    C_RUST = RGBColor(194, 65, 12)     # Deep burnt orange/rust accent
    C_MUTED = RGBColor(100, 116, 139)  # Slate gray for subtitles & metadata
    C_CARD_BG = RGBColor(248, 250, 252) # Very light slate card background
    C_CARD_BORDER = RGBColor(226, 232, 240)
    C_RUST_BG = RGBColor(254, 242, 242)

    def add_header(slide, section_num, section_name, current_slide, total_slides="09"):
        # Section name left
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(8.0), Inches(0.4))
        p = tb.text_frame.paragraphs[0]
        p.text = f"{section_num} — {section_name.upper()}"
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = C_DARK
        p.font.name = "Arial"

        # Slide counter right
        tb2 = slide.shapes.add_textbox(Inches(10.5), Inches(0.5), Inches(2.0), Inches(0.4))
        p2 = tb2.text_frame.paragraphs[0]
        p2.alignment = PP_ALIGN.RIGHT
        p2.text = f"{current_slide} / {total_slides}"
        p2.font.size = Pt(11)
        p2.font.bold = True
        p2.font.color.rgb = C_MUTED
        p2.font.name = "Arial"

    def add_titles(slide, headline, subtitle):
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.95), Inches(11.7), Inches(0.6))
        p = tb.text_frame.paragraphs[0]
        p.text = headline
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = C_DARK
        p.font.name = "Arial"

        tb_sub = slide.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.7), Inches(0.5))
        p_sub = tb_sub.text_frame.paragraphs[0]
        p_sub.text = subtitle
        p_sub.font.size = Pt(13)
        p_sub.font.color.rgb = C_MUTED
        p_sub.font.name = "Arial"

    # ==========================================
    # SLIDE 0: TITLE SLIDE
    # ==========================================
    s0 = prs.slides.add_slide(blank_layout)
    
    # Top Institution Header
    tb = s0.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(11.7), Inches(0.4))
    p = tb.text_frame.paragraphs[0]
    p.text = "EIE · COMPUTER ENGINEERING  |  COVENANT UNIVERSITY"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = C_MUTED
    p.font.name = "Arial"

    # Project Title
    tb_title = s0.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.7), Inches(1.8))
    p_title = tb_title.text_frame.paragraphs[0]
    p_title.text = "INTELLIGENT APM"
    p_title.font.size = Pt(54)
    p_title.font.bold = True
    p_title.font.color.rgb = C_DARK
    p_title.font.name = "Arial"

    p_sub = tb_title.text_frame.add_paragraph()
    p_sub.text = "Development of an Intelligent API & Application Performance Monitoring System for Enterprise Services"
    p_sub.font.size = Pt(16)
    p_sub.font.color.rgb = C_RUST
    p_sub.font.name = "Arial"

    # Metadata cards bottom
    # Student
    tb_st = s0.shapes.add_textbox(Inches(0.8), Inches(5.4), Inches(5.0), Inches(1.2))
    p1 = tb_st.text_frame.paragraphs[0]
    p1.text = "STUDENT / CANDIDATE"
    p1.font.size = Pt(10)
    p1.font.bold = True
    p1.font.color.rgb = C_MUTED
    p2 = tb_st.text_frame.add_paragraph()
    p2.text = "[CANDIDATE NAME]"
    p2.font.size = Pt(15)
    p2.font.bold = True
    p2.font.color.rgb = C_DARK
    p3 = tb_st.text_frame.add_paragraph()
    p3.text = "Matriculation: [MATRIC NO]"
    p3.font.size = Pt(12)
    p3.font.color.rgb = C_MUTED

    # Supervisor
    tb_sp = s0.shapes.add_textbox(Inches(6.8), Inches(5.4), Inches(5.0), Inches(1.2))
    p1 = tb_sp.text_frame.paragraphs[0]
    p1.text = "PROJECT SUPERVISOR"
    p1.font.size = Pt(10)
    p1.font.bold = True
    p1.font.color.rgb = C_MUTED
    p2 = tb_sp.text_frame.add_paragraph()
    p2.text = "[SUPERVISOR NAME]"
    p2.font.size = Pt(15)
    p2.font.bold = True
    p2.font.color.rgb = C_DARK
    p3 = tb_sp.text_frame.add_paragraph()
    p3.text = "Department of Electrical & Information Engineering"
    p3.font.size = Pt(12)
    p3.font.color.rgb = C_MUTED

    # ==========================================
    # SLIDE 1: 01 — THE PROBLEM
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)
    add_header(s1, "01", "The Problem", "01")
    add_titles(s1, "Fragmented signals, silent cascades.", 
               "Enterprise services depend on chains of microservices, databases, and third-party APIs. A delay in one dependency silently breaks the wider service.")

    # 3 Cards Left
    cards = [
        ("CASCADE FAILURES", "A delay in a downstream database or third-party service surfaces as a failure in an unrelated upstream API."),
        ("FRAGMENTED TOOLS", "Metrics, logs, and distributed traces sit in separate monitoring tools with tedious manual correlation."),
        ("BLACK-BOX APIS", "Managed cloud dependencies cannot be inspected internally; only client-side duration and timeouts are visible.")
    ]
    for i, (title, desc) in enumerate(cards):
        top_pos = Inches(2.3 + i * 1.5)
        # Card shape
        shape = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), top_pos, Inches(5.6), Inches(1.3))
        shape.fill.solid()
        shape.fill.fore_color.rgb = C_CARD_BG
        shape.line.color.rgb = C_CARD_BORDER
        shape.line.width = Pt(1)

        tb = s1.shapes.add_textbox(Inches(1.0), top_pos + Inches(0.12), Inches(5.2), Inches(1.0))
        p = tb.text_frame.paragraphs[0]
        p.text = title
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = C_RUST if i == 0 else C_DARK
        p2 = tb.text_frame.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(10.5)
        p2.font.color.rgb = C_MUTED

    # Right Diagram
    r_shape = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.8), Inches(2.3), Inches(5.7), Inches(4.3))
    r_shape.fill.solid()
    r_shape.fill.fore_color.rgb = C_CARD_BG
    r_shape.line.color.rgb = C_CARD_BORDER

    tb_diag = s1.shapes.add_textbox(Inches(7.1), Inches(2.5), Inches(5.1), Inches(3.9))
    tf = tb_diag.text_frame
    p = tf.paragraphs[0]
    p.text = "THE DIAGNOSTIC GAP IN PRACTICE"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = C_DARK

    lines = [
        ("\n[ Client Request ]", C_DARK, True),
        ("       ↓", C_MUTED, False),
        ("[ API Gateway ]", C_DARK, True),
        ("       ↓", C_MUTED, False),
        ("[ Microservice A ]  -->  [ Microservice B ]", C_DARK, True),
        ("                                ↓ (Egress Call)", C_MUTED, False),
        ("[ External Black-Box Dependency ]", C_RUST, True),
        ("  • Latency spikes to 3.0s or times out", C_RUST, False),
        ("  • Upstream services crash with HTTP 500", C_RUST, False),
        ("  • Static threshold alerts report symptom, NOT cause", C_MUTED, False)
    ]
    for text, col, bold in lines:
        p = tf.add_paragraph()
        p.text = text
        p.font.size = Pt(10)
        p.font.bold = bold
        p.font.color.rgb = col

    # ==========================================
    # SLIDE 2: 02 — MOTIVATION
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "02", "Motivation", "02")
    add_titles(s2, "The observability gap.", 
               "Current monitoring forces an impossible choice between brittle manual rules and proprietary, expensive black-box suites.")

    # Two big comparison columns
    col_data = [
        (Inches(0.8), "TRADITIONAL MONITORING", "Nagios / Zabbix / Static Rules", [
            ("DETECTION", "Fixed threshold limits (e.g., Latency > 500ms)."),
            ("LIMITATION", "High false alarms on traffic bursts; false negatives on gradual degradation; zero context."),
            ("COLD START", "Requires manual tuning for every new endpoint."),
            ("DIAGNOSIS", "Alerts only that a limit broke; leaves root cause to human guesswork.")
        ], C_CARD_BG, C_CARD_BORDER),
        (Inches(6.8), "PROPRIETARY APM SUITES", "Datadog / Dynatrace / New Relic", [
            ("DETECTION", "Full-stack automated analytics and tracing."),
            ("LIMITATION", "Millions of naira annually; proprietary vendor lock-in; opaque cloud processing."),
            ("COLD START", "Deep models require huge datasets and fail on newly deployed services."),
            ("DIAGNOSIS", "Internal algorithms are closed; black-box dependencies remain unverified.")
        ], C_RUST_BG, C_RUST)
    ]

    for left, title, sub, items, bg_col, b_col in col_data:
        box = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, Inches(2.3), Inches(5.7), Inches(4.1))
        box.fill.solid()
        box.fill.fore_color.rgb = bg_col
        box.line.color.rgb = b_col
        box.line.width = Pt(1.5)

        tb = s2.shapes.add_textbox(left + Inches(0.3), Inches(2.5), Inches(5.1), Inches(3.7))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = C_DARK

        p_s = tf.add_paragraph()
        p_s.text = sub
        p_s.font.size = Pt(10)
        p_s.font.color.rgb = C_MUTED

        for lbl, txt in items:
            p_lbl = tf.add_paragraph()
            p_lbl.text = f"\n{lbl}"
            p_lbl.font.size = Pt(9.5)
            p_lbl.font.bold = True
            p_lbl.font.color.rgb = C_RUST if b_col == C_RUST else C_DARK
            p_txt = tf.add_paragraph()
            p_txt.text = txt
            p_txt.font.size = Pt(10)
            p_txt.font.color.rgb = C_DARK

    # Bottom takeaway
    tb_bot = s2.shapes.add_textbox(Inches(0.8), Inches(6.6), Inches(11.7), Inches(0.5))
    p = tb_bot.text_frame.paragraphs[0]
    p.text = "Our system is the hybrid solution — open-standard, low-cost OpenTelemetry telemetry combining unsupervised ML with a statistical safety net."
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = C_DARK

    # ==========================================
    # SLIDE 3: 03 — OBJECTIVES
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "03", "Objectives", "03")
    add_titles(s3, "Aim & specific objectives.", 
               "Design, implement, and validate an intelligent APM prototype that detects anomalous API behavior and provides explainable indications of likely causes.")

    objs = [
        ("01", "Analyze Observability & ML Gaps", "Synthesize existing APM, time-series anomaly detection, benchmark flaws, and derive requirements for cold-start mitigation."),
        ("02", "Design OpenTelemetry Ingestion Pipeline", "Architect an open pipeline collecting API RED metrics (Rate, Errors, Duration), traces, and host signals (CPU/RAM)."),
        ("03", "Implement Multivariate Anomaly Detection", "Train an Isolation Forest with RobustScaler and deploy an automated statistical threshold fallback for cold-start conditions."),
        ("04", "Develop Multimodal Root Cause Analysis (RCA)", "Correlate anomalies with W3C trace context, socket error logs, and resource metrics to generate ranked diagnostic hints."),
        ("05", "Evaluate Empirically Against Baseline", "Benchmark against fixed-threshold monitoring using a 12,000-point controlled workload and the public Server Machine Dataset (SMD).")
    ]

    for i, (num, headline, desc) in enumerate(objs):
        top_pos = Inches(2.2 + i * 0.95)
        # Number box
        n_box = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), top_pos, Inches(0.7), Inches(0.75))
        n_box.fill.solid()
        n_box.fill.fore_color.rgb = C_RUST
        n_box.line.fill.background()
        p = n_box.text_frame.paragraphs[0]
        p.text = num
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)

        # Content box
        c_box = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.6), top_pos, Inches(10.9), Inches(0.75))
        c_box.fill.solid()
        c_box.fill.fore_color.rgb = C_CARD_BG
        c_box.line.color.rgb = C_CARD_BORDER
        tb = s3.shapes.add_textbox(Inches(1.8), top_pos + Inches(0.06), Inches(10.5), Inches(0.65))
        p = tb.text_frame.paragraphs[0]
        p.text = headline
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = C_DARK
        p2 = tb.text_frame.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = C_MUTED

    # ==========================================
    # SLIDE 4: 04 — ARCHITECTURE
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "04", "Architecture", "04")
    add_titles(s4, "What the system is.", 
               "A decoupled, vendor-neutral observability architecture that isolates analytical workloads from the API request path.")

    stages = [
        ("STAGE 1 · COLLECTION", "Continuous Ingestion & Probing", [
            "• Synthetic Probes (APScheduler every 60s)",
            "• OpenTelemetry W3C Trace Headers (traceparent)",
            "• Asynchronous telemetry queue (Queue.Queue)",
            "• Zero added latency to production API requests"
        ]),
        ("STAGE 2 · ANALYTICS & RCA", "Multivariate ML & Diagnostics", [
            "• 6D Multivariate Isolation Forest (300 trees)",
            "• RobustScaler fitted strictly on training data",
            "• Cold-Start Statistical Baseline Fallback",
            "• Multimodal Root Cause Analysis (Table 5.4)"
        ]),
        ("STAGE 3 · PRESENTATION", "Real-Time Dashboard & Alerts", [
            "• FastAPI REST Backend + SQLite Time-Series DB",
            "• Real-Time Chart.js Dashboard with Anomaly Dots",
            "• Deduplicated SMTP Email & Microsoft Teams Alerts",
            "• SLO Error Budget Burn Rate Monitoring"
        ])
    ]

    for i, (title, sub, bullets) in enumerate(stages):
        left_pos = Inches(0.8 + i * 4.0)
        box = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, left_pos, Inches(2.3), Inches(3.7), Inches(4.3))
        box.fill.solid()
        box.fill.fore_color.rgb = C_CARD_BG
        box.line.color.rgb = C_CARD_BORDER
        box.line.width = Pt(1.5)

        tb = s4.shapes.add_textbox(left_pos + Inches(0.2), Inches(2.5), Inches(3.3), Inches(3.9))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = C_RUST

        p_s = tf.add_paragraph()
        p_s.text = sub
        p_s.font.size = Pt(12)
        p_s.font.bold = True
        p_s.font.color.rgb = C_DARK

        for b in bullets:
            p_b = tf.add_paragraph()
            p_b.text = f"\n{b}"
            p_b.font.size = Pt(10)
            p_b.font.color.rgb = C_MUTED

    # ==========================================
    # SLIDE 5: 05 — DETECTION ENGINE
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "05", "Detection Engine", "05")
    add_titles(s5, "Multivariate isolation with cold-start safety.", 
               "Combining unsupervised machine learning with statistical safeguards to eliminate day-one blind spots.")

    cols = [
        ("6D MULTIVARIATE VECTOR", "Comprehensive Signal Set", 
         "Analyzes 6 metrics simultaneously:\n• Request Rate (RPS)\n• P95 Response Latency\n• P99 Response Latency\n• HTTP 5xx Error Rate\n• Host CPU Utilization\n• Host RAM Utilization\n\nCatches multi-metric interactions that bypass single thresholds."),
        ("COLD-START FALLBACK", "Day-One Reliability", 
         "When an API has < 25 historical samples:\n• Enforces robust rolling medians & IQRs\n• Applies operational safety thresholds (warn/critical latency, CPU > 85%)\n• Prevents inaccurate model scoring during deployment\n• Automatically transitions to ML when history is ready."),
        ("ISOLATION FOREST", "Unsupervised Scoring", 
         "• 300 isolation trees\n• RobustScaler normalization prevents leakage\n• Anomaly Score Threshold set empirically from training distribution\n• Measures partition depth: anomalies isolate in very few random cuts\n• Detects subtle degradation ramps early.")
    ]

    for i, (head, sub, body) in enumerate(cols):
        left_pos = Inches(0.8 + i * 4.0)
        box = s5.shapes.add_shape(MSO_SHAPE.RECTANGLE, left_pos, Inches(2.3), Inches(3.7), Inches(4.3))
        box.fill.solid()
        box.fill.fore_color.rgb = C_CARD_BG if i != 1 else C_RUST_BG
        box.line.color.rgb = C_CARD_BORDER if i != 1 else C_RUST
        box.line.width = Pt(1.5)

        tb = s5.shapes.add_textbox(left_pos + Inches(0.2), Inches(2.5), Inches(3.3), Inches(3.9))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = head
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = C_RUST if i == 1 else C_DARK

        p_s = tf.add_paragraph()
        p_s.text = sub
        p_s.font.size = Pt(12)
        p_s.font.bold = True
        p_s.font.color.rgb = C_DARK

        p_b = tf.add_paragraph()
        p_b.text = f"\n{body}"
        p_b.font.size = Pt(10)
        p_b.font.color.rgb = C_MUTED

    # ==========================================
    # SLIDE 6: 06 — ROOT CAUSE ANALYSIS
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "06", "Root Cause Analysis", "06")
    add_titles(s6, "Explainable evidence, not black-box guesses.", 
               "Correlating anomalies across metrics, socket error logs, and W3C trace identifiers to diagnose the exact failure mode.")

    # Left: Trigger Rules Table
    left_box = s6.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(2.3), Inches(6.8), Inches(4.4))
    left_box.fill.solid()
    left_box.fill.fore_color.rgb = C_CARD_BG
    left_box.line.color.rgb = C_CARD_BORDER

    tb = s6.shapes.add_textbox(Inches(1.0), Inches(2.4), Inches(6.4), Inches(4.1))
    tf = tb.text_frame
    p = tf.paragraphs[0]
    p.text = "DIAGNOSTIC TRIGGER RULES (TABLE 5.4 SCHEMA)"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = C_DARK

    rules = [
        ("SERVICE OFFLINE", "Status code is None / connection refused in >= 50% checks."),
        ("CPU SATURATION", "Host CPU average > 85% or peak > 92% across incident window."),
        ("MEMORY EXHAUSTION", "Host RAM average > 85% indicating memory leak or cache exhaustion."),
        ("INTERNAL SERVER ERROR", "HTTP 5xx responses exceed 30% of total check volume."),
        ("SEVERE LATENCY SPIKE", "Average response latency exceeds warning/critical threshold limits.")
    ]
    for r_title, r_desc in rules:
        p1 = tf.add_paragraph()
        p1.text = f"\n• {r_title}"
        p1.font.size = Pt(10)
        p1.font.bold = True
        p1.font.color.rgb = C_RUST
        p2 = tf.add_paragraph()
        p2.text = f"  {r_desc}"
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = C_MUTED

    # Right: Evidence Schema Card
    r_box = s6.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(7.8), Inches(2.3), Inches(4.7), Inches(4.4))
    r_box.fill.solid()
    r_box.fill.fore_color.rgb = C_RUST_BG
    r_box.line.color.rgb = C_RUST
    r_box.line.width = Pt(1.5)

    tb_r = s6.shapes.add_textbox(Inches(8.0), Inches(2.4), Inches(4.3), Inches(4.1))
    tf_r = tb_r.text_frame
    p = tf_r.paragraphs[0]
    p.text = "EVIDENCE DELIVERED TO OPERATOR"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = C_DARK

    ev_items = [
        ("\nEvent State", "ACTIVE / RESOLVED status tracking"),
        ("\nTop Candidate", "Ranked primary failure contributor"),
        ("\nDetection Evidence", "Isolation Forest score & threshold rule"),
        ("\nCorrelated Context", "W3C trace IDs, socket error logs, peak CPU"),
        ("\nConfidence Note", "Separates internal faults from black-box external cloud dependencies")
    ]
    for k, v in ev_items:
        p1 = tf_r.add_paragraph()
        p1.text = f"{k}: {v}"
        p1.font.size = Pt(9.5)
        p1.font.bold = True if "State" in k or "Candidate" in k else False
        p1.font.color.rgb = C_DARK

    # ==========================================
    # SLIDE 7: 07 — METHODOLOGY & TESTBED
    # ==========================================
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "07", "Methodology", "07")
    add_titles(s7, "Controlled validation & public benchmarks.", 
               "Design Science Research methodology with rigorous point-wise evaluation without artificial point adjustment.")

    col1 = s7.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(2.3), Inches(5.7), Inches(4.3))
    col1.fill.solid()
    col1.fill.fore_color.rgb = C_CARD_BG
    col1.line.color.rgb = C_CARD_BORDER
    tb1 = s7.shapes.add_textbox(Inches(1.0), Inches(2.5), Inches(5.3), Inches(3.9))
    tf1 = tb1.text_frame
    p = tf1.paragraphs[0]
    p.text = "TRACK 1: CONTROLLED WORKLOAD"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = C_RUST
    p_sub = tf1.add_paragraph()
    p_sub.text = "Repeatable API Failure Injections (Seed: 20261125)\n"
    p_sub.font.size = Pt(10)
    p_sub.font.color.rgb = C_MUTED

    items1 = [
        "• 12,000 one-minute multivariate points",
        "• Chronological split: 5,000 train / 7,000 test",
        "• Daily (1440m) & hourly (60m) cyclic seasonality",
        "• 6 non-overlapping 60-min failure scenarios:",
        "    1. Latency Injection (P95 spike)",
        "    2. Elevated HTTP 5xx Error Burst",
        "    3. Gateway Timeout Surge",
        "    4. Host Resource Saturation (CPU burn)",
        "    5. Slow External Black-Box Dependency",
        "    6. Combined Dependency & Timeout Failure"
    ]
    for it in items1:
        p = tf1.add_paragraph()
        p.text = it
        p.font.size = Pt(9.5)
        p.font.color.rgb = C_DARK

    col2 = s7.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.8), Inches(2.3), Inches(5.7), Inches(4.3))
    col2.fill.solid()
    col2.fill.fore_color.rgb = C_CARD_BG
    col2.line.color.rgb = C_CARD_BORDER
    tb2 = s7.shapes.add_textbox(Inches(7.0), Inches(2.5), Inches(5.3), Inches(3.9))
    tf2 = tb2.text_frame
    p = tf2.paragraphs[0]
    p.text = "TRACK 2: SERVER MACHINE DATASET"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = C_DARK
    p_sub = tf2.add_paragraph()
    p_sub.text = "Public Multivariate Anomaly Benchmark (SMD)\n"
    p_sub.font.size = Pt(10)
    p_sub.font.color.rgb = C_MUTED

    items2 = [
        "• Source: Internet enterprise cluster (Su et al., 2019)",
        "• 38 continuous numerical metric dimensions",
        "• 5,000 training points / 5,000 test points",
        "• 4.16% anomaly density (208 labeled points)",
        "• Strict point-wise evaluation (no point adjustment)",
        "• Evaluated against PCA reconstruction error baseline (Alves et al., 2026)",
        "• Verifies behavior on high-dimensional telemetry"
    ]
    for it in items2:
        p = tf2.add_paragraph()
        p.text = it
        p.font.size = Pt(9.5)
        p.font.color.rgb = C_DARK

    # ==========================================
    # SLIDE 8: 08 — EXPERIMENTAL RESULTS
    # ==========================================
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "08", "Experimental Results", "08")
    add_titles(s8, "Faster detection, explainable diagnosis.", 
               "Quantitative validation proves earlier detection on gradual degradation and 100% root-cause attribution accuracy.")

    # 4 Stat Cards Top
    stat_cards = [
        ("3.50 min", "ML MTTD", "3x faster than thresholds (11.83 min) on degradation"),
        ("100%", "RCA ACCURACY", "Top-1 feature attribution across all 6 scenarios"),
        ("0.0075", "LOW FPR", "Minimal false alarm fatigue during normal traffic"),
        ("0.052 ms", "INFERENCE SPEED", "Ultra-lightweight per-point scoring duration")
    ]
    for i, (val, title, sub) in enumerate(stat_cards):
        left_pos = Inches(0.8 + i * 2.95)
        box = s8.shapes.add_shape(MSO_SHAPE.RECTANGLE, left_pos, Inches(2.3), Inches(2.8), Inches(1.5))
        box.fill.solid()
        box.fill.fore_color.rgb = C_RUST_BG if i == 0 else C_CARD_BG
        box.line.color.rgb = C_RUST if i == 0 else C_CARD_BORDER
        box.line.width = Pt(1.5)

        tb = s8.shapes.add_textbox(left_pos + Inches(0.1), Inches(2.4), Inches(2.6), Inches(1.3))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = val
        p.font.size = Pt(22)
        p.font.bold = True
        p.font.color.rgb = C_RUST if i == 0 else C_DARK

        p2 = tf.add_paragraph()
        p2.text = title
        p2.font.size = Pt(10)
        p2.font.bold = True
        p2.font.color.rgb = C_DARK

        p3 = tf.add_paragraph()
        p3.text = sub
        p3.font.size = Pt(8.5)
        p3.font.color.rgb = C_MUTED

    # Bottom Table: Table 5.2 & 5.3
    table_box = s8.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(4.0), Inches(11.7), Inches(2.9))
    table_box.fill.solid()
    table_box.fill.fore_color.rgb = C_CARD_BG
    table_box.line.color.rgb = C_CARD_BORDER

    tb_tab = s8.shapes.add_textbox(Inches(1.0), Inches(4.1), Inches(11.3), Inches(2.7))
    tf_t = tb_tab.text_frame
    p = tf_t.paragraphs[0]
    p.text = "CONTROLLED-WORKLOAD DETECTION RESULTS (TABLE 5.2 & TABLE 5.3 SUMMARY)"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = C_DARK

    t_rows = [
        f"{'Metric':<25} {'Isolation Forest':<20} {'Fixed Threshold Baseline':<25} {'Operational Interpretation'}",
        "-" * 100,
        f"{'True Positives (TP)':<25} {'118':<20} {'279':<25} {'Thresholds trigger 100% on cliff breaches'}",
        f"{'False Positives (FP)':<25} {'50':<20} {'0':<25} {'Conservative ML threshold captures early drift'}",
        f"{'Precision':<25} {'0.702':<20} {'1.000':<25} {'Baseline is exact for pre-coded limit breaches'}",
        f"{'Recall':<25} {'0.328':<20} {'0.775':<25} {'Point-wise recall without point adjustment'}",
        f"{'Mean Time To Detect':<25} {'3.50 minutes':<20} {'11.83 minutes':<25} {'ML catches gradual ramps 3x faster'}",
        f"{'RCA Top-1 Attribution':<25} {'6 / 6 (100%)':<20} {'N/A (Rules only)':<25} {'Ranks correct primary failure feature'}"
    ]
    for r in t_rows:
        p = tf_t.add_paragraph()
        p.text = r
        p.font.size = Pt(9)
        p.font.name = "Consolas"
        p.font.color.rgb = C_DARK

    # ==========================================
    # SLIDE 9: 09 — CONTRIBUTION & CONCLUSION
    # ==========================================
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "09", "Contribution", "09")
    add_titles(s9, "Enterprise-grade intelligent APM.", 
               "An explainable, vendor-neutral monitoring solution delivering proactive detection and root-cause localization.")

    contribs = [
        ("DETECT", "Dynamic Multivariate Anomaly Detection", 
         "Flags complex multi-signal degradation before hard manual limits breach, achieving a Mean Time to Detect of 3.50 minutes (3x faster than threshold baselines)."),
        ("EXPLAIN", "Multimodal Root Cause Localization", 
         "Correlates W3C traces, error logs, and metrics to achieve 100% Top-1 feature attribution, providing actionable evidence without assuming internal cloud provider access."),
        ("PROTECT", "Governed Hybrid Architecture", 
         "Combines unsupervised Isolation Forest with robust statistical fallbacks, eliminating the cold-start vulnerability on newly deployed enterprise services.")
    ]

    for i, (head, sub, desc) in enumerate(contribs):
        top_pos = Inches(2.3 + i * 1.35)
        box = s9.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), top_pos, Inches(11.7), Inches(1.15))
        box.fill.solid()
        box.fill.fore_color.rgb = C_CARD_BG if i != 0 else C_RUST_BG
        box.line.color.rgb = C_CARD_BORDER if i != 0 else C_RUST
        box.line.width = Pt(1.5)

        tb = s9.shapes.add_textbox(Inches(1.1), top_pos + Inches(0.12), Inches(11.1), Inches(0.9))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = f"{head} — {sub.upper()}"
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = C_RUST if i == 0 else C_DARK

        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(10.5)
        p2.font.color.rgb = C_MUTED

    # Thank you footer
    tb_ty = s9.shapes.add_textbox(Inches(0.8), Inches(6.5), Inches(11.7), Inches(0.5))
    p = tb_ty.text_frame.paragraphs[0]
    p.text = "THANK YOU  ·  QUESTIONS & ANSWERS"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_RUST

    output_path = os.path.join(os.path.dirname(__file__), "APM_Project_Presentation.pptx")
    prs.save(output_path)
    print(f"[SUCCESS] PowerPoint generated successfully: {output_path}")

if __name__ == "__main__":
    create_deck()
