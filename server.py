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


# ========================== KEY CHEATER EXPLOIT ========================== #
def keycheater_bypass(seller="zennymod1", game="noroot"):
    """KeyCheater Exploit - lấy key từ keycheater.site"""
    try:
        import requests
    except ImportError:
        return {"success": False, "error": "requests module not installed"}

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
        r = s.get(f"{API}/{seller}")
        r.raise_for_status()
        html = r.text

        csrf_m = re.search(r'csrf_test_name" value="([^"]+)"', html)
        if not csrf_m:
            return {"success": False, "error": "No CSRF token found"}
        csrf = csrf_m.group(1)

        # Config
        wait = 100
        wm = re.search(r'wait_time["\:]\s*(\d+)', html)
        if wm:
            wait = int(wm.group(1))

        sm = re.search(r'shortlink_url["\:]\s*"([^"]+)"', html)
        sl = sm.group(1) if sm else "N/A"

        km = re.search(r'key_prefix["\:]\s*"([^"]+)"', html)
        kp = km.group(1) if km else "Vip"

        # STEP 2: SUBMIT
        r2 = s.post(f"{BASE}/getkey-process",
                    data={"csrf_test_name": csrf, "seller": seller, "game": game},
                    allow_redirects=False)
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

        # STEP 3: WAIT
        time.sleep(wait)

        # STEP 4: CALLBACK
        r3 = s.get(f"{BASE}/getkey-callback/{seller}")
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

    def bypass(self, gate_url, gate_wait=15, unlock_wait=6):
        cur = gate_url
        html = None
        actions = 0
        MAX_ACTIONS = 80

        while actions < MAX_ACTIONS:
            actions += 1

            if html is None:
                code, fu, html = self.http.request("GET", cur)
                cur = fu

            # post-redirect form
            action, fields = self.parse_post_redirect(html)
            if action and fields:
                code, fu, html = self.http.request("POST", action, fields, referer=cur)
                cur = fu
                if not self.parse_gate_form(html)[2] and not self.get_unlock_token(html) and not self.get_key(html) and not self.parse_post_redirect(html)[0]:
                    time.sleep(3)
                    code, fu, html = self.http.request("POST", action, fields, referer=cur)
                    cur = fu
                continue

            # gate form
            gaction, gmethod, gfields = self.parse_gate_form(html)
            if gfields is not None:
                target = gaction or cur
                if gate_wait > 0 and "cad=" not in cur:
                    time.sleep(gate_wait)
                if gmethod == "post":
                    code, fu, html = self.http.request("POST", target, gfields, referer=cur)
                else:
                    qs = urllib.parse.urlencode(gfields)
                    full = target + ("&" if "?" in target else "?") + qs
                    code, fu, html = self.http.request("GET", full, referer=cur)
                cur = fu
                continue

            # unlock form
            if self.get_unlock_token(html):
                tok = self.get_unlock_token(html)
                code, fu, html = self.http.request("POST", cur, {
                    "unl": "1", "unlock_src": "blur_iframe", "unlock_token": tok,
                }, referer=cur)
                cur = fu
                k2 = self.get_k(html)
                if k2:
                    time.sleep(unlock_wait)
                    u3 = fu + ("&" if "?" in fu else "?") + "fc_go=1&k=" + urllib.parse.quote(k2)
                    code, fu, html = self.http.request("GET", u3, referer=fu)
                    cur = fu
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


def jirviral_bypass(url, gate_wait=15, unlock_wait=6):
    jb = JirviralBypass()
    return jb.bypass(url, gate_wait, unlock_wait)


# ========================== WEB API ========================== #

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Bypass Tool API</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #0d1117; color: #c9d1d9; }
        h1 { color: #58a6ff; }
        .card { background: #161b22; padding: 20px; border-radius: 10px; margin: 20px 0; border: 1px solid #30363d; }
        .endpoint { color: #f0883e; font-weight: bold; }
        .method { color: #58a6ff; }
        .param { color: #ffa657; }
        pre { background: #0d1117; padding: 15px; border-radius: 5px; overflow-x: auto; }
        .success { color: #3fb950; }
        .error { color: #f85149; }
        input, select, button { padding: 10px; margin: 5px 0; border-radius: 5px; border: 1px solid #30363d; background: #0d1117; color: #c9d1d9; width: 100%; }
        button { background: #238636; color: white; font-weight: bold; cursor: pointer; }
        button:hover { background: #2ea043; }
        .row { display: flex; gap: 10px; }
        .row > * { flex: 1; }
    </style>
</head>
<body>
    <h1>🚀 Bypass Tool API</h1>
    <p>Dashboard tích hợp 2 công cụ bypass</p>
    
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
        <button onclick="runKeyCheater()">Lấy Key</button>
        <pre id="kc-result"></pre>
    </div>

    <div class="card">
        <h2>🔗 Jirviral</h2>
        <input id="jirviral-url" placeholder="https://jirviral.xyz/.../?cad=...">
        <button onclick="runJirviral()">Bypass</button>
        <pre id="jv-result"></pre>
    </div>

    <script>
        async function runKeyCheater() {
            const seller = document.getElementById('seller').value;
            const game = document.getElementById('game').value;
            const result = document.getElementById('kc-result');
            result.textContent = '⏳ Đang xử lý...';
            try {
                const res = await fetch('/api/keycheater', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ seller, game })
                });
                const data = await res.json();
                result.textContent = JSON.stringify(data, null, 2);
            } catch(e) {
                result.textContent = '❌ Lỗi: ' + e.message;
            }
        }

        async function runJirviral() {
            const url = document.getElementById('jirviral-url').value;
            const result = document.getElementById('jv-result');
            if (!url) { result.textContent = '⚠️ Vui lòng nhập URL'; return; }
            result.textContent = '⏳ Đang xử lý...';
            try {
                const res = await fetch('/api/jirviral', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });
                const data = await res.json();
                result.textContent = JSON.stringify(data, null, 2);
            } catch(e) {
                result.textContent = '❌ Lỗi: ' + e.message;
            }
        }
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
        gate_wait = data.get('gate_wait', 15)
        unlock_wait = data.get('unlock_wait', 6)
        result = jirviral_bypass(url, gate_wait, unlock_wait)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ========================== RUN ========================== #
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)