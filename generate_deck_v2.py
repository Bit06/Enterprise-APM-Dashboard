import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def build_v2_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Theme Colors matching Covenant University reference style
    C_BG = RGBColor(255, 255, 255)
    C_DARK = RGBColor(18, 18, 18)
    C_RUST = RGBColor(194, 65, 12)       # Accent burnt orange / crimson
    C_MUTED = RGBColor(100, 116, 139)    # Slate gray for subtitles & body
    C_CARD_BG = RGBColor(248, 250, 252)  # Soft background for cards
    C_CARD_BORDER = RGBColor(226, 232, 240)
    C_RUST_BG = RGBColor(254, 242, 242)  # Soft warm highlight card
    C_WHITE = RGBColor(255, 255, 255)

    TOTAL_SLIDES = "14"

    def add_header(slide, num_str, name_str, cur_slide):
        # Section category left
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.45), Inches(8.0), Inches(0.35))
        p = tb.text_frame.paragraphs[0]
        p.text = f"{num_str} — {name_str.upper()}"
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = C_DARK
        p.font.name = "Arial"

        # Counter right
        tb2 = slide.shapes.add_textbox(Inches(10.5), Inches(0.45), Inches(2.0), Inches(0.35))
        p2 = tb2.text_frame.paragraphs[0]
        p2.alignment = PP_ALIGN.RIGHT
        p2.text = f"{cur_slide} / {TOTAL_SLIDES}"
        p2.font.size = Pt(11)
        p2.font.bold = True
        p2.font.color.rgb = C_MUTED
        p2.font.name = "Arial"

    def add_hero(slide, headline, subtitle=""):
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(11.7), Inches(0.6))
        p = tb.text_frame.paragraphs[0]
        p.text = headline
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = C_DARK
        p.font.name = "Arial"

        if subtitle:
            tb_sub = slide.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(0.45))
            p_sub = tb_sub.text_frame.paragraphs[0]
            p_sub.text = subtitle
            p_sub.font.size = Pt(13)
            p_sub.font.color.rgb = C_MUTED
            p_sub.font.name = "Arial"

    # ============================================================
    # SLIDE 0: TITLE SLIDE
    # ============================================================
    s0 = prs.slides.add_slide(blank_layout)
    tb = s0.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(11.7), Inches(0.4))
    p = tb.text_frame.paragraphs[0]
    p.text = "EIE · COMPUTER ENGINEERING  |  COVENANT UNIVERSITY"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = C_MUTED
    p.font.name = "Arial"

    tb_t = s0.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.7), Inches(2.0))
    p = tb_t.text_frame.paragraphs[0]
    p.text = "INTELLIGENT APM"
    p.font.size = Pt(52)
    p.font.bold = True
    p.font.color.rgb = C_DARK
    p.font.name = "Arial"

    p2 = tb_t.text_frame.add_paragraph()
    p2.text = "Development of an Intelligent API & Application Performance Monitoring System for Enterprise Services"
    p2.font.size = Pt(16)
    p2.font.color.rgb = C_RUST
    p2.font.name = "Arial"

    # Student metadata
    tb_st = s0.shapes.add_textbox(Inches(0.8), Inches(5.4), Inches(5.0), Inches(1.3))
    p = tb_st.text_frame.paragraphs[0]
    p.text = "CANDIDATE"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = C_MUTED
    p = tb_st.text_frame.add_paragraph()
    p.text = "[CANDIDATE NAME]"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_DARK
    p = tb_st.text_frame.add_paragraph()
    p.text = "Matriculation: [MATRIC NO]"
    p.font.size = Pt(12)
    p.font.color.rgb = C_MUTED

    # Supervisor metadata
    tb_sp = s0.shapes.add_textbox(Inches(6.8), Inches(5.4), Inches(5.0), Inches(1.3))
    p = tb_sp.text_frame.paragraphs[0]
    p.text = "SUPERVISOR"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = C_MUTED
    p = tb_sp.text_frame.add_paragraph()
    p.text = "Dr. [SUPERVISOR NAME]"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_DARK
    p = tb_sp.text_frame.add_paragraph()
    p.text = "Department of Electrical & Information Engineering"
    p.font.size = Pt(12)
    p.font.color.rgb = C_MUTED

    # ============================================================
    # SLIDE 1: 01 — THE PROBLEM
    # ============================================================
    s1 = prs.slides.add_slide(blank_layout)
    add_header(s1, "01", "The Problem", "01")
    add_hero(s1, "Fragmented signals, silent cascades.", 
             "Enterprise applications depend on interconnected microservices, databases, and third-party APIs. A single dependency delay cascades silently across the service.")

    p_cards = [
        ("CASCADE FAILURES", "Downstream bottlenecks in a database or third-party service manifest as mysterious HTTP 500 crashes in unrelated upstream APIs."),
        ("FRAGMENTED TOOLS", "Metrics, application logs, and distributed traces reside in separate tools, requiring tedious manual correlation during outages."),
        ("BLACK-BOX APIS", "Third-party cloud dependencies (AWS, Azure, payment gateways) cannot be inspected internally; only client-side duration and timeouts are measurable.")
    ]
    for i, (title, desc) in enumerate(p_cards):
        left_pos = Inches(0.8 + i * 4.0)
        box = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, left_pos, Inches(2.3), Inches(3.7), Inches(4.5))
        box.fill.solid()
        box.fill.fore_color.rgb = C_CARD_BG if i != 0 else C_RUST_BG
        box.line.color.rgb = C_CARD_BORDER if i != 0 else C_RUST
        box.line.width = Pt(1.5)

        tb = s1.shapes.add_textbox(left_pos + Inches(0.2), Inches(2.6), Inches(3.3), Inches(3.9))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = C_RUST if i == 0 else C_DARK

        p2 = tf.add_paragraph()
        p2.text = f"\n{desc}"
        p2.font.size = Pt(11)
        p2.font.color.rgb = C_MUTED

    # ============================================================
    # SLIDE 2: 02 — MOTIVATION
    # ============================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "02", "Motivation", "02")
    add_hero(s2, "The observability gap.", 
             "Enterprises are trapped between brittle manual rules and proprietary, million-naira monitoring suites.")

    m_cols = [
        ("TRADITIONAL MONITORING", "Nagios / Zabbix / Static Thresholds", [
            ("MECHANISM", "Hardcoded threshold limits (e.g. latency > 500ms)."),
            ("LIMITATIONS", "High false alarms on legitimate traffic surges; blind to gradual degradation; zero context."),
            ("COLD START", "Requires tedious manual recalibration for every new route."),
            ("DIAGNOSIS", "Alerts that a limit breached; leaves root cause to human guesswork.")
        ], C_CARD_BG, C_CARD_BORDER),
        ("PROPRIETARY APM SUITES", "Datadog / Dynatrace / New Relic", [
            ("MECHANISM", "Automated full-stack cloud analytics and tracing agents."),
            ("LIMITATIONS", "Millions of naira in annual subscription fees; vendor lock-in; proprietary formats."),
            ("COLD START", "Deep models require huge historical datasets and fail on newly deployed services."),
            ("DIAGNOSIS", "Opaque cloud processing; black-box dependencies remain unverified.")
        ], C_RUST_BG, C_RUST)
    ]
    for i, (head, sub, items, bg_c, b_c) in enumerate(m_cols):
        left_pos = Inches(0.8 + i * 6.0)
        box = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, left_pos, Inches(2.2), Inches(5.7), Inches(4.3))
        box.fill.solid()
        box.fill.fore_color.rgb = bg_c
        box.line.color.rgb = b_c
        box.line.width = Pt(1.5)

        tb = s2.shapes.add_textbox(left_pos + Inches(0.3), Inches(2.4), Inches(5.1), Inches(3.9))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = head
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = C_DARK

        p_s = tf.add_paragraph()
        p_s.text = sub
        p_s.font.size = Pt(10)
        p_s.font.color.rgb = C_MUTED

        for lbl, txt in items:
            p1 = tf.add_paragraph()
            p1.text = f"\n{lbl}: "
            p1.font.size = Pt(10)
            p1.font.bold = True
            p1.font.color.rgb = C_RUST if b_c == C_RUST else C_DARK
            p2 = tf.add_paragraph()
            p2.text = txt
            p2.font.size = Pt(10)
            p2.font.color.rgb = C_DARK

    tb_f = s2.shapes.add_textbox(Inches(0.8), Inches(6.7), Inches(11.7), Inches(0.4))
    p = tb_f.text_frame.paragraphs[0]
    p.text = "Our system provides the missing hybrid quadrant: open-standard telemetry pairing unsupervised ML with a statistical safety net."
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = C_DARK

    # ============================================================
    # SLIDE 3: 03 — OBJECTIVES
    # ============================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "03", "Objectives", "03")
    add_hero(s3, "Aim & specific objectives.", 
             "Design, implement, and validate an intelligent APM prototype that detects anomalous API behavior and provides explainable indications of likely causes.")

    objs = [
        ("01", "Analyze Observability Gaps & Requirements", "Synthesize existing APM, time-series anomaly detection, and benchmark flaws to formulate requirements for cold-start mitigation."),
        ("02", "Design OpenTelemetry Telemetry Pipeline", "Architect a vendor-neutral pipeline collecting API RED metrics (Rate, Errors, Duration), traces, and host signals (CPU/RAM)."),
        ("03", "Implement Multivariate Anomaly Detection", "Train a 6-feature Isolation Forest with RobustScaler and deploy an automated statistical threshold fallback for cold start."),
        ("04", "Develop Multimodal Root Cause Analysis (RCA)", "Correlate anomalies with W3C trace context, socket error logs, and resource metrics to generate ranked diagnostic hints (Table 5.4)."),
        ("05", "Evaluate Empirically Against Baseline", "Benchmark against fixed-threshold monitoring using a 12,000-point controlled workload and the public Server Machine Dataset (SMD).")
    ]
    for i, (num, headline, desc) in enumerate(objs):
        top_pos = Inches(2.2 + i * 0.95)
        n_box = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), top_pos, Inches(0.7), Inches(0.75))
        n_box.fill.solid()
        n_box.fill.fore_color.rgb = C_RUST
        n_box.line.fill.background()
        p = n_box.text_frame.paragraphs[0]
        p.text = num
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = C_WHITE

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

    # ============================================================
    # SLIDE 4: 04 — ARCHITECTURE
    # ============================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "04", "Architecture", "04")
    add_hero(s4, "What the system is.", 
             "A decoupled, vendor-neutral observability architecture that completely isolates analytics from the API request path.")

    stages = [
        ("STAGE 1 · COLLECTION", "Continuous Ingestion & Probing", [
            "• Synthetic Probes (APScheduler every 60s)",
            "• OpenTelemetry W3C Trace Headers (traceparent)",
            "• In-Memory Telemetry Queue (Queue.Queue)",
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

    # ============================================================
    # SLIDE 5: 05 — TELEMETRY & INGESTION
    # ============================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "05", "Telemetry & Ingestion", "05")
    add_hero(s5, "Vendor-neutral telemetry without overhead.", 
             "Combining OpenTelemetry distributed tracing with active health probing to capture complete transaction lifecycles.")

    tel_cards = [
        ("W3C TRACE CONTEXT", "End-to-End Request Stitching", 
         "• Generates W3C-compliant traceparent headers (00-<trace_id>-<span_id>-01).\n• Trace context propagates across microservice boundaries.\n• Binds high-frequency application logs directly to specific slow requests.\n• Replaces guesswork with distributed span timelines."),
        ("ACTIVE SYNTHETIC PROBES", "Continuous Endpoint Auditing", 
         "• Automated probes execute via APScheduler on configurable intervals (default: 60s).\n• Records round-trip duration, HTTP status code, and network exceptions.\n• Samples simulated host CPU and RAM utilization.\n• Pre-computes continuous UP/DOWN operational intervals for SLA math."),
        ("ASYNC BATCH INGESTION", "Zero Production Penalty", 
         "• Client middleware flushes batches asynchronously in background threads.\n• Telemetry queue decouples collection from database persistence.\n• Ingestion endpoint (/api/ingest) accepts high-throughput traffic without stalling user requests.")
    ]
    for i, (head, sub, desc) in enumerate(tel_cards):
        left_pos = Inches(0.8 + i * 4.0)
        box = s5.shapes.add_shape(MSO_SHAPE.RECTANGLE, left_pos, Inches(2.3), Inches(3.7), Inches(4.3))
        box.fill.solid()
        box.fill.fore_color.rgb = C_CARD_BG
        box.line.color.rgb = C_CARD_BORDER
        box.line.width = Pt(1.5)

        tb = s5.shapes.add_textbox(left_pos + Inches(0.2), Inches(2.5), Inches(3.3), Inches(3.9))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = head
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = C_RUST

        p_s = tf.add_paragraph()
        p_s.text = sub
        p_s.font.size = Pt(12)
        p_s.font.bold = True
        p_s.font.color.rgb = C_DARK

        p_b = tf.add_paragraph()
        p_b.text = f"\n{desc}"
        p_b.font.size = Pt(10)
        p_b.font.color.rgb = C_MUTED

    # ============================================================
    # SLIDE 6: 06 — THE DETECTION ENGINE
    # ============================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "06", "Detection Engine", "06")
    add_hero(s6, "Multivariate Isolation Forest.", 
             "Unsupervised anomaly detection across 6 simultaneous performance dimensions, isolating degradations before hard limits breach.")

    det_cards = [
        ("THE 6D FEATURE VECTOR", "Comprehensive Signal Set", 
         "Evaluates metrics simultaneously:\n• Request Rate (RPS)\n• P95 Response Latency\n• P99 Response Latency\n• HTTP 5xx Error Rate\n• Host CPU Utilization\n• Host RAM Utilization\n\nCatches subtle multi-signal interactions that 1D static rules miss."),
        ("HOW ISOLATION FOREST WORKS", "Partition-Depth Principle", 
         "• 300 isolation trees partition feature space randomly.\n• Anomalies are few and different, isolating in very few cuts (low tree depth).\n• Normal traffic clusters tightly, requiring many partitions to isolate.\n• Evaluates points by score: values below empirical threshold trigger alerts."),
        ("LEAKAGE-FREE SCALING", "Mathematical Rigor", 
         "• Uses RobustScaler based on medians and Interquartile Ranges (IQR).\n• Immune to extreme outage outliers.\n• Fitted strictly on chronological training intervals to prevent data leakage.\n• Sub-millisecond scoring duration (0.052 ms per point).")
    ]
    for i, (head, sub, desc) in enumerate(det_cards):
        left_pos = Inches(0.8 + i * 4.0)
        box = s6.shapes.add_shape(MSO_SHAPE.RECTANGLE, left_pos, Inches(2.3), Inches(3.7), Inches(4.3))
        box.fill.solid()
        box.fill.fore_color.rgb = C_CARD_BG
        box.line.color.rgb = C_CARD_BORDER
        box.line.width = Pt(1.5)

        tb = s6.shapes.add_textbox(left_pos + Inches(0.2), Inches(2.5), Inches(3.3), Inches(3.9))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = head
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = C_DARK

        p_s = tf.add_paragraph()
        p_s.text = sub
        p_s.font.size = Pt(12)
        p_s.font.bold = True
        p_s.font.color.rgb = C_RUST

        p_b = tf.add_paragraph()
        p_b.text = f"\n{desc}"
        p_b.font.size = Pt(10)
        p_b.font.color.rgb = C_MUTED

    # ============================================================
    # SLIDE 7: 07 — COLD-START MITIGATION
    # ============================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "07", "Cold-Start Handling", "07")
    add_hero(s7, "Eliminating day-one deployment blind spots.", 
             "A governed hybrid architecture that protects newly deployed endpoints until historical training data accumulates.")

    cs_left = s7.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(2.3), Inches(5.7), Inches(4.3))
    cs_left.fill.solid()
    cs_left.fill.fore_color.rgb = C_CARD_BG
    cs_left.line.color.rgb = C_CARD_BORDER
    tb_l = s7.shapes.add_textbox(Inches(1.0), Inches(2.5), Inches(5.3), Inches(3.9))
    tf_l = tb_l.text_frame
    p = tf_l.paragraphs[0]
    p.text = "THE COLD-START CHALLENGE"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = C_DARK
    p_s = tf_l.add_paragraph()
    p_s.text = "Why pure machine learning fails in enterprise operations:\n"
    p_s.font.size = Pt(10)
    p_s.font.color.rgb = C_MUTED

    cs_bullets = [
        "• Newly deployed microservices have zero historical telemetry.",
        "• Unsupervised models without sufficient baseline data produce high false alarms or complete detection failure.",
        "• Frequent microservice redeployments cause concept drift.",
        "• Literature survey (Tuli et al., 2022; Notaro et al., 2021) identifies cold start as the #1 barrier to enterprise ML adoption."
    ]
    for b in cs_bullets:
        p = tf_l.add_paragraph()
        p.text = b
        p.font.size = Pt(10)
        p.font.color.rgb = C_DARK

    cs_right = s7.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.8), Inches(2.3), Inches(5.7), Inches(4.3))
    cs_right.fill.solid()
    cs_right.fill.fore_color.rgb = C_RUST_BG
    cs_right.line.color.rgb = C_RUST
    cs_right.line.width = Pt(1.5)
    tb_r = s7.shapes.add_textbox(Inches(7.0), Inches(2.5), Inches(5.3), Inches(3.9))
    tf_r = tb_r.text_frame
    p = tf_r.paragraphs[0]
    p.text = "OUR HYBRID SAFEGUARD SOLUTION"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = C_RUST
    p_s = tf_r.add_paragraph()
    p_s.text = "Automated state transition logic in ml_engine.py:\n"
    p_s.font.size = Pt(10)
    p_s.font.color.rgb = C_MUTED

    sol_bullets = [
        "1. Cold-Start State (< 25 Samples):",
        "   • Automatically activates robust rolling medians and IQRs.",
        "   • Enforces operational safety thresholds (Warn/Crit latency, CPU > 85%, Error rate > 10%).",
        "   • Tags metadata as 'state: cold_start' for auditable traceability.",
        "\n2. Seamless Model Transition (>= 25 Samples):",
        "   • Fits RobustScaler and trains Multivariate Isolation Forest.",
        "   • Derives empirical score threshold from training percentile.",
        "   • Retains threshold rules as a permanent secondary safety net."
    ]
    for b in sol_bullets:
        p = tf_r.add_paragraph()
        p.text = b
        p.font.size = Pt(9.5)
        p.font.color.rgb = C_DARK

    # ============================================================
    # SLIDE 8: 08 — ROOT CAUSE ANALYSIS
    # ============================================================
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "08", "Root Cause Analysis", "08")
    add_hero(s8, "Explainable evidence, not black-box guesses.", 
               "Correlating anomalies across metrics, socket error logs, and W3C trace identifiers according to the Table 5.4 diagnostic schema.")

    left_box = s8.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(2.3), Inches(6.8), Inches(4.4))
    left_box.fill.solid()
    left_box.fill.fore_color.rgb = C_CARD_BG
    left_box.line.color.rgb = C_CARD_BORDER

    tb = s8.shapes.add_textbox(Inches(1.0), Inches(2.4), Inches(6.4), Inches(4.1))
    tf = tb.text_frame
    p = tf.paragraphs[0]
    p.text = "DIAGNOSTIC TRIGGER RULES (TABLE 5.4 SCHEMA)"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = C_DARK

    rules = [
        ("SERVICE OFFLINE", "Status code is None / socket refused in >= 50% checks. Evidence: Socket connection error strings."),
        ("CPU SATURATION", "Host CPU average > 85% or peak > 92%. Evidence: High CPU utilization across incident window."),
        ("MEMORY EXHAUSTION", "Host RAM average > 85%. Evidence: Memory leak / exhaustion pattern."),
        ("INTERNAL SERVER ERROR", "HTTP 5xx responses exceed 30% of checks. Evidence: Server stack/error responses."),
        ("SEVERE LATENCY SPIKE", "Response latency exceeds warn/critical limits. Evidence: Upstream bottleneck timing.")
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

    r_box = s8.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(7.8), Inches(2.3), Inches(4.7), Inches(4.4))
    r_box.fill.solid()
    r_box.fill.fore_color.rgb = C_RUST_BG
    r_box.line.color.rgb = C_RUST
    r_box.line.width = Pt(1.5)

    tb_r = s8.shapes.add_textbox(Inches(8.0), Inches(2.4), Inches(4.3), Inches(4.1))
    tf_r = tb_r.text_frame
    p = tf_r.paragraphs[0]
    p.text = "EVIDENCE DELIVERED TO OPERATOR"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = C_DARK

    ev_items = [
        ("\nEvent State", "ACTIVE / RESOLVED lifecycle tracking"),
        ("\nTop Candidate", "Ranked primary failure contributor"),
        ("\nDetection Evidence", "Isolation Forest score & threshold rule"),
        ("\nCorrelated Context", "W3C trace IDs, socket error logs, peak CPU"),
        ("\nConfidence Note", "Distinguishes client-side observations from unprovable cloud provider internal causes")
    ]
    for k, v in ev_items:
        p1 = tf_r.add_paragraph()
        p1.text = f"{k}: {v}"
        p1.font.size = Pt(9.5)
        p1.font.bold = True if "State" in k or "Candidate" in k else False
        p1.font.color.rgb = C_DARK

    # ============================================================
    # SLIDE 9: 09 — THE DASHBOARD & ALERTING
    # ============================================================
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "09", "Dashboard & Alerts", "09")
    add_hero(s9, "Real-time visibility & operational alerting.", 
             "A unified web dashboard providing executive KPIs, latency percentile charts, interactive RCA, and deduplicated notifications.")

    dash_cards = [
        ("EXECUTIVE SLA SUMMARY", "High-Level Health Cards", 
         "• System Availability % (Target: >= 99.9%)\n• SLA Compliance Status (MET / BREACHED)\n• Mean Time To Recovery (MTTR in minutes)\n• Mean Time Between Failures (MTBF in hours)\n• Active Incident Counter"),
        ("REAL-TIME CHART.JS GRIDS", "Interactive Telemetry Charts", 
         "• Live response time time-series chart.\n• Red Anomaly Markers highlight ML detections in real time.\n• Status Badges: Green (Up), Amber (Degraded), Red (Down).\n• Deep-dive endpoint inspector with historical latency distributions."),
        ("ACTIONABLE ALERT WORKFLOW", "Deduplication & Multi-Channel", 
         "• Intelligent alert deduplication prevents storm fatigue.\n• Dispatches formatted notifications to Microsoft Teams webhooks & SMTP Email.\n• Tracks continuous SLO error budget burn rates.\n• Interactive 'Analyze Root Cause' modal in UI.")
    ]
    for i, (head, sub, desc) in enumerate(dash_cards):
        left_pos = Inches(0.8 + i * 4.0)
        box = s9.shapes.add_shape(MSO_SHAPE.RECTANGLE, left_pos, Inches(2.3), Inches(3.7), Inches(4.3))
        box.fill.solid()
        box.fill.fore_color.rgb = C_CARD_BG
        box.line.color.rgb = C_CARD_BORDER
        box.line.width = Pt(1.5)

        tb = s9.shapes.add_textbox(left_pos + Inches(0.2), Inches(2.5), Inches(3.3), Inches(3.9))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = head
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = C_DARK

        p_s = tf.add_paragraph()
        p_s.text = sub
        p_s.font.size = Pt(12)
        p_s.font.bold = True
        p_s.font.color.rgb = C_RUST

        p_b = tf.add_paragraph()
        p_b.text = f"\n{desc}"
        p_b.font.size = Pt(10)
        p_b.font.color.rgb = C_MUTED

    # ============================================================
    # SLIDE 10: 10 — METHODOLOGY & TESTBED
    # ============================================================
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "10", "Methodology", "10")
    add_hero(s10, "Controlled validation & public benchmarks.", 
             "Design Science Research (DSR) methodology with strict point-wise evaluation without artificial point adjustment.")

    col1 = s10.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(2.3), Inches(5.7), Inches(4.3))
    col1.fill.solid()
    col1.fill.fore_color.rgb = C_CARD_BG
    col1.line.color.rgb = C_CARD_BORDER
    tb1 = s10.shapes.add_textbox(Inches(1.0), Inches(2.5), Inches(5.3), Inches(3.9))
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
        "• 12,000 one-minute multivariate observations",
        "• Chronological split: 5,000 train / 7,000 test points",
        "• Daily (1440m) & hourly (60m) cyclic seasonality",
        "• 6 non-overlapping 60-min failure scenarios (360 anomaly points):",
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

    col2 = s10.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.8), Inches(2.3), Inches(5.7), Inches(4.3))
    col2.fill.solid()
    col2.fill.fore_color.rgb = C_CARD_BG
    col2.line.color.rgb = C_CARD_BORDER
    tb2 = s10.shapes.add_textbox(Inches(7.0), Inches(2.5), Inches(5.3), Inches(3.9))
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
        "• Evaluated against PCA reconstruction baseline (Alves et al., 2026)",
        "• Verifies model scalability on high-dimensional telemetry"
    ]
    for it in items2:
        p = tf2.add_paragraph()
        p.text = it
        p.font.size = Pt(9.5)
        p.font.color.rgb = C_DARK

    # ============================================================
    # SLIDE 11: 11 — EXPERIMENTAL RESULTS (TABLE 5.2)
    # ============================================================
    s11 = prs.slides.add_slide(blank_layout)
    add_header(s11, "11", "Detection Results", "11")
    add_hero(s11, "Earlier detection of gradual degradation.", 
             "Isolation Forest achieved a 3x faster Mean Time to Detect on gradual ramps, validating the hybrid architecture.")

    stat_cards = [
        ("3.50 min", "ML MTTD", "Detects gradual degradation 3x faster than thresholds (11.83 min)"),
        ("100%", "RCA ACCURACY", "Top-1 feature attribution across all 6 failure types"),
        ("0.0075", "LOW FPR", "Minimal false alarm fatigue during normal traffic"),
        ("0.052 ms", "INFERENCE SPEED", "Ultra-lightweight per-point scoring duration")
    ]
    for i, (val, title, sub) in enumerate(stat_cards):
        left_pos = Inches(0.8 + i * 2.95)
        box = s11.shapes.add_shape(MSO_SHAPE.RECTANGLE, left_pos, Inches(2.2), Inches(2.8), Inches(1.4))
        box.fill.solid()
        box.fill.fore_color.rgb = C_RUST_BG if i == 0 else C_CARD_BG
        box.line.color.rgb = C_RUST if i == 0 else C_CARD_BORDER
        box.line.width = Pt(1.5)

        tb = s11.shapes.add_textbox(left_pos + Inches(0.1), Inches(2.3), Inches(2.6), Inches(1.2))
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

    table_box = s11.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(3.8), Inches(11.7), Inches(3.2))
    table_box.fill.solid()
    table_box.fill.fore_color.rgb = C_CARD_BG
    table_box.line.color.rgb = C_CARD_BORDER

    tb_tab = s11.shapes.add_textbox(Inches(1.0), Inches(3.9), Inches(11.3), Inches(3.0))
    tf_t = tb_tab.text_frame
    p = tf_t.paragraphs[0]
    p.text = "TABLE 5.2: CONTROLLED-WORKLOAD DETECTION RESULTS (12,000 OBSERVATIONS)"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = C_DARK

    t_rows = [
        f"{'Metric':<25} {'Isolation Forest':<20} {'Fixed Threshold Baseline':<25} {'Operational Finding'}",
        "-" * 100,
        f"{'True Positives (TP)':<25} {'118':<20} {'279':<25} {'Thresholds trigger 100% on cliff breaches'}",
        f"{'False Positives (FP)':<25} {'50':<20} {'0':<25} {'Conservative ML captures early subtle drift'}",
        f"{'True Negatives (TN)':<25} {'6,590':<20} {'6,640':<25} {'High specificity maintained on normal traffic'}",
        f"{'False Negatives (FN)':<25} {'242':<20} {'81':<25} {'Strict point-wise scoring without point adjustment'}",
        f"{'Precision':<25} {'0.702':<20} {'1.000':<25} {'Thresholds exact on pre-coded limits'}",
        f"{'Recall':<25} {'0.328':<20} {'0.775':<25} {'ML catches initial onset; thresholds catch full event'}",
        f"{'Mean Time To Detect':<25} {'3.50 minutes':<20} {'11.83 minutes':<25} {'ML alerts 3x faster than static limits'}"
    ]
    for r in t_rows:
        p = tf_t.add_paragraph()
        p.text = r
        p.font.size = Pt(9)
        p.font.name = "Consolas"
        p.font.color.rgb = C_DARK

    # ============================================================
    # SLIDE 12: 12 — DIAGNOSTIC & BENCHMARK VALIDATION
    # ============================================================
    s12 = prs.slides.add_slide(blank_layout)
    add_header(s12, "12", "Benchmark & RCA", "12")
    add_hero(s12, "100% root-cause attribution & SMD benchmark.", 
             "Explanatory ranking correctly isolates the injected root cause in every scenario; SMD proves high-dimensional behavior.")

    b_left = s12.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(2.2), Inches(6.8), Inches(4.8))
    b_left.fill.solid()
    b_left.fill.fore_color.rgb = C_CARD_BG
    b_left.line.color.rgb = C_CARD_BORDER
    tb_bl = s12.shapes.add_textbox(Inches(1.0), Inches(2.3), Inches(6.4), Inches(4.5))
    tf_bl = tb_bl.text_frame
    p = tf_bl.paragraphs[0]
    p.text = "TABLE 5.3: PER-SCENARIO DETECTION DELAYS & RANKED EVIDENCE"
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = C_DARK

    sc_rows = [
        f"{'Scenario':<28} {'IF Delay':<10} {'TH Delay':<10} {'Ranked Top Evidence'}",
        "-" * 65,
        f"{'Latency Injection':<28} {'2 min':<10} {'17 min':<10} {'api_p95_latency (Rank #1)'}",
        f"{'Elevated HTTP 5xx':<28} {'14 min':<10} {'0 min':<10} {'http_5xx_rate (Rank #1)'}",
        f"{'Timeouts':<28} {'0 min':<10} {'0 min':<10} {'timeout_rate (Rank #1)'}",
        f"{'Resource Pressure':<28} {'5 min':<10} {'32 min':<10} {'cpu_percent (Rank #1)'}",
        f"{'Slow External Dependency':<28} {'0 min':<10} {'22 min':<10} {'dependency_p95 (Rank #1)'}",
        f"{'Combined Dependency Failure':<28} {'0 min':<10} {'0 min':<10} {'timeout_rate (Rank #1)'}",
        "-" * 65,
        "Top-1 Attribution Accuracy: 6 / 6 (100%)",
        "Top-3 Attribution Accuracy: 6 / 6 (100%)"
    ]
    for sr in sc_rows:
        p = tf_bl.add_paragraph()
        p.text = sr
        p.font.size = Pt(8.5)
        p.font.name = "Consolas"
        p.font.color.rgb = C_RUST if "Attribution" in sr else C_DARK

    b_right = s12.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(7.8), Inches(2.2), Inches(4.7), Inches(4.8))
    b_right.fill.solid()
    b_right.fill.fore_color.rgb = C_RUST_BG
    b_right.line.color.rgb = C_RUST
    b_right.line.width = Pt(1.5)
    tb_br = s12.shapes.add_textbox(Inches(8.0), Inches(2.3), Inches(4.3), Inches(4.5))
    tf_br = tb_br.text_frame
    p = tf_br.paragraphs[0]
    p.text = "SERVER MACHINE DATASET (SMD)"
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = C_DARK

    smd_text = [
        "\n38-Dimensional Benchmark Results:",
        "• Model: Isolation Forest vs. PCA Baseline",
        "• True Positives: 37 (IF) vs. 208 (PCA)",
        "• False Positives: 224 (IF) vs. 224 (PCA)",
        "• Precision: 0.142 (IF) vs. 0.481 (PCA)",
        "• Recall: 0.178 (IF) vs. 1.000 (PCA)",
        "• F1-Score: 0.158 (IF) vs. 0.650 (PCA)",
        "\nKey Scientific Finding:",
        "Confirms Alves et al. (2026) and Xu et al. (2023): on high-dimensional non-axis-parallel anomalies, PCA/linear models remain strong competitors. This empirically justifies our hybrid monitoring model."
    ]
    for st in smd_text:
        p = tf_br.add_paragraph()
        p.text = st
        p.font.size = Pt(8.5)
        p.font.color.rgb = C_DARK

    # ============================================================
    # SLIDE 13: 13 — LIVE DEMO WORKFLOW
    # ============================================================
    s13 = prs.slides.add_slide(blank_layout)
    add_header(s13, "13", "System Demonstration", "13")
    add_hero(s13, "Live demonstration workflow.", 
             "A repeatable 3-step script proving baseline health, dynamic ML anomaly detection, and automated Root Cause Analysis.")

    demo_steps = [
        ("STEP 1 · NORMAL BASELINE", "Proving System Health", [
            "• Launch APM backend & dummy app.",
            "• Traffic generator sends 50 concurrent requests.",
            "• Dashboard shows steady green (Up) status.",
            "• Response times stable at ~5ms, global SLA > 99%."
        ]),
        ("STEP 2 · MACHINE LEARNING", "Proving Dynamic Detection", [
            "• Switch load generator to --mode latency_spike.",
            "• Response times climb toward 3000ms.",
            "• Red dots appear dynamically on Chart.js.",
            "• Proves faster detection (MTTD 3.5 min) before static limit breaches."
        ]),
        ("STEP 3 · ROOT CAUSE (RCA)", "Proving Explainability", [
            "• Stop the target dummy app (--mode kill).",
            "• Health status turns RED (Down).",
            "• Click endpoint -> 'Analyze Root Cause'.",
            "• RCA modal proves 'Service Offline' with 100% socket error logs and W3C trace IDs."
        ])
    ]
    for i, (title, sub, bullets) in enumerate(demo_steps):
        left_pos = Inches(0.8 + i * 4.0)
        box = s13.shapes.add_shape(MSO_SHAPE.RECTANGLE, left_pos, Inches(2.3), Inches(3.7), Inches(4.3))
        box.fill.solid()
        box.fill.fore_color.rgb = C_CARD_BG if i != 1 else C_RUST_BG
        box.line.color.rgb = C_CARD_BORDER if i != 1 else C_RUST
        box.line.width = Pt(1.5)

        tb = s13.shapes.add_textbox(left_pos + Inches(0.2), Inches(2.5), Inches(3.3), Inches(3.9))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = C_RUST if i == 1 else C_DARK

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

    # ============================================================
    # SLIDE 14: 14 — CONCLUSION
    # ============================================================
    s14 = prs.slides.add_slide(blank_layout)
    add_header(s14, "14", "Conclusion", "14")
    add_hero(s14, "Enterprise-grade intelligent APM.", 
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
        box = s14.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), top_pos, Inches(11.7), Inches(1.15))
        box.fill.solid()
        box.fill.fore_color.rgb = C_CARD_BG if i != 0 else C_RUST_BG
        box.line.color.rgb = C_CARD_BORDER if i != 0 else C_RUST
        box.line.width = Pt(1.5)

        tb = s14.shapes.add_textbox(Inches(1.1), top_pos + Inches(0.12), Inches(11.1), Inches(0.9))
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

    tb_ty = s14.shapes.add_textbox(Inches(0.8), Inches(6.5), Inches(11.7), Inches(0.5))
    p = tb_ty.text_frame.paragraphs[0]
    p.text = "THANK YOU  ·  QUESTIONS & ANSWERS"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_RUST

    out1 = os.path.join(os.path.dirname(__file__), "APM_Project_Presentation.pptx")
    out2 = os.path.join(os.path.dirname(__file__), "..", "APM_Project_Presentation.pptx")

    try:
        prs.save(out1)
        print(f"[SUCCESS] Saved to {out1}")
    except Exception as e:
        alt_path = os.path.join(os.path.dirname(__file__), "APM_Project_Presentation_V2.pptx")
        prs.save(alt_path)
        print(f"[NOTE] Main file locked ({e}). Saved to {alt_path}")

    try:
        prs.save(out2)
        print(f"[SUCCESS] Saved to {out2}")
    except Exception as e:
        print(f"[NOTE] Root save skipped ({e})")

if __name__ == "__main__":
    build_v2_presentation()
