from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import time
import os

app = Flask(__name__)

# ==================== SCRAPING FUNCTION ====================
def scrape_pakistan_details(query):
    query = query.strip().replace(" ", "").replace("-", "").replace("+", "")
    
    if not (re.match(r'^92\d{9,11}$', query) or re.match(r'^\d{13}$', query)):
        return {"error": "Invalid input. Mobile number 92 se start hona chahiye ya 13 digit CNIC ho."}

    url = "https://pakistandatabase.com/index.php"
    
    headers = {
        'authority': 'pakistandatabase.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://pakistandatabase.com',
        'referer': 'https://pakistandatabase.com/index.php',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36',
    }

    data = {'search_query': query}

    try:
        response = requests.post(url, headers=headers, data=data, timeout=20)
        
        if response.status_code != 200:
            return {"error": f"Request failed with status {response.status_code}"}

        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        for row in soup.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 4:
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                
                if (query in cell_texts[0] or 
                    (len(cell_texts) > 2 and query in cell_texts[2])):
                    
                    result = {
                        "mobile": cell_texts[0] if len(cell_texts) > 0 else "N/A",
                        "name": cell_texts[1] if len(cell_texts) > 1 else "N/A",
                        "cnic": cell_texts[2] if len(cell_texts) > 2 else "N/A",
                        "address": cell_texts[3] if len(cell_texts) > 3 else "N/A"
                    }
                    results.append(result)

        search_type = "Mobile" if query.startswith("92") else "CNIC"
        
        if results:
            return {
                "success": True,
                "query": query,
                "search_type": search_type,
                "total_records": len(results),
                "results": results
            }
        else:
            return {
                "success": False,
                "query": query,
                "message": "No record found on the site for this query."
            }

    except Exception as e:
        return {"error": f"Server error: {str(e)}"}


# ==================== API ROUTES ====================
@app.route('/api/lookup', methods=['GET', 'POST'])
def lookup():
    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form
        query = data.get('query') or data.get('search_query') or data.get('number') or data.get('cnic')
    else:
        query = (request.args.get('query') or 
                 request.args.get('search_query') or 
                 request.args.get('number') or 
                 request.args.get('cnic'))

    if not query:
        return jsonify({
            "error": "Please provide 'query' parameter.",
            "example": "/api/lookup?query=923001234567"
        }), 400

    time.sleep(1.2)  # Small delay to avoid rate limiting
    
    result = scrape_pakistan_details(query)
    return jsonify(result)


@app.route('/')
def home():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Shadow API \u2014 Pakistan SIM &amp; CNIC Lookup</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:        #0d1117;
      --surface:   #161b22;
      --border:    #30363d;
      --accent:    #238636;
      --accent-h:  #2ea043;
      --blue:      #1f6feb;
      --blue-h:    #388bfd;
      --text:      #e6edf3;
      --muted:     #8b949e;
      --code-bg:   #1c2128;
      --green:     #3fb950;
      --orange:    #d29922;
      --red:       #f85149;
    }

    html { scroll-behavior: smooth; }

    body {
      font-family: 'Inter', system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* NAV */
    nav {
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(13,17,23,.85);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      padding: 0 1.5rem;
    }
    .nav-inner {
      max-width: 1100px;
      margin: 0 auto;
      height: 60px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .logo {
      display: flex;
      align-items: center;
      gap: .6rem;
      font-weight: 700;
      font-size: 1.1rem;
      text-decoration: none;
      color: var(--text);
    }
    .logo-icon {
      width: 32px; height: 32px;
      background: linear-gradient(135deg, #238636, #1f6feb);
      border-radius: 8px;
      display: flex; align-items: center; justify-content: center;
      font-size: 1rem;
    }
    .badge {
      font-size: .7rem;
      font-weight: 600;
      padding: .2rem .55rem;
      border-radius: 20px;
      background: rgba(35,134,54,.15);
      color: var(--green);
      border: 1px solid rgba(63,185,80,.25);
      letter-spacing: .04em;
    }
    .nav-links { display: flex; gap: 1.5rem; }
    .nav-links a {
      color: var(--muted);
      text-decoration: none;
      font-size: .875rem;
      font-weight: 500;
      transition: color .2s;
    }
    .nav-links a:hover { color: var(--text); }

    /* HERO */
    .hero {
      text-align: center;
      padding: 5rem 1.5rem 4rem;
      background: radial-gradient(ellipse 80% 50% at 50% -10%, rgba(31,111,235,.18), transparent);
    }
    .hero-flag { font-size: 3rem; margin-bottom: 1rem; display: block; }
    .hero h1 {
      font-size: clamp(2rem, 5vw, 3.2rem);
      font-weight: 800;
      letter-spacing: -.03em;
      line-height: 1.15;
      background: linear-gradient(135deg, #e6edf3 30%, #8b949e);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 1rem;
    }
    .hero p {
      font-size: 1.1rem;
      color: var(--muted);
      max-width: 560px;
      margin: 0 auto 2rem;
    }
    .hero-actions { display: flex; gap: .75rem; justify-content: center; flex-wrap: wrap; }
    .btn {
      display: inline-flex;
      align-items: center;
      gap: .4rem;
      padding: .65rem 1.4rem;
      border-radius: 8px;
      font-size: .9rem;
      font-weight: 600;
      text-decoration: none;
      transition: all .2s;
      cursor: pointer;
      border: none;
    }
    .btn-primary { background: var(--accent); color: #fff; }
    .btn-primary:hover { background: var(--accent-h); transform: translateY(-1px); }
    .btn-secondary { background: transparent; color: var(--text); border: 1px solid var(--border); }
    .btn-secondary:hover { border-color: var(--muted); background: var(--surface); }

    /* STATS */
    .stats { display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap; padding: 0 1.5rem 4rem; }
    .stat { text-align: center; }
    .stat-value { font-size: 1.8rem; font-weight: 800; color: var(--text); }
    .stat-label { font-size: .8rem; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; margin-top: .15rem; }

    /* MAIN */
    main { flex: 1; max-width: 1100px; margin: 0 auto; padding: 0 1.5rem 5rem; width: 100%; }

    /* SECTION TITLES */
    .section-title {
      font-size: 1.4rem;
      font-weight: 700;
      margin-bottom: 1.25rem;
      display: flex;
      align-items: center;
      gap: .6rem;
    }
    .section-title::after { content: ''; flex: 1; height: 1px; background: var(--border); margin-left: .5rem; }

    /* ENDPOINT CARDS */
    .endpoints { display: flex; flex-direction: column; gap: 1.25rem; margin-bottom: 3.5rem; }
    .endpoint-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      transition: border-color .2s;
    }
    .endpoint-card:hover { border-color: #484f58; }
    .endpoint-header {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1rem 1.25rem;
      border-bottom: 1px solid var(--border);
      flex-wrap: wrap;
    }
    .method {
      font-family: 'JetBrains Mono', monospace;
      font-size: .75rem;
      font-weight: 700;
      padding: .25rem .65rem;
      border-radius: 6px;
      letter-spacing: .05em;
    }
    .method-get  { background: rgba(31,111,235,.2);  color: #79c0ff; border: 1px solid rgba(31,111,235,.35); }
    .method-post { background: rgba(35,134,54,.2);   color: #7ee787; border: 1px solid rgba(35,134,54,.35); }
    .endpoint-path { font-family: 'JetBrains Mono', monospace; font-size: .9rem; color: var(--text); flex: 1; }
    .endpoint-desc { font-size: .82rem; color: var(--muted); margin-left: auto; }
    .endpoint-body { padding: 1.25rem; }

    .param-table { width: 100%; border-collapse: collapse; font-size: .875rem; margin-bottom: 1rem; }
    .param-table th {
      text-align: left;
      padding: .5rem .75rem;
      color: var(--muted);
      font-weight: 600;
      font-size: .75rem;
      text-transform: uppercase;
      letter-spacing: .06em;
      border-bottom: 1px solid var(--border);
    }
    .param-table td { padding: .6rem .75rem; border-bottom: 1px solid rgba(48,54,61,.5); vertical-align: top; }
    .param-table tr:last-child td { border-bottom: none; }
    .param-name { font-family: 'JetBrains Mono', monospace; font-size: .82rem; color: #79c0ff; }
    .param-type { font-family: 'JetBrains Mono', monospace; font-size: .78rem; color: var(--orange); }
    .required-badge {
      font-size: .68rem; padding: .1rem .4rem; border-radius: 4px;
      background: rgba(248,81,73,.15); color: var(--red); border: 1px solid rgba(248,81,73,.3); font-weight: 600;
    }
    .optional-badge {
      font-size: .68rem; padding: .1rem .4rem; border-radius: 4px;
      background: rgba(139,148,158,.1); color: var(--muted); border: 1px solid var(--border); font-weight: 600;
    }

    /* CODE BLOCKS */
    .code-label { font-size: .72rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; margin-bottom: .4rem; }
    pre {
      background: var(--code-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1rem 1.25rem;
      overflow-x: auto;
      font-family: 'JetBrains Mono', monospace;
      font-size: .82rem;
      line-height: 1.7;
      margin-bottom: 1rem;
    }
    pre:last-child { margin-bottom: 0; }
    .kw  { color: #ff7b72; }
    .str { color: #a5d6ff; }
    .key { color: #79c0ff; }
    .val { color: #7ee787; }
    .num { color: #f2cc60; }
    .url { color: #a5d6ff; }

    /* EXAMPLES GRID */
    .examples-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.25rem; margin-bottom: 3.5rem; }
    .example-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.25rem;
      transition: border-color .2s;
    }
    .example-card:hover { border-color: #484f58; }
    .example-card h4 { font-size: .9rem; font-weight: 600; margin-bottom: .75rem; display: flex; align-items: center; gap: .5rem; }
    .example-card a {
      display: block;
      font-family: 'JetBrains Mono', monospace;
      font-size: .78rem;
      color: var(--blue-h);
      text-decoration: none;
      padding: .4rem .6rem;
      border-radius: 6px;
      background: rgba(31,111,235,.08);
      margin-bottom: .4rem;
      word-break: break-all;
      transition: background .2s;
    }
    .example-card a:hover { background: rgba(31,111,235,.18); }

    /* RESPONSE */
    .response-section { margin-bottom: 3.5rem; }
    .response-tabs { display: flex; gap: .5rem; margin-bottom: 1rem; flex-wrap: wrap; }
    .tab { padding: .4rem .9rem; border-radius: 6px; font-size: .8rem; font-weight: 600; border: 1px solid var(--border); background: transparent; color: var(--muted); }
    .tab.success { border-color: rgba(63,185,80,.4); color: var(--green); background: rgba(63,185,80,.08); }
    .tab.error   { border-color: rgba(248,81,73,.4);  color: var(--red);   background: rgba(248,81,73,.08); }

    /* INFO CARDS */
    .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; margin-bottom: 3.5rem; }
    .info-card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; }
    .info-card-icon { font-size: 1.5rem; margin-bottom: .75rem; }
    .info-card h4 { font-size: .95rem; font-weight: 700; margin-bottom: .4rem; }
    .info-card p { font-size: .85rem; color: var(--muted); line-height: 1.55; }

    /* FOOTER */
    footer { border-top: 1px solid var(--border); padding: 2rem 1.5rem; text-align: center; color: var(--muted); font-size: .82rem; }
    footer a { color: var(--muted); text-decoration: none; }
    footer a:hover { color: var(--text); }
    .footer-inner { max-width: 1100px; margin: 0 auto; display: flex; flex-direction: column; align-items: center; gap: .6rem; }
    .footer-links { display: flex; gap: 1.5rem; }

    /* RESPONSIVE */
    @media (max-width: 640px) {
      .nav-links { display: none; }
      .stats { gap: 1.25rem; }
      .endpoint-desc { display: none; }
    }
  </style>
</head>
<body>

<nav>
  <div class="nav-inner">
    <a class="logo" href="/">
      <div class="logo-icon">\U0001f50d</div>
      Shadow API
      <span class="badge">v1.0</span>
    </a>
    <div class="nav-links">
      <a href="#endpoints">Endpoints</a>
      <a href="#examples">Examples</a>
      <a href="#response">Response</a>
      <a href="#notes">Notes</a>
    </div>
  </div>
</nav>

<div class="hero">
  <span class="hero-flag">\U0001f1f5\U0001f1f0</span>
  <h1>Pakistan SIM &amp; CNIC<br/>Lookup API</h1>
  <p>Fast, simple REST API to look up Pakistan mobile numbers and CNIC records. Integrate in seconds.</p>
  <div class="hero-actions">
    <a class="btn btn-primary" href="#endpoints">View Endpoints</a>
    <a class="btn btn-secondary" href="/api/lookup?query=923001234567">Try Live Demo</a>
  </div>
</div>

<div class="stats">
  <div class="stat"><div class="stat-value">2</div><div class="stat-label">Endpoints</div></div>
  <div class="stat"><div class="stat-value">GET &amp; POST</div><div class="stat-label">Methods</div></div>
  <div class="stat"><div class="stat-value">JSON</div><div class="stat-label">Response Format</div></div>
  <div class="stat"><div class="stat-value">REST</div><div class="stat-label">Architecture</div></div>
</div>

<main>

  <div id="endpoints">
    <div class="section-title">\U0001f4e1 API Endpoints</div>
    <div class="endpoints">

      <div class="endpoint-card">
        <div class="endpoint-header">
          <span class="method method-get">GET</span>
          <span class="endpoint-path">/api/lookup</span>
          <span class="endpoint-desc">Query via URL parameter</span>
        </div>
        <div class="endpoint-body">
          <table class="param-table">
            <thead>
              <tr>
                <th>Parameter</th><th>Type</th><th>Required</th><th>Description</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><span class="param-name">query</span></td>
                <td><span class="param-type">string</span></td>
                <td><span class="required-badge">Required</span></td>
                <td style="color:var(--muted);font-size:.82rem">Mobile number (92xxxxxxxxxx) or 13-digit CNIC</td>
              </tr>
              <tr>
                <td><span class="param-name">number</span></td>
                <td><span class="param-type">string</span></td>
                <td><span class="optional-badge">Alias</span></td>
                <td style="color:var(--muted);font-size:.82rem">Alias for <code style="font-family:monospace;color:#79c0ff">query</code> &mdash; mobile number lookup</td>
              </tr>
              <tr>
                <td><span class="param-name">cnic</span></td>
                <td><span class="param-type">string</span></td>
                <td><span class="optional-badge">Alias</span></td>
                <td style="color:var(--muted);font-size:.82rem">Alias for <code style="font-family:monospace;color:#79c0ff">query</code> &mdash; CNIC lookup</td>
              </tr>
            </tbody>
          </table>
          <div class="code-label">Request URL</div>
          <pre><span class="url">https://shadow-api-production-63bf.up.railway.app/api/lookup?query=923001234567</span></pre>
        </div>
      </div>

      <div class="endpoint-card">
        <div class="endpoint-header">
          <span class="method method-post">POST</span>
          <span class="endpoint-path">/api/lookup</span>
          <span class="endpoint-desc">Query via JSON body</span>
        </div>
        <div class="endpoint-body">
          <div class="code-label">Request Body (JSON)</div>
          <pre>{
  <span class="key">"query"</span>: <span class="str">"923001234567"</span>
}</pre>
          <div class="code-label">cURL Example</div>
          <pre><span class="kw">curl</span> -X POST \\
  https://shadow-api-production-63bf.up.railway.app/api/lookup \\
  -H <span class="str">"Content-Type: application/json"</span> \\
  -d <span class="str">'{"query": "923001234567"}'</span></pre>
        </div>
      </div>

    </div>
  </div>

  <div id="examples">
    <div class="section-title">\u26a1 Quick Examples</div>
    <div class="examples-grid">
      <div class="example-card">
        <h4>\U0001f4f1 Mobile Number Lookup</h4>
        <a href="/api/lookup?query=923001234567">/api/lookup?query=923001234567</a>
        <a href="/api/lookup?query=923458765432">/api/lookup?query=923458765432</a>
        <a href="/api/lookup?query=923119876543">/api/lookup?query=923119876543</a>
      </div>
      <div class="example-card">
        <h4>\U0001faaa CNIC Lookup</h4>
        <a href="/api/lookup?query=3520112345671">/api/lookup?query=3520112345671</a>
        <a href="/api/lookup?query=4230123456789">/api/lookup?query=4230123456789</a>
        <a href="/api/lookup?query=3610456789123">/api/lookup?query=3610456789123</a>
      </div>
    </div>
  </div>

  <div id="response" class="response-section">
    <div class="section-title">\U0001f4e6 Response Format</div>

    <div class="response-tabs">
      <span class="tab success">\u2713 200 Success</span>
    </div>
    <div class="code-label">Success Response</div>
    <pre>{
  <span class="key">"success"</span>:       <span class="val">true</span>,
  <span class="key">"query"</span>:         <span class="str">"923001234567"</span>,
  <span class="key">"search_type"</span>:   <span class="str">"Mobile"</span>,
  <span class="key">"total_records"</span>: <span class="num">1</span>,
  <span class="key">"results"</span>: [
    {
      <span class="key">"mobile"</span>:  <span class="str">"923001234567"</span>,
      <span class="key">"name"</span>:    <span class="str">"Muhammad Ali"</span>,
      <span class="key">"cnic"</span>:    <span class="str">"3520112345671"</span>,
      <span class="key">"address"</span>: <span class="str">"House 12, Street 4, Lahore"</span>
    }
  ]
}</pre>

    <div class="response-tabs" style="margin-top:1.25rem">
      <span class="tab error">\u2717 Not Found</span>
    </div>
    <div class="code-label">No Record Response</div>
    <pre>{
  <span class="key">"success"</span>: <span class="val">false</span>,
  <span class="key">"query"</span>:   <span class="str">"923001234567"</span>,
  <span class="key">"message"</span>: <span class="str">"No record found on the site for this query."</span>
}</pre>

    <div class="response-tabs" style="margin-top:1.25rem">
      <span class="tab error">\u2717 400 Bad Request</span>
    </div>
    <div class="code-label">Error Response</div>
    <pre>{
  <span class="key">"error"</span>: <span class="str">"Invalid input. Mobile number 92 se start hona chahiye ya 13 digit CNIC ho."</span>
}</pre>
  </div>

  <div id="notes">
    <div class="section-title">\U0001f4cb Notes &amp; Constraints</div>
    <div class="info-grid">
      <div class="info-card">
        <div class="info-card-icon">\U0001f4f1</div>
        <h4>Mobile Format</h4>
        <p>Numbers must start with <code style="font-family:monospace;color:#79c0ff">92</code> (Pakistan country code) followed by 9&ndash;11 digits. Example: <code style="font-family:monospace;color:#a5d6ff">923001234567</code></p>
      </div>
      <div class="info-card">
        <div class="info-card-icon">\U0001faaa</div>
        <h4>CNIC Format</h4>
        <p>Must be exactly <strong>13 digits</strong> with no dashes or spaces. Example: <code style="font-family:monospace;color:#a5d6ff">3520112345671</code></p>
      </div>
      <div class="info-card">
        <div class="info-card-icon">\u23f1\ufe0f</div>
        <h4>Rate Limiting</h4>
        <p>A small delay is applied between requests to avoid being rate-limited by the upstream data source. Expect ~1&ndash;2 s response times.</p>
      </div>
      <div class="info-card">
        <div class="info-card-icon">\u26a0\ufe0f</div>
        <h4>Data Source</h4>
        <p><strong style="color:var(--red)">USE AT YOUR OWN RISK.</strong> This is an unofficial scraping API with no affiliation to any government or telecom authority. Data accuracy and availability depend entirely on the upstream source and may be incomplete, outdated, or unavailable at any time. The author assumes <strong style="color:var(--red)">no liability whatsoever</strong> for how this API is used. Misuse &mdash; including any activity that violates applicable laws or the privacy of individuals &mdash; is solely the responsibility of the user.</p>
      </div>

    </div>
  </div>

</main>

<footer>
  <div class="footer-inner">
    <div>\U0001f50d <strong>Shadow API</strong> &mdash; Pakistan SIM &amp; CNIC Lookup</div>
    <div class="footer-links">
      <a href="#endpoints">Endpoints</a>
      <a href="#examples">Examples</a>
      <a href="#response">Response</a>
      <a href="/api/lookup?query=923001234567">Live Demo</a>
    </div>
    <div>Deployed on <a href="https://railway.app" target="_blank" rel="noopener">Railway</a> &nbsp;&middot;&nbsp; Unofficial scraping API &nbsp;&middot;&nbsp; Use responsibly</div>
  </div>
</footer>

</body>
</html>"""


# ==================== RUN FOR RAILWAY ====================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
