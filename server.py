#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SERVER.PY - Web API cho Render Dashboard
Tích hợp KeyCheater + Jirviral Bypass
"""

import re
import time
import json
import urllib.parse
import urllib.request
import urllib.error
import http.cookiejar
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# ========================== CONFIG ========================== #
DEFAULT_UA = ("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36")

# ========================== HTTP HELPER ========================== #
class Http:
    def __init__(self, ua=DEFAULT_UA):
        self.ua = ua
        self.cj = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj),
            urllib.request.HTTPRedirectHandler(),
        )

    def request(self, method, url, data=None, referer=None):
        headers = {
            "User-Agent": self.ua,
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
        }
        body = None
        if data is not None:
            body = urllib.parse.urlencode(data).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            o = urllib.parse.urlparse(url)
            headers["Origin"] = o.scheme + "://" + o.netloc
            headers["Referer"] = referer or url
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            resp = self.op.open(req, timeout=60)
            return resp.getcode(), resp.geturl(), resp.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            return e.code, e.geturl(), e.read().decode("utf-8", "ignore")
        except Exception as e:
            return 500, url, str(e)


# ========================== KEY CHEATER EXPLOIT ========================== #
def keycheater_bypass(seller="zennymod1", game="noroot"):
    """KeyCheater Exploit - lấy key từ keycheater.site"""
    try:
        import requests
    except ImportError:
        return {"success": False, "error": "requests module not installed. Run: pip install requests"}

    BASE = "https://keycheater.site"
    API = f"{BASE}/getkey"
    UA = DEFAULT_UA

    try:
        s = requests.Session()
        s.headers.update({
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
        })

        # STEP 1: GET CSRF
        r = s.get(f"{API}/{seller}", timeout=30)
        r.raise_for_status()
        html = r.text

        csrf_m = re.search(r'csrf_test_name" value="([^"]+)"', html)
        if not csrf_m:
            return {"success": False, "error": "No CSRF token found"}
        csrf = csrf_m.group(1)

        # Config
        wait = 30  # Giảm xuống 30s để tránh timeout trên Render free
        wm = re.search(r'wait_time["\:]\s*(\d+)', html)
        if wm:
            wait = min(int(wm.group(1)), 30)  # Giới hạn tối đa 30s

        sm = re.search(r'shortlink_url["\:]\s*"([^"]+)"', html)
        sl = sm.group(1) if sm else "N/A"

        # STEP 2: SUBMIT
        r2 = s.post(f"{BASE}/getkey-process",
                    data={"csrf_test_name": csrf, "seller": seller, "game": game},
                    allow_redirects=False,
                    timeout=30)
        if r2.status_code not in (302, 303):
            return {"success": False, "error": f"HTTP {r2.status_code}"}

        token = None
        for k, v in r2.headers.items():
            if k.lower() == "set-cookie":
                mt = re.search(r'getkey_token=([^;]+)', v)
                if mt:
                    token = mt.group(1)
        if not token:
            return {"success": False, "error": "No token found"}

        s.cookies.set("getkey_token", token, domain="keycheater.site", path="/")
        s.cookies.set("getkey_game", game, domain="keycheater.site", path="/")

        # STEP 3: WAIT (giảm thời gian chờ)
        time.sleep(min(wait, 30))

        # STEP 4: CALLBACK
        r3 = s.get(f"{BASE}/getkey-callback/{seller}", timeout=30)
        text = r3.text

        if "PHAT HIEN" in text.upper() or "GIAN LAN" in text.upper():
            return {"success": False, "error": "BLOCKED! Server detected bypass"}

        # EXTRACT KEY
        key = None

        # Method 1: key-box div
        m = re.search(r'class="[^"]*key[-_]?box[^"]*"[^>]*>([^<]+)<', text, re.I)
        if m:
            key = m.group(1).strip()

        # Method 2: VipXXXXX
        if not key:
            m = re.search(r'>([Vv]ip[A-Za-z0-9_-]+)<', text)
            if m:
                key = m.group(1)

        # Method 3: Getkey-XXXX
        if not key:
            m = re.search(r'(Getkey-[A-F0-9]+)', text)
            if m:
                key = m.group(1)

        # Method 4: SQL query
        if not key:
            m = re.search(r"user_key['\"]?\s*[,)]\s*'([^']+)'", text)
            if m:
                key = m.group(1)

        # Method 5: JSON
        if not key:
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    for k in ("key", "key_code", "user_key", "data", "code", "token"):
                        if k in data:
                            key = data[k]
                            break
            except:
                pass

        if key:
            return {
                "success": True,
                "key": key,
                "seller": seller,
                "game": game,
                "link": f"{API}/{seller}",
                "shortlink": sl,
                "expires": "24 hours"
            }
        else:
            return {"success": False, "error": "No key found in response"}

    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timeout - server took too long"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection error - cannot reach server"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ========================== JIRVIRAL BYPASS ========================== #
class JirviralBypass:
    def __init__(self):
        self.http = Http()

    def get_unlock_token(self, html):
        m = re.search(r'name=["\']unlock_token["\'][^>]*value=["\']([^"\']+)["\']', html, re.I)
        return m.group(1) if m else None

    def get_k(self, html):
        m = re.search(r'name=["\']k["\']\s+value=["\']([^"\']+)["\']', html, re.I)
        return m.group(1) if m else None

    def title(self, html):
        m = re.search(r'<title>(.*?)</title>', html, re.S | re.I)
        return m.group(1) if m else None

    def get_key(self, html):
        m = re.search(r'id=["\']keyText["\'][^>]*>\s*([^<\s]+)', html, re.I)
        return m.group(1).strip() if m else None

    def parse_gate_form(self, html):
        for fm in re.finditer(r'<form([^>]*)>(.*?)</form>', html, re.S | re.I):
            inner = fm.group(2)
            if 'id="download"' not in inner and "id='download'" not in inner:
                continue
            attrs = fm.group(1)
            action = re.search(r'action=["\']([^"\']*)["\']', attrs, re.I)
            action = action.group(1) if action else ""
            method = re.search(r'method=["\']([^"\']*)["\']', attrs, re.I)
            method = (method.group(1) or "get").lower()
            fields = {}
            for m2 in re.finditer(r'<input[^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']', inner, re.I):
                fields[m2.group(1)] = m2.group(2)
            for m2 in re.finditer(r'<input[^>]*value=["\']([^"\']*)["\'][^>]*name=["\']([^"\']+)["\']', inner, re.I):
                fields[m2.group(2)] = m2.group(1)
            return action, method, fields
        return None, None, None

    def parse_post_redirect(self, html):
        m = re.search(r'<form[^>]*id=["\']fc-post-redirect["\'][^>]*action=["\']([^"\']+)["\'][^>]*>(.*?)</form>', html, re.S | re.I)
        if not m:
            return None, None
        action = m.group(1)
        fields = {}
        for fm in re.finditer(r'<input[^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']', m.group(2), re.I):
            fields[fm.group(1)] = fm.group(2)
        return action, fields

    def bypass(self, gate_url, gate_wait=10, unlock_wait=5):
        cur = gate_url
        html = None
        actions = 0
        MAX_ACTIONS = 80

        while actions < MAX_ACTIONS:
            actions += 1

            if html is None:
                try:
                    code, fu, html = self.http.request("GET", cur)
                    cur = fu
                except Exception as e:
                    return {"success": False, "error": f"Request failed: {str(e)}"}

            # post-redirect form
            action, fields = self.parse_post_redirect(html)
            if action and fields:
                try:
                    code, fu, html = self.http.request("POST", action, fields, referer=cur)
                    cur = fu
                    if not self.parse_gate_form(html)[2] and not self.get_unlock_token(html) and not self.get_key(html) and not self.parse_post_redirect(html)[0]:
                        time.sleep(2)
                        code, fu, html = self.http.request("POST", action, fields, referer=cur)
                        cur = fu
                except Exception as e:
                    return {"success": False, "error": f"Redirect failed: {str(e)}"}
                continue

            # gate form
            gaction, gmethod, gfields = self.parse_gate_form(html)
            if gfields is not None:
                target = gaction or cur
                if gate_wait > 0 and "cad=" not in cur:
                    time.sleep(min(gate_wait, 10))  # Giới hạn chờ
                try:
                    if gmethod == "post":
                        code, fu, html = self.http.request("POST", target, gfields, referer=cur)
                    else:
                        qs = urllib.parse.urlencode(gfields)
                        full = target + ("&" if "?" in target else "?") + qs
                        code, fu, html = self.http.request("GET", full, referer=cur)
                    cur = fu
                except Exception as e:
                    return {"success": False, "error": f"Gate form failed: {str(e)}"}
                continue

            # unlock form
            if self.get_unlock_token(html):
                tok = self.get_unlock_token(html)
                try:
                    code, fu, html = self.http.request("POST", cur, {
                        "unl": "1", "unlock_src": "blur_iframe", "unlock_token": tok,
                    }, referer=cur)
                    cur = fu
                    k2 = self.get_k(html)
                    if k2:
                        time.sleep(min(unlock_wait, 5))
                        u3 = fu + ("&" if "?" in fu else "?") + "fc_go=1&k=" + urllib.parse.quote(k2)
                        code, fu, html = self.http.request("GET", u3, referer=fu)
                        cur = fu
                except Exception as e:
                    return {"success": False, "error": f"Unlock failed: {str(e)}"}
                continue

            # final key
            key = self.get_key(html)
            if key:
                return {"success": True, "key": key}

            t = (self.title(html) or "").lower()
            if "tempo expirado" in t or "acesso bloqueado" in t:
                return {"success": False, "error": f"Link expired: {self.title(html)}"}

            if html is not None:
                return {"success": False, "error": f"Unknown page: {self.title(html)}"}

        return {"success": False, "error": "Max actions reached, no key found"}


def jirviral_bypass(url, gate_wait=10, unlock_wait=5):
    jb = JirviralBypass()
    return jb.bypass(url, gate_wait, unlock_wait)


# ========================== WEB API ========================== #

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Bypass Tool API</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 900px; margin: 20px auto; padding: 20px; background: #0d1117; color: #c9d1d9; }
        h1 { color: #58a6ff; text-align:center; margin-bottom:20px; }
        .card { background: #161b22; padding: 20px; border-radius: 10px; margin: 15px 0; border: 1px solid #30363d; }
        .endpoint { color: #f0883e; font-weight: bold; }
        .method { color: #58a6ff; }
        pre { background: #0d1117; padding: 15px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; }
        .success { color: #3fb950; }
        .error { color: #f85149; }
        input, button { padding: 10px; margin: 5px 0; border-radius: 5px; border: 1px solid #30363d; background: #0d1117; color: #c9d1d9; width: 100%; }
        button { background: #238636; color: white; font-weight: bold; cursor: pointer; width: auto; min-width: 120px; }
        button:hover { background: #2ea043; }
        button:disabled { opacity:0.5; cursor:not-allowed; }
        .row { display: flex; gap: 10px; flex-wrap: wrap; }
        .row > * { flex: 1; min-width: 120px; }
        .flex { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
        .badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.7rem; font-weight: 600; }
        .badge-blue { background: #1f6feb; color: white; }
        .badge-orange { background: #d29922; color: white; }
        .mt-10 { margin-top: 10px; }
        .mb-10 { margin-bottom: 10px; }
        .text-center { text-align: center; }
        .text-muted { color: #8b949e; font-size:0.9rem; }
        .border-left { border-left: 4px solid #30363d; padding-left: 15px; }
        .border-left-success { border-left-color: #3fb950; }
        .border-left-error { border-left-color: #f85149; }
        .border-left-loading { border-left-color: #58a6ff; animation: pulse 1.5s ease-in-out infinite; }
        @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.5; } }
        .status-box { min-height: 50px; padding: 12px 16px; background: #0d1117; border-radius: 8px; margin-top: 10px; word-break: break-all; }
        .key-highlight { background: #1c2333; padding: 2px 10px; border-radius: 4px; font-family: monospace; font-weight: 700; color: #f0883e; font-size: 1.1rem; }
    </style>
</head>
<body>
    <h1>🚀 Bypass Tool</h1>
    <p class="text-center text-muted">KeyCheater v3.0 + Jirviral / Olympus Link Bypass</p>

    <div class="card">
        <h2>📌 API Endpoints</h2>
        <p><span class="method">POST</span> <span class="endpoint">/api/keycheater</span> - KeyCheater Exploit</p>
        <p><span class="method">POST</span> <span class="endpoint">/api/jirviral</span> - Jirviral Bypass</p>
        <p><span class="method">GET</span> <span class="endpoint">/</span> - Trang này</p>
    </div>

    <div class="card">
        <h2>🔑 KeyCheater</h2>
        <div class="row">
            <input id="seller" placeholder="Seller (zennymod1)" value="zennymod1">
            <input id="game" placeholder="Game (noroot)" value="noroot">
        </div>
        <button onclick="runKeyCheater()" id="kc-btn">⚡ Lấy Key</button>
        <div class="status-box border-left" id="kc-result">⏳ Nhập thông tin và nhấn nút</div>
    </div>

    <div class="card">
        <h2>🔗 Jirviral</h2>
        <input id="jv-url" placeholder="https://jirviral.xyz/.../?cad=...">
        <div class="row">
            <input id="jv-gate" placeholder="Gate wait (s)" value="10" type="number" min="0">
            <input id="jv-unlock" placeholder="Unlock wait (s)" value="5" type="number" min="0">
        </div>
        <button onclick="runJirviral()" id="jv-btn">🚀 Bypass</button>
        <div class="status-box border-left" id="jv-result">⏳ Dán link và nhấn nút</div>
    </div>

    <script>
        let kcProcessing = false;
        let jvProcessing = false;

        function setStatus(id, html, type='idle') {
            const el = document.getElementById(id);
            el.className = 'status-box border-left';
            if (type === 'loading') el.className += ' border-left-loading';
            else if (type === 'success') el.className += ' border-left-success';
            else if (type === 'error') el.className += ' border-left-error';
            el.innerHTML = html;
        }

        async function runKeyCheater() {
            if (kcProcessing) { setStatus('kc-result', '⏳ Đang xử lý, vui lòng đợi...', 'loading'); return; }
            kcProcessing = true;
            const btn = document.getElementById('kc-btn');
            btn.disabled = true;
            btn.textContent = '⏳ Đang xử lý...';
            setStatus('kc-result', '🔄 Đang gửi request... Vui lòng đợi.', 'loading');

            try {
                const res = await fetch('/api/keycheater', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        seller: document.getElementById('seller').value || 'zennymod1',
                        game: document.getElementById('game').value || 'noroot'
                    })
                });
                const data = await res.json();
                if (data.success) {
                    setStatus('kc-result', `✅ THÀNH CÔNG! Key: <span class="key-highlight">${data.key}</span>`, 'success');
                } else {
                    setStatus('kc-result', `❌ THẤT BẠI: ${data.error || 'Unknown error'}`, 'error');
                }
            } catch(e) {
                setStatus('kc-result', `❌ LỖI: ${e.message}`, 'error');
            }
            kcProcessing = false;
            btn.disabled = false;
            btn.textContent = '⚡ Lấy Key';
        }

        async function runJirviral() {
            if (jvProcessing) { setStatus('jv-result', '⏳ Đang xử lý, vui lòng đợi...', 'loading'); return; }
            const url = document.getElementById('jv-url').value.trim();
            if (!url) { setStatus('jv-result', '⚠️ Vui lòng nhập URL', 'error'); return; }
            jvProcessing = true;
            const btn = document.getElementById('jv-btn');
            btn.disabled = true;
            btn.textContent = '⏳ Đang bypass...';
            setStatus('jv-result', '🔄 Đang bypass link... Vui lòng đợi.', 'loading');

            try {
                const res = await fetch('/api/jirviral', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        url: url,
                        gate_wait: parseInt(document.getElementById('jv-gate').value) || 10,
                        unlock_wait: parseInt(document.getElementById('jv-unlock').value) || 5
                    })
                });
                const data = await res.json();
                if (data.success) {
                    setStatus('jv-result', `✅ THÀNH CÔNG! Key/Link: <span class="key-highlight">${data.key}</span>`, 'success');
                } else {
                    setStatus('jv-result', `❌ THẤT BẠI: ${data.error || 'Unknown error'}`, 'error');
                }
            } catch(e) {
                setStatus('jv-result', `❌ LỖI: ${e.message}`, 'error');
            }
            jvProcessing = false;
            btn.disabled = false;
            btn.textContent = '🚀 Bypass';
        }

        // Enter key support
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                if (document.activeElement.id === 'seller' || document.activeElement.id === 'game') {
                    runKeyCheater();
                } else if (document.activeElement.id === 'jv-url' || document.activeElement.id === 'jv-gate' || document.activeElement.id === 'jv-unlock') {
                    runJirviral();
                }
            }
        });
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/keycheater', methods=['POST'])
def api_keycheater():
    try:
        data = request.get_json() or {}
        seller = data.get('seller', 'zennymod1')
        game = data.get('game', 'noroot')
        result = keycheater_bypass(seller, game)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/jirviral', methods=['POST'])
def api_jirviral():
    try:
        data = request.get_json() or {}
        url = data.get('url', '')
        if not url:
            return jsonify({"success": False, "error": "Missing url parameter"})
        gate_wait = data.get('gate_wait', 10)
        unlock_wait = data.get('unlock_wait', 5)
        result = jirviral_bypass(url, gate_wait, unlock_wait)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ========================== RUN ========================== #
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)