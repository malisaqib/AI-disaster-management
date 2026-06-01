import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import date
from api import get, post, warm_up
from components import (
    inject_css, page_header, stat_card, data_table,
    severity_color, severity_badge, format_date, severity_to_color,
)

st.set_page_config(page_title="DisasterLink", page_icon="🚨", layout="wide")
inject_css()
page_header("DisasterLink Dashboard", "Disaster relief coordination · Pakistan")

# Wake the backend if the free host has spun down (shows a friendly message
# instead of red errors while it cold-starts).
if not st.session_state.get("backend_ready"):
    with st.spinner("Connecting to server… (free hosting may take up to a minute to wake up)"):
        if warm_up():
            st.session_state.backend_ready = True
        else:
            st.warning("The backend is starting up. Please wait a moment and refresh.")
            st.stop()

page = st.sidebar.selectbox(
    "Navigate",
    ["Dashboard", "3D Map", "Disasters", "Organizations", "Programs", "Incident Reports", "AI Assistant"],
)

# ─── Dashboard ───────────────────────────────────────────────────────────────
if page == "Dashboard":
    try:
        disasters = get("/disasters")
        orgs = get("/organizations")
        beneficiaries = get("/beneficiaries")
        programs = get("/programs")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            stat_card("Total Disasters", len(disasters), "🌊")
        with col2:
            stat_card("Organizations", len(orgs), "🏢")
        with col3:
            stat_card("Beneficiaries", len(beneficiaries), "👥")
        with col4:
            stat_card("Programs", len(programs), "📋")

        st.divider()

        active = [d for d in disasters if d.get("status") == "Active"]
        if active:
            st.subheader("Active Disasters")
            for d in active:
                st.markdown(
                    f"<div style='background:#fff;border:1px solid #e2e8f0;border-left:4px solid #2563eb;"
                    f"border-radius:10px;padding:0.8rem 1.1rem;margin-bottom:0.6rem;"
                    f"display:flex;align-items:center;justify-content:space-between;"
                    f"box-shadow:0 1px 2px rgba(15,23,42,0.05);'>"
                    f"<span style='font-weight:600;color:#0f172a;'>{d['disaster_name']}</span>"
                    f"<span>{severity_badge(d['severity_level'])}"
                    f"<span style='color:#64748b;font-size:0.85rem;margin-left:0.8rem;'>"
                    f"Declared {format_date(d['declaration_date'])}</span></span></div>",
                    unsafe_allow_html=True,
                )

        st.subheader("Recent Incident Reports")
        reports = get("/incidents", params={"limit": 10})
        if reports:
            df = pd.DataFrame([
                {
                    "Severity": f"{severity_color(r['severity_flag'])} {r['severity_flag']}",
                    "Title": r["report_title"],
                    "Date": format_date(r["report_date"]),
                    "Submitted By": r["submitted_by"],
                }
                for r in reports
            ])
            data_table(df)
    except Exception as e:
        st.error(f"Failed to load dashboard: {e}")

# ─── 3D Map ──────────────────────────────────────────────────────────────────
elif page == "3D Map":
    st.subheader("Disaster Heatmap")
    st.caption("Click a marker to view full disaster details.")

    try:
        locations = get("/disasters/locations")

        if not locations:
            st.info("No disaster locations with GPS data found.")
        else:
            with_gps = [loc for loc in locations if loc.get("gps_latitude") and loc.get("gps_longitude")]
            if not with_gps:
                st.warning("No GPS coordinates available for any disaster locations.")
            else:
                # ── Build the Folium map ──────────────────────────────────
                m = folium.Map(
                    location=[30.0, 69.0],
                    zoom_start=5,
                    tiles="CartoDB dark_matter",
                )

                # Heatmap overlay
                from folium.plugins import HeatMap
                heat_data = [
                    [loc["gps_latitude"], loc["gps_longitude"], loc["affected_population"] / 1000]
                    for loc in with_gps
                ]
                HeatMap(heat_data, radius=40, blur=30, max_zoom=1).add_to(m)

                # ── Clickable markers ─────────────────────────────────────
                for loc in with_gps:
                    sev = loc["severity_level"]
                    color_map = {
                        "Critical": "red",
                        "High": "orange",
                        "Medium": "yellow",
                        "Low": "green",
                    }
                    marker_color = color_map.get(sev, "gray")

                    popup_html = f"""
                    <div style="font-family: sans-serif; min-width: 220px;">
                        <h4 style="margin: 0 0 8px 0; color: #333;">{loc['disaster_name']}</h4>
                        <table style="font-size: 13px; border-collapse: collapse; width: 100%;">
                            <tr><td style="padding: 3px 0; color: #666; width: 120px;"><b>Type</b></td><td style="padding: 3px 0;">{loc['disaster_type']}</td></tr>
                            <tr><td style="padding: 3px 0; color: #666;"><b>Severity</b></td><td style="padding: 3px 0;"><span style="color: {marker_color}; font-weight: bold;">{sev}</span></td></tr>
                            <tr><td style="padding: 3px 0; color: #666;"><b>Status</b></td><td style="padding: 3px 0;">{loc['status']}</td></tr>
                            <tr><td style="padding: 3px 0; color: #666;"><b>Affected</b></td><td style="padding: 3px 0;">{loc['affected_population']:,} people</td></tr>
                            <tr><td style="padding: 3px 0; color: #666;"><b>Location</b></td><td style="padding: 3px 0;">{loc['district']}, {loc['province']}</td></tr>
                            <tr><td style="padding: 3px 0; color: #666;"><b>Tehsil</b></td><td style="padding: 3px 0;">{loc.get('tehsil') or '—'}</td></tr>
                            <tr><td style="padding: 3px 0; color: #666;"><b>GPS</b></td><td style="padding: 3px 0;">{loc['gps_latitude']}, {loc['gps_longitude']}</td></tr>
                        </table>
                    </div>
                    """

                    folium.Marker(
                        location=[loc["gps_latitude"], loc["gps_longitude"]],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=f"{loc['disaster_name']} ({sev})",
                        icon=folium.Icon(color=marker_color, icon="info-sign"),
                    ).add_to(m)

                # ── Legend ────────────────────────────────────────────────
                legend_html = """
                <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                            background: white; padding: 12px 16px; border-radius: 8px;
                            box-shadow: 0 2px 6px rgba(0,0,0,0.3); font-size: 13px; font-family: sans-serif;">
                    <b style="font-size: 14px;">Severity</b><br/>
                    <span style="color: red; font-weight: bold;">&#9679;</span> Critical<br/>
                    <span style="color: orange; font-weight: bold;">&#9679;</span> High<br/>
                    <span style="color: #d4a017; font-weight: bold;">&#9679;</span> Medium<br/>
                    <span style="color: green; font-weight: bold;">&#9679;</span> Low
                </div>
                """
                m.get_root().html.add_child(folium.Element(legend_html))

                st_folium(m, width="100%", height=600)

    except Exception as e:
        st.error(f"Failed to load map data: {e}")

# ─── Disasters ───────────────────────────────────────────────────────────────
elif page == "Disasters":
    tab_list, tab_create = st.tabs(["All Disasters", "Create Disaster"])

    with tab_list:
        try:
            disasters = get("/disasters")
            if disasters:
                df = pd.DataFrame([
                    {
                        "ID": d["disaster_id"],
                        "Name": d["disaster_name"],
                        "Type ID": d["disaster_type_id"],
                        "Severity": d["severity_level"],
                        "Status": d["status"],
                        "Declared": format_date(d["declaration_date"]),
                        "End": format_date(d.get("projected_end_date")),
                    }
                    for d in disasters
                ])
                data_table(df)
            else:
                st.info("No disasters found.")
        except Exception as e:
            st.error(f"Error: {e}")

    with tab_create:
        with st.form("create_disaster"):
            name = st.text_input("Disaster Name")
            dtype = st.number_input("Disaster Type ID", min_value=1, value=1)
            severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
            dec_date = st.date_input("Declaration Date", value=date.today())
            desc = st.text_area("Description")
            submitted = st.form_submit_button("Create")
            if submitted and name:
                try:
                    result = post("/disasters", {
                        "disaster_type_id": dtype,
                        "disaster_name": name,
                        "severity_level": severity,
                        "declaration_date": str(dec_date),
                        "description": desc,
                    })
                    st.success(f"Created: {result['disaster_name']}")
                except Exception as e:
                    st.error(f"Error: {e}")

# ─── Organizations ───────────────────────────────────────────────────────────
elif page == "Organizations":
    tab_list, tab_leaderboard = st.tabs(["All Organizations", "Fulfillment Leaderboard"])

    with tab_list:
        try:
            orgs = get("/organizations")
            if orgs:
                df = pd.DataFrame([
                    {
                        "ID": o["org_id"],
                        "Name": o["org_name"],
                        "Category": o["org_category_id"],
                        "Email": o["contact_email"],
                        "Status": o["approval_status"],
                    }
                    for o in orgs
                ])
                data_table(df)
        except Exception as e:
            st.error(f"Error: {e}")

    with tab_leaderboard:
        try:
            lb = get("/organizations/leaderboard")
            if lb:
                df = pd.DataFrame([
                    {
                        "Organization": o["org_name"],
                        "Category": o["category_name"],
                        "Commitments": o["total_commitments"],
                        "Delivered": o["total_units_delivered"],
                        "Committed": o["total_units_committed"],
                        "Reliability %": o["reliability_pct"],
                    }
                    for o in lb
                ])
                data_table(df)
        except Exception as e:
            st.error(f"Error: {e}")

# ─── Programs ────────────────────────────────────────────────────────────────
elif page == "Programs":
    tab_list, tab_active, tab_gap = st.tabs(["All Programs", "Active Programs", "Gap Report"])

    with tab_list:
        try:
            programs = get("/programs")
            if programs:
                df = pd.DataFrame([
                    {
                        "ID": p["program_id"],
                        "Name": p["program_name"],
                        "Disaster ID": p["disaster_id"],
                        "Status": p["status"],
                        "Start": format_date(p["start_date"]),
                        "End": format_date(p.get("end_date")),
                    }
                    for p in programs
                ])
                data_table(df)
        except Exception as e:
            st.error(f"Error: {e}")

    with tab_active:
        try:
            active = get("/programs/active")
            if active:
                df = pd.DataFrame([
                    {
                        "Program": a["program_name"],
                        "Disaster": a["disaster_name"],
                        "Severity": a["severity_level"],
                        "Orgs Enrolled": a["enrolled_org_count"],
                        "Requirements": a["total_requirements"],
                        "Start": format_date(a["start_date"]),
                    }
                    for a in active
                ])
                data_table(df)
        except Exception as e:
            st.error(f"Error: {e}")

    with tab_gap:
        prog_id = st.number_input("Program ID for Gap Report", min_value=1, value=1)
        threshold = st.slider("Fulfillment Threshold (%)", 0, 100, 70)
        if st.button("Generate Report"):
            try:
                gap = get(f"/programs/{prog_id}/gap-report", params={"threshold": threshold})
                if gap:
                    df = pd.DataFrame([
                        {
                            "Requirement": g["requirement_id"],
                            "District": g["location_district"],
                            "Product": g["product_name"],
                            "Required": g["quantity_required"],
                            "Fulfilled": g["quantity_fulfilled"],
                            "Fulfillment %": g["fulfillment_pct"],
                            "Gap": g["gap_units"],
                            "Priority": g["priority"],
                        }
                        for g in gap
                    ])
                    data_table(df)
                else:
                    st.info("All requirements are above the threshold.")
            except Exception as e:
                st.error(f"Error: {e}")

# ─── Incident Reports ────────────────────────────────────────────────────────
elif page == "Incident Reports":
    tab_list, tab_submit = st.tabs(["All Reports", "Submit Report"])

    with tab_list:
        try:
            severity_filter = st.selectbox("Filter by Severity", ["All", "Info", "Warning", "Critical"])
            params = {"limit": 50}
            if severity_filter != "All":
                params["severity"] = severity_filter
            reports = get("/incidents", params=params)
            if reports:
                for r in reports:
                    icon = severity_color(r["severity_flag"])
                    with st.expander(f"{icon} [{r['severity_flag']}] {r['report_title']} — {format_date(r['report_date'])}"):
                        st.write(r["report_body"])
                        st.caption(f"Submitted by: {r['submitted_by']} | Team: {r['team_id']} | Location: {r['location_id']}")
        except Exception as e:
            st.error(f"Error: {e}")

    with tab_submit:
        with st.form("submit_report"):
            team_id = st.number_input("Team ID", min_value=1, value=1)
            location_id = st.number_input("Location ID", min_value=1, value=1)
            title = st.text_input("Report Title")
            body = st.text_area("Report Body")
            sev = st.selectbox("Severity", ["Info", "Warning", "Critical"])
            submitter = st.text_input("Submitted By")
            submitted = st.form_submit_button("Submit Report")
            if submitted and title and body and submitter:
                try:
                    post("/incidents", {
                        "team_id": team_id,
                        "location_id": location_id,
                        "report_title": title,
                        "report_body": body,
                        "severity_flag": sev,
                        "submitted_by": submitter,
                    })
                    st.success("Report submitted successfully!")
                except Exception as e:
                    st.error(f"Error: {e}")

# ─── AI Assistant ────────────────────────────────────────────────────────────
elif page == "AI Assistant":
    st.subheader("DisasterLink AI Assistant")
    st.caption("Ask questions about incident reports. The AI will answer based on field reports in the database.")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Re-ingest Reports"):
            try:
                result = post("/rag/ingest")
                st.success(f"Ingested {result['reports_ingested']} reports")
            except Exception as e:
                st.error(f"Ingestion failed: {e}")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("sources"):
                st.caption("Sources: " + ", ".join(
                    f"Report {s['id']} ({s['location']}, score: {s['score']})"
                    for s in msg["sources"]
                ))

    if prompt := st.chat_input("Ask about disaster incidents..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching incident reports..."):
                try:
                    result = post("/rag/query", {"query": prompt, "top_k": 3})
                    st.write(result["answer"])
                    if result.get("sources"):
                        st.caption("Sources: " + ", ".join(
                            f"Report {s['id']} ({s['location']}, score: {s['score']})"
                            for s in result["sources"]
                        ))
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["answer"],
                        "sources": result.get("sources", []),
                    })
                except Exception as e:
                    st.error(f"AI query failed: {e}")
