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
    return """
    <h1>🇵🇰 Pakistan SIM & CNIC Lookup API</h1>
    <p><strong>How to use:</strong></p>
    <ul>
        <li>GET → <code>/api/lookup?query=923001234567</code></li>
        <li>GET CNIC → <code>/api/lookup?query=3520112345671</code></li>
        <li>POST JSON → {"query": "923001234567"}</li>
    </ul>

    <h3>Example (Random Fake Numbers)</h3>
    <p>Mobile Examples:</p>
    <ul>
        <li><code>/api/lookup?query=923001234567</code></li>
        <li><code>/api/lookup?query=923458765432</code></li>
        <li><code>/api/lookup?query=923119876543</code></li>
    </ul>
    <p>CNIC Examples:</p>
    <ul>
        <li><code>/api/lookup?query=3520112345671</code></li>
        <li><code>/api/lookup?query=4230123456789</code></li>
        <li><code>/api/lookup?query=3610456789123</code></li>
    </ul>
    <p><strong>Note:</strong> Unofficial scraping API. Data site pe depend karta hai.</p>
    """


# ==================== RUN FOR RAILWAY ====================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)