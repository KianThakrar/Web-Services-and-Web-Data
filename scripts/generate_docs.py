"""Generate API documentation PDF from the FastAPI OpenAPI schema."""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from weasyprint import HTML

openapi = app.openapi()


def badge(method: str) -> str:
    colours = {
        "get": "#61affe",
        "post": "#49cc90",
        "put": "#fca130",
        "delete": "#f93e3e",
        "patch": "#50e3c2",
    }
    bg = colours.get(method.lower(), "#aaa")
    return (
        f'<span style="background:{bg};color:#fff;padding:2px 8px;'
        f'border-radius:3px;font-weight:bold;font-size:11px;'
        f'font-family:monospace;">{method.upper()}</span>'
    )


def render_schema_table(schema: dict, definitions: dict) -> str:
    """Render a JSON schema as an HTML properties table."""
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    if not props:
        return "<p><em>No properties defined.</em></p>"
    rows = ""
    for name, info in props.items():
        # Resolve $ref
        if "$ref" in info:
            ref_name = info["$ref"].split("/")[-1]
            info = definitions.get(ref_name, info)
        typ = info.get("type", info.get("$ref", "object").split("/")[-1])
        desc = info.get("description", "")
        req = "✓" if name in required else ""
        default = info.get("default", "")
        rows += (
            f"<tr><td><code>{name}</code></td><td>{typ}</td>"
            f"<td>{req}</td><td>{default}</td><td>{desc}</td></tr>"
        )
    return (
        "<table><thead><tr>"
        "<th>Field</th><th>Type</th><th>Required</th><th>Default</th><th>Description</th>"
        "</tr></thead><tbody>" + rows + "</tbody></table>"
    )


def render_params(params: list) -> str:
    if not params:
        return ""
    rows = ""
    for p in params:
        schema = p.get("schema", {})
        typ = schema.get("type", "string")
        default = schema.get("default", "")
        required = "✓" if p.get("required") else ""
        rows += (
            f"<tr><td><code>{p['name']}</code></td>"
            f"<td>{p.get('in','')}</td>"
            f"<td>{typ}</td>"
            f"<td>{required}</td>"
            f"<td>{default}</td>"
            f"<td>{p.get('description','')}</td></tr>"
        )
    return (
        "<h5>Parameters</h5>"
        "<table><thead><tr>"
        "<th>Name</th><th>In</th><th>Type</th><th>Required</th><th>Default</th><th>Description</th>"
        "</tr></thead><tbody>" + rows + "</tbody></table>"
    )


def render_responses(responses: dict) -> str:
    rows = ""
    for code, info in responses.items():
        rows += f"<tr><td><code>{code}</code></td><td>{info.get('description','')}</td></tr>"
    return (
        "<h5>Responses</h5>"
        "<table><thead><tr><th>Status</th><th>Description</th></tr></thead>"
        "<tbody>" + rows + "</tbody></table>"
    )


api_version = openapi.get("info", {}).get("version", "1.0")

# Build HTML
tags_order = [t["name"] for t in openapi.get("tags", [])]
# Group endpoints by tag
tag_endpoints: dict[str, list] = {t: [] for t in tags_order}
tag_endpoints.setdefault("Other", [])

for path, methods in openapi.get("paths", {}).items():
    for method, op in methods.items():
        if method in ("get", "post", "put", "delete", "patch"):
            tags = op.get("tags", ["Other"])
            for tag in tags:
                tag_endpoints.setdefault(tag, [])
                tag_endpoints[tag].append((method, path, op))

definitions = openapi.get("components", {}).get("schemas", {})

endpoint_html = ""
for tag, endpoints in tag_endpoints.items():
    if not endpoints:
        continue
    endpoint_html += f"<h2>{tag}</h2>"
    for method, path, op in endpoints:
        summary = op.get("summary", op.get("description", "")[:80])
        desc = op.get("description", "")
        params = op.get("parameters", [])
        req_body = op.get("requestBody", {})

        endpoint_html += f"""
        <div class="endpoint">
          <div class="endpoint-header">
            {badge(method)}&nbsp;&nbsp;<code class="path">{path}</code>
            <span class="summary">{summary}</span>
          </div>
        """

        if desc and desc != summary:
            endpoint_html += f"<p>{desc}</p>"

        endpoint_html += render_params(params)

        if req_body:
            content = req_body.get("content", {})
            for content_type, content_info in content.items():
                schema = content_info.get("schema", {})
                if "$ref" in schema:
                    ref_name = schema["$ref"].split("/")[-1]
                    schema = definitions.get(ref_name, schema)
                endpoint_html += f"<h5>Request Body ({content_type})</h5>"
                endpoint_html += render_schema_table(schema, definitions)

        endpoint_html += render_responses(op.get("responses", {}))
        endpoint_html += "</div>"

html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>F1 Racing Intelligence API — Documentation</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         font-size: 12px; color: #333; margin: 0; padding: 0; }}
  @page {{ size: A4; margin: 20mm 15mm; }}
  h1 {{ font-size: 24px; color: #1a1a2e; border-bottom: 3px solid #e10600;
        padding-bottom: 8px; margin-bottom: 4px; }}
  .subtitle {{ color: #666; margin-top: 0; font-size: 13px; margin-bottom: 16px; }}
  h2 {{ font-size: 16px; color: #e10600; border-bottom: 1px solid #e10600;
        padding-bottom: 4px; margin-top: 24px; page-break-after: avoid; }}
  h5 {{ font-size: 12px; margin: 8px 0 4px; color: #444; }}
  .endpoint {{ border: 1px solid #e0e0e0; border-radius: 4px; padding: 10px 12px;
               margin: 8px 0; page-break-inside: avoid; }}
  .endpoint-header {{ display: flex; align-items: baseline; gap: 10px; margin-bottom: 6px; }}
  code.path {{ font-size: 12px; color: #333; font-weight: 600; }}
  .summary {{ color: #555; font-size: 11px; margin-left: 4px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 11px; margin: 4px 0 8px; }}
  th {{ background: #f5f5f5; padding: 4px 8px; text-align: left;
       border: 1px solid #ddd; font-weight: 600; }}
  td {{ padding: 3px 8px; border: 1px solid #eee; vertical-align: top; }}
  code {{ background: #f5f5f5; padding: 1px 4px; border-radius: 2px;
          font-family: 'Courier New', monospace; font-size: 11px; }}
  .info-box {{ background: #f0f7ff; border-left: 4px solid #2196f3; padding: 10px 14px;
               margin: 10px 0; border-radius: 2px; font-size: 12px; }}
  .toc {{ background: #fafafa; border: 1px solid #e0e0e0; padding: 12px 16px;
          border-radius: 4px; margin: 12px 0; column-count: 2; column-gap: 20px; }}
  .toc a {{ color: #333; text-decoration: none; display: block; margin: 2px 0; font-size: 11px; }}
</style>
</head>
<body>

<h1>F1 Racing Intelligence API</h1>
<p class="subtitle">API Reference Documentation &nbsp;|&nbsp; COMP3011 Web Services and Web Data &nbsp;|&nbsp; University of Leeds 2025/26</p>

<div class="info-box">
  <strong>Base URL:</strong> <code>http://localhost:8000</code><br>
  <strong>Interactive Docs:</strong> <code>http://localhost:8000/docs</code> (Swagger UI)<br>
  <strong>OpenAPI Schema:</strong> <code>http://localhost:8000/openapi.json</code><br>
  <strong>Version:</strong> {api_version}
</div>

<h2>Authentication</h2>
<p>Protected endpoints require a <strong>Bearer JWT token</strong> in the <code>Authorization</code> header:</p>
<pre><code>Authorization: Bearer &lt;access_token&gt;</code></pre>
<p>Tokens are issued at <code>POST /api/v1/auth/login</code> and can be revoked at <code>POST /api/v1/auth/logout</code>.
Each token contains a JTI (JWT ID) claim — logout blacklists the JTI so the token cannot be reused.</p>

<h2>Win Probability Model</h2>
<p>The <code>GET /api/v1/analytics/drivers/{{id}}/win-probability</code> endpoint uses a four-factor weighted model:</p>
<table>
  <tr><th>Factor</th><th>Weight</th><th>Description</th></tr>
  <tr><td>Circuit win rate</td><td>40%</td><td>Historical wins at the specific circuit</td></tr>
  <tr><td>Overall career win rate</td><td>30%</td><td>All-time wins across all circuits</td></tr>
  <tr><td>Recent form</td><td>20%</td><td>Win rate in the last 10 races</td></tr>
  <tr><td>Constructor strength</td><td>10%</td><td>Constructor's all-time win rate</td></tr>
</table>
<p>When no circuit is specified, the circuit factor is replaced by the overall career win rate.</p>

<h2>MCP Server</h2>
<p>The project exposes all F1 data as <strong>Model Context Protocol (MCP) tools</strong> consumable by AI clients:</p>
<table>
  <tr><th>Transport</th><th>Command</th><th>Compatible clients</th></tr>
  <tr><td>stdio</td><td><code>python mcp_server.py</code></td><td>Claude Desktop, Claude Code, VS Code Copilot</td></tr>
  <tr><td>SSE (HTTP)</td><td><code>python mcp_server.py --sse</code></td><td>Any MCP client (Claude, OpenAI Agents, Google Gemini ADK)</td></tr>
</table>

<h2>Error Reference</h2>
<table>
  <tr><th>Status Code</th><th>Meaning</th></tr>
  <tr><td><code>200</code></td><td>Success</td></tr>
  <tr><td><code>201</code></td><td>Created</td></tr>
  <tr><td><code>400</code></td><td>Bad Request — invalid input</td></tr>
  <tr><td><code>401</code></td><td>Unauthorized — missing or revoked token</td></tr>
  <tr><td><code>403</code></td><td>Forbidden — resource belongs to another user</td></tr>
  <tr><td><code>404</code></td><td>Not Found</td></tr>
  <tr><td><code>409</code></td><td>Conflict — duplicate resource (e.g. username taken)</td></tr>
  <tr><td><code>429</code></td><td>Too Many Requests — rate limit exceeded (10/min per IP)</td></tr>
  <tr><td><code>422</code></td><td>Unprocessable Entity — validation error</td></tr>
  <tr><td><code>500</code></td><td>Internal Server Error</td></tr>
</table>

<h2 style="page-break-before: always;">Endpoint Reference</h2>

{endpoint_html}

</body>
</html>"""

out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "api_documentation.pdf")
print(f"Generating PDF → {out_path}")
HTML(string=html).write_pdf(out_path)
print("Done.")
