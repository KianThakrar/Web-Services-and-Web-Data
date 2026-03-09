"""Generate a professional API documentation PDF from the FastAPI OpenAPI schema.

Produces a Stripe/Twilio-style reference document with:
  - Cover section with project metadata
  - Grouped endpoints by tag with descriptions
  - Parameters, request bodies, and response tables
  - Example curl commands for key endpoints
  - Colour-coded method badges and consistent typography

Usage:
    DYLD_LIBRARY_PATH="$(brew --prefix)/lib" python -m scripts.generate_docs
"""

import json
import os
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from weasyprint import HTML

openapi = app.openapi()
api_version = openapi.get("info", {}).get("version", "1.0")
definitions = openapi.get("components", {}).get("schemas", {})

# ── Example curl snippets for key endpoints ──────────────────────────────────

CURL_EXAMPLES = {
    "/api/v1/drivers": 'curl "http://localhost:8000/api/v1/drivers?nationality=British&name=hamilton"',
    "/api/v1/races": 'curl "http://localhost:8000/api/v1/races?season=2024"',
    "/api/v1/auth/register": textwrap.dedent("""\
        curl -X POST http://localhost:8000/api/v1/auth/register \\
          -H "Content-Type: application/json" \\
          -d '{"username": "fan1", "email": "fan@example.com", "password": "securepass8"}'"""),
    "/api/v1/auth/login": textwrap.dedent("""\
        curl -X POST http://localhost:8000/api/v1/auth/login \\
          -H "Content-Type: application/x-www-form-urlencoded" \\
          -d "username=fan1&password=securepass8"
    """).strip(),
    "/api/v1/predictions": textwrap.dedent("""\
        curl -X POST http://localhost:8000/api/v1/predictions \\
          -H "Authorization: Bearer <token>" \\
          -H "Content-Type: application/json" \\
          -d '{"race_id": 84, "predicted_driver_id": 692, "predicted_position": 1}'"""),
    "/api/v1/favourites": textwrap.dedent("""\
        curl -X POST http://localhost:8000/api/v1/favourites \\
          -H "Authorization: Bearer <token>" \\
          -H "Content-Type: application/json" \\
          -d '{"driver_id": 692}'"""),
    "/api/v1/analytics/drivers/standings": 'curl "http://localhost:8000/api/v1/analytics/drivers/standings?season=2024"',
    "/api/v1/analytics/weather/circuits/{circuit_name}": 'curl "http://localhost:8000/api/v1/analytics/weather/circuits/Silverstone%20Circuit"',
    "/api/v1/analytics/weather/drivers/{driver_id}": 'curl "http://localhost:8000/api/v1/analytics/weather/drivers/332"',
    "/api/v1/analytics/weather/races/{race_id}": 'curl "http://localhost:8000/api/v1/analytics/weather/races/84"',
    "/api/v1/ai/races/{race_id}/summary": 'curl "http://localhost:8000/api/v1/ai/races/84/summary"',
}

EXAMPLE_RESPONSES = {
    "/api/v1/analytics/weather/drivers/{driver_id}": json.dumps({
        "driver_id": 332, "driver_name": "Lewis Hamilton", "nationality": "British",
        "total_races_with_weather_data": 189,
        "wet": {
            "condition": "Wet", "races": 68, "wins": 12, "podiums": 23,
            "win_rate": 0.1765, "podium_rate": 0.3382, "avg_finish": 4.1,
            "dnfs": 4, "total_points": 966.0
        },
        "dry": {
            "condition": "Dry", "races": 121, "wins": 38, "podiums": 72,
            "win_rate": 0.314, "podium_rate": 0.595, "avg_finish": 3.8,
            "dnfs": 7, "total_points": 1914.0
        },
        "verdict": "Lewis Hamilton performs consistently regardless of weather conditions"
    }, indent=2),
    "/api/v1/analytics/weather/circuits/{circuit_name}": json.dumps({
        "circuit_name": "Silverstone Circuit", "total_races_with_data": 27,
        "avg_temperature_max": 20.5, "wet_race_percentage": 63.0,
        "wet_races": 17, "dry_races": 10
    }, indent=2),
}


def badge(method: str) -> str:
    colours = {
        "get": "#2196f3", "post": "#4caf50", "put": "#ff9800",
        "delete": "#f44336", "patch": "#9c27b0",
    }
    bg = colours.get(method.lower(), "#757575")
    return (
        f'<span style="background:{bg};color:#fff;padding:3px 10px;'
        f'border-radius:4px;font-weight:700;font-size:10px;'
        f'font-family:\'SF Mono\',Consolas,monospace;letter-spacing:0.5px;'
        f'text-transform:uppercase;">{method.upper()}</span>'
    )


def render_params(params: list) -> str:
    if not params:
        return ""
    rows = ""
    for p in params:
        schema = p.get("schema", {})
        typ = schema.get("type", "string")
        default = schema.get("default", "—")
        required = '<span style="color:#4caf50;font-weight:700">required</span>' if p.get("required") else '<span style="color:#999">optional</span>'
        desc = p.get("description", "")
        rows += (
            f'<tr><td><code>{p["name"]}</code></td>'
            f'<td style="color:#666">{p.get("in","")}</td>'
            f'<td style="color:#666">{typ}</td>'
            f'<td>{required}</td>'
            f'<td style="color:#666">{default}</td>'
            f'<td>{desc}</td></tr>'
        )
    return (
        '<div class="param-section">'
        '<h5>Parameters</h5>'
        '<table><thead><tr>'
        '<th>Name</th><th>In</th><th>Type</th><th>Required</th><th>Default</th><th>Description</th>'
        '</tr></thead><tbody>' + rows + '</tbody></table></div>'
    )


def render_body(req_body: dict) -> str:
    if not req_body:
        return ""
    content = req_body.get("content", {})
    html = ""
    for content_type, content_info in content.items():
        schema = content_info.get("schema", {})
        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            schema = definitions.get(ref_name, schema)
        props = schema.get("properties", {})
        required = set(schema.get("required", []))
        if not props:
            continue
        rows = ""
        for name, info in props.items():
            if "$ref" in info:
                info = definitions.get(info["$ref"].split("/")[-1], info)
            typ = info.get("type", "object")
            desc = info.get("description", "")
            req = '<span style="color:#4caf50;font-weight:700">required</span>' if name in required else '<span style="color:#999">optional</span>'
            rows += f'<tr><td><code>{name}</code></td><td style="color:#666">{typ}</td><td>{req}</td><td>{desc}</td></tr>'
        html += (
            '<div class="param-section">'
            f'<h5>Request Body <span style="color:#999;font-weight:400">({content_type})</span></h5>'
            '<table><thead><tr>'
            '<th>Field</th><th>Type</th><th>Required</th><th>Description</th>'
            '</tr></thead><tbody>' + rows + '</tbody></table></div>'
        )
    return html


def render_responses(responses: dict) -> str:
    rows = ""
    for code, info in responses.items():
        color = "#4caf50" if str(code).startswith("2") else "#f44336" if str(code).startswith("4") else "#ff9800"
        rows += f'<tr><td><code style="color:{color};font-weight:700">{code}</code></td><td>{info.get("description","")}</td></tr>'
    return (
        '<div class="param-section">'
        '<h5>Responses</h5>'
        '<table><thead><tr><th style="width:80px">Status</th><th>Description</th></tr></thead>'
        '<tbody>' + rows + '</tbody></table></div>'
    )


def render_curl(path: str) -> str:
    curl = CURL_EXAMPLES.get(path, "")
    if not curl:
        return ""
    resp = EXAMPLE_RESPONSES.get(path, "")
    html = (
        '<div class="example-box">'
        f'<h5>Example Request</h5>'
        f'<pre>{curl}</pre>'
    )
    if resp:
        html += f'<h5>Example Response</h5><pre>{resp}</pre>'
    html += '</div>'
    return html


# ── Group endpoints by tag ───────────────────────────────────────────────────
tags_order = [t["name"] for t in openapi.get("tags", [])]
tag_descriptions = {t["name"]: t.get("description", "") for t in openapi.get("tags", [])}
tag_endpoints: dict[str, list] = {t: [] for t in tags_order}

for path, methods in openapi.get("paths", {}).items():
    for method, op in methods.items():
        if method in ("get", "post", "put", "delete", "patch"):
            tags = op.get("tags", ["Other"])
            for tag in tags:
                tag_endpoints.setdefault(tag, [])
                tag_endpoints[tag].append((method, path, op))

# Count total endpoints
total_endpoints = sum(len(eps) for eps in tag_endpoints.values())

# ── Build TOC ────────────────────────────────────────────────────────────────
toc_html = ""
for tag, endpoints in tag_endpoints.items():
    if not endpoints:
        continue
    toc_html += f'<div style="margin-bottom:3px"><strong>{tag}</strong> <span style="color:#999">({len(endpoints)} endpoints)</span></div>'
    for method, path, op in endpoints:
        summary = op.get("summary", "")
        toc_html += f'<div style="margin-left:16px;margin-bottom:1px;font-size:10px">{badge(method)} <code style="font-size:10px">{path}</code> <span style="color:#888">{summary}</span></div>'

# ── Build endpoint sections ──────────────────────────────────────────────────
endpoint_html = ""
for tag, endpoints in tag_endpoints.items():
    if not endpoints:
        continue
    tag_desc = tag_descriptions.get(tag, "")
    endpoint_html += f'<h2>{tag}</h2>'
    if tag_desc:
        endpoint_html += f'<p style="color:#666;margin-top:-4px">{tag_desc}</p>'

    for method, path, op in endpoints:
        summary = op.get("summary", "")
        desc = op.get("description", "")
        params = op.get("parameters", [])
        req_body = op.get("requestBody", {})

        endpoint_html += f'''
        <div class="endpoint">
          <div class="endpoint-header">
            {badge(method)}&nbsp;&nbsp;<code class="path">{path}</code>
          </div>
          <div class="endpoint-summary">{summary}</div>
        '''

        if desc and desc != summary:
            endpoint_html += f'<p class="endpoint-desc">{desc}</p>'

        endpoint_html += render_params(params)
        endpoint_html += render_body(req_body)
        endpoint_html += render_responses(op.get("responses", {}))
        endpoint_html += render_curl(path)
        endpoint_html += '</div>'


# ── Final HTML ───────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>F1 Racing Intelligence API — Documentation</title>
<style>
  @page {{
    size: A4;
    margin: 18mm 14mm 20mm 14mm;
    @bottom-center {{
      content: "F1 Racing Intelligence API — Page " counter(page);
      font-size: 8px;
      color: #aaa;
      font-family: -apple-system, 'Segoe UI', sans-serif;
    }}
  }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, sans-serif;
    font-size: 11px;
    color: #1a1a2e;
    margin: 0;
    padding: 0;
    line-height: 1.5;
  }}

  /* ── Cover ─────────────────────────────────────────── */
  .cover {{
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: #fff;
    padding: 40px 32px;
    border-radius: 8px;
    margin-bottom: 20px;
  }}
  .cover h1 {{
    font-size: 28px;
    margin: 0 0 4px;
    letter-spacing: -0.5px;
  }}
  .cover .accent {{
    color: #e10600;
    font-weight: 800;
  }}
  .cover .subtitle {{
    color: #a0aec0;
    font-size: 12px;
    margin: 0 0 16px;
  }}
  .cover-meta {{
    display: flex;
    gap: 24px;
    margin-top: 16px;
  }}
  .cover-stat {{
    text-align: center;
  }}
  .cover-stat .val {{
    font-size: 22px;
    font-weight: 800;
    color: #e10600;
  }}
  .cover-stat .lbl {{
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #a0aec0;
  }}

  /* ── Info boxes ────────────────────────────────────── */
  .info-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 16px;
  }}
  .info-card {{
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 6px;
    padding: 10px 14px;
  }}
  .info-card h4 {{
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #666;
    margin: 0 0 4px;
  }}
  .info-card p {{
    margin: 0;
    font-size: 11px;
  }}

  /* ── TOC ───────────────────────────────────────────── */
  .toc {{
    background: #fafbfc;
    border: 1px solid #e1e4e8;
    border-radius: 6px;
    padding: 14px 18px;
    margin: 14px 0;
  }}
  .toc-title {{
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 8px;
    color: #1a1a2e;
  }}

  /* ── Sections ──────────────────────────────────────── */
  h2 {{
    font-size: 15px;
    color: #1a1a2e;
    border-bottom: 2px solid #e10600;
    padding-bottom: 4px;
    margin-top: 24px;
    page-break-after: avoid;
  }}
  h5 {{
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: #555;
    margin: 8px 0 4px;
  }}

  /* ── Endpoints ─────────────────────────────────────── */
  .endpoint {{
    border: 1px solid #e1e4e8;
    border-radius: 6px;
    padding: 12px 14px;
    margin: 10px 0;
    page-break-inside: avoid;
  }}
  .endpoint-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 2px;
  }}
  code.path {{
    font-size: 11px;
    color: #1a1a2e;
    font-weight: 600;
    font-family: 'SF Mono', Consolas, monospace;
  }}
  .endpoint-summary {{
    font-size: 11px;
    color: #555;
    margin-bottom: 6px;
  }}
  .endpoint-desc {{
    font-size: 10px;
    color: #666;
    margin: 4px 0;
    line-height: 1.4;
  }}

  /* ── Tables ────────────────────────────────────────── */
  .param-section {{
    margin: 6px 0;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 10px;
    margin: 2px 0 6px;
  }}
  th {{
    background: #f6f8fa;
    padding: 5px 8px;
    text-align: left;
    border: 1px solid #e1e4e8;
    font-weight: 600;
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    color: #555;
  }}
  td {{
    padding: 4px 8px;
    border: 1px solid #eee;
    vertical-align: top;
  }}

  /* ── Code ──────────────────────────────────────────── */
  code {{
    background: #f1f3f5;
    padding: 1px 5px;
    border-radius: 3px;
    font-family: 'SF Mono', Consolas, monospace;
    font-size: 10px;
  }}
  pre {{
    background: #1a1a2e;
    color: #e2e8f0;
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 9px;
    font-family: 'SF Mono', Consolas, monospace;
    line-height: 1.5;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-all;
  }}

  /* ── Example box ───────────────────────────────────── */
  .example-box {{
    background: #fafbfc;
    border: 1px solid #e1e4e8;
    border-radius: 6px;
    padding: 8px 12px;
    margin-top: 6px;
  }}

  /* ── Auth & model info ─────────────────────────────── */
  .model-box {{
    background: #f0f4ff;
    border-left: 3px solid #2196f3;
    padding: 10px 14px;
    margin: 10px 0;
    border-radius: 0 6px 6px 0;
    font-size: 11px;
  }}
  .error-table {{
    margin: 10px 0;
  }}
</style>
</head>
<body>

<!-- Cover -->
<div class="cover">
  <h1>F1 Racing Intelligence <span class="accent">API</span></h1>
  <p class="subtitle">COMP3011 Web Services and Web Data &nbsp;|&nbsp; University of Leeds 2025/26</p>
  <div class="cover-meta">
    <div class="cover-stat"><div class="val">{total_endpoints}</div><div class="lbl">Endpoints</div></div>
    <div class="cover-stat"><div class="val">13</div><div class="lbl">MCP Tools</div></div>
    <div class="cover-stat"><div class="val">60</div><div class="lbl">Tests</div></div>
    <div class="cover-stat"><div class="val">12,641</div><div class="lbl">Data Rows</div></div>
    <div class="cover-stat"><div class="val">2</div><div class="lbl">External APIs</div></div>
  </div>
</div>

<!-- Quick reference -->
<div class="info-grid">
  <div class="info-card">
    <h4>Base URL</h4>
    <p><code>http://localhost:8000</code></p>
  </div>
  <div class="info-card">
    <h4>Interactive Docs</h4>
    <p><code>http://localhost:8000/docs</code> (Swagger UI)</p>
  </div>
  <div class="info-card">
    <h4>Authentication</h4>
    <p>Bearer JWT in <code>Authorization</code> header. Tokens issued at <code>POST /api/v1/auth/login</code>.</p>
  </div>
  <div class="info-card">
    <h4>Response Format</h4>
    <p>All responses are <strong>JSON</strong>. Errors include <code>"detail"</code> message.</p>
  </div>
</div>

<!-- Authentication detail -->
<div class="model-box">
  <strong>Authentication Flow:</strong> Register → Login (receive JWT) → Include <code>Authorization: Bearer &lt;token&gt;</code> in protected requests.
  Tokens include a JTI claim — <code>POST /api/v1/auth/logout</code> blacklists the JTI so the token cannot be reused.
</div>

<!-- Error codes -->
<h2>HTTP Status Codes</h2>
<table class="error-table">
  <tr><th>Code</th><th>Meaning</th><th>When Used</th></tr>
  <tr><td><code style="color:#4caf50;font-weight:700">200</code></td><td>OK</td><td>Successful GET, PUT</td></tr>
  <tr><td><code style="color:#4caf50;font-weight:700">201</code></td><td>Created</td><td>Successful POST (resource created)</td></tr>
  <tr><td><code style="color:#4caf50;font-weight:700">204</code></td><td>No Content</td><td>Successful DELETE</td></tr>
  <tr><td><code style="color:#f44336;font-weight:700">400</code></td><td>Bad Request</td><td>Validation errors, malformed input</td></tr>
  <tr><td><code style="color:#f44336;font-weight:700">401</code></td><td>Unauthorized</td><td>Missing, expired, or revoked JWT token</td></tr>
  <tr><td><code style="color:#f44336;font-weight:700">403</code></td><td>Forbidden</td><td>Authenticated but not resource owner</td></tr>
  <tr><td><code style="color:#f44336;font-weight:700">404</code></td><td>Not Found</td><td>Resource does not exist</td></tr>
  <tr><td><code style="color:#f44336;font-weight:700">409</code></td><td>Conflict</td><td>Duplicate username, email, or favourite</td></tr>
  <tr><td><code style="color:#ff9800;font-weight:700">422</code></td><td>Unprocessable Entity</td><td>Pydantic schema validation failure</td></tr>
  <tr><td><code style="color:#ff9800;font-weight:700">429</code></td><td>Too Many Requests</td><td>Rate limit exceeded (10/min on auth)</td></tr>
  <tr><td><code style="color:#f44336;font-weight:700">500</code></td><td>Internal Server Error</td><td>Unhandled exceptions</td></tr>
</table>

<!-- Models -->
<h2>Data Models</h2>
<div class="model-box">
  <strong>Win Probability Model:</strong> The <code>GET /api/v1/analytics/drivers/{{id}}/win-probability</code> endpoint combines
  Circuit Win Rate (40%), Overall Career Win Rate (30%), Recent Form — last 10 races (20%), and Constructor Strength (10%)
  into a probability score between 0 and 1.
</div>
<div class="model-box">
  <strong>Weather Classification:</strong> Races are classified as wet or dry using WMO weather codes and precipitation thresholds (&gt;0.5mm).
  The <code>weather_advantage_score</code> (0–100) combines finishing position and points-per-race differences — scores &gt;50 indicate better performance in wet conditions.
  Weather data is sourced from the <strong>Open-Meteo Archive API</strong> (500 races, 2000–2025).
</div>

<!-- MCP Server -->
<h2>MCP Server</h2>
<p>The project exposes all F1 data as <strong>Model Context Protocol (MCP) tools</strong> for AI client integration (13 tools):</p>
<table>
  <tr><th>Transport</th><th>Command</th><th>Compatible Clients</th></tr>
  <tr><td>stdio</td><td><code>python mcp_server.py</code></td><td>Claude Desktop, Claude Code, VS Code Copilot</td></tr>
  <tr><td>SSE (HTTP)</td><td><code>python mcp_server.py --sse</code></td><td>Any MCP client (Claude, OpenAI Agents, Google Gemini ADK)</td></tr>
</table>
<p>Verify with: <code>python -m scripts.test_mcp</code></p>

<!-- TOC -->
<div class="toc" style="page-break-before: always;">
  <div class="toc-title">Endpoint Reference — Table of Contents</div>
  {toc_html}
</div>

<!-- Endpoint reference -->
{endpoint_html}

</body>
</html>"""

out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "api_documentation.pdf")
print(f"Generating PDF → {out_path}")
HTML(string=html).write_pdf(out_path)
print(f"Done — {os.path.getsize(out_path) // 1024} KB")
