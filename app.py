import http.cookiejar
import json
import mimetypes
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent
INDEX_PATH = ROOT / "templates" / "index.html"
STATIC_DIR = ROOT / "static"


def parse_hidden_fields(html: str):
    return {
        name: value
        for name, value in re.findall(r'<input[^>]+name="([^"]+)"[^>]+value="([^"]*)"', html, flags=re.I)
        if name in {"__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"}
    }


def detect_login_fields(html: str):
    username = None
    password = None
    captcha = None

    for field in re.findall(r'<input[^>]+name="([^"]+)"', html, flags=re.I):
        name = field.lower()
        if not username and any(token in name for token in ["kullanici", "user", "username", "login", "mail", "tc", "kimlik"]):
            username = field
        if not password and any(token in name for token in ["sifre", "password", "parola", "pwd"]):
            password = field
        if not captcha and any(token in name for token in ["captcha", "guvenlik", "kod", "image", "resim"]):
            captcha = field

    return {
        "username_field": username,
        "password_field": password,
        "captcha_field": captcha,
    }


def extract_forms(html: str) -> List[Dict[str, object]]:
    forms = []
    for match in re.finditer(r'<form([^>]*)>(.*?)</form>', html, flags=re.I | re.S):
        attrs = match.group(1)
        body = match.group(2)
        inputs = re.findall(r'<input[^>]+name="([^"]+)"', body, flags=re.I)
        buttons = re.findall(r'<button[^>]*>(.*?)</button>', body, flags=re.I | re.S)
        forms.append({
            "attributes": attrs,
            "input_names": inputs,
            "button_texts": [re.sub(r'<.*?>', '', b).strip() for b in buttons if b.strip()],
        })
    return forms


def extract_script_urls(html: str) -> List[str]:
    return re.findall(r'<script[^>]+src="([^"]+)"', html, flags=re.I)


class BrowserOpener(urllib.request.OpenerDirector):
    def __init__(self):
        super().__init__()
        self.cookie_jar = http.cookiejar.CookieJar()
        handler = urllib.request.HTTPCookieProcessor(self.cookie_jar)
        self.add_handler(handler)
        self.add_handler(urllib.request.HTTPHandler())
        self.add_handler(urllib.request.HTTPSHandler())


class NexPanelHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/":
            self.serve_html(INDEX_PATH)
            return
        if path.startswith("/static/"):
            self.serve_static(path)
            return
        if path == "/api/health":
            self.send_json({"status": "ok", "service": "NexPanel"})
            return
        if path.startswith("/api/proxy"):
            self.handle_proxy("GET", parsed)
            return

        self.serve_html(INDEX_PATH)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/proxy"):
            self.handle_proxy("POST", parsed)
            return
        self.send_json({"error": "Unsupported endpoint"}, 404)

    def handle_proxy(self, method, parsed):
        query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        target = query.get("target", [""])[0]
        if not target:
            self.send_json({"error": "Missing target"}, 400)
            return

        query_string = query.get("query", [""])[0]
        payload = query.get("payload", [""])[0]
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Origin": "https://e-okul.meb.gov.tr",
            "Referer": "https://e-okul.meb.gov.tr/logineokul.aspx"
        }

        final_url = self.build_url(target, query_string)
        body = None
        encoded_payload = None
        if payload:
            body = payload.encode("utf-8")
            encoded_payload = payload
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        opener = BrowserOpener()
        cookie_header = self.headers.get("Cookie")
        if cookie_header:
            headers["Cookie"] = cookie_header

        try:
            req = urllib.request.Request(final_url, data=body, headers=headers, method=method)
            with opener.open(req, timeout=20) as response:
                raw = response.read()
                content_type = response.headers.get_content_type()
                charset = response.headers.get_content_charset() or "utf-8"
                text = raw.decode(charset, errors="ignore")

                try:
                    parsed_body = json.loads(text)
                except Exception:
                    parsed_body = text

                self.send_json({
                    "ok": True,
                    "url": final_url,
                    "status": response.status,
                    "contentType": content_type,
                    "body": parsed_body,
                    "rawLength": len(raw),
                    "cookies": [c.name + "=" + c.value for c in opener.cookie_jar],
                    "hiddenFields": parse_hidden_fields(text) if isinstance(parsed_body, str) else {},
                    "detectedLoginFields": detect_login_fields(text) if isinstance(parsed_body, str) else {},
                    "forms": extract_forms(text) if isinstance(parsed_body, str) else [],
                    "scriptUrls": extract_script_urls(text) if isinstance(parsed_body, str) else [],
                    "payload": encoded_payload,
                })
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            charset = exc.headers.get_content_charset() or "utf-8"
            text = raw.decode(charset, errors="ignore")
            self.send_json({
                "ok": False,
                "url": final_url,
                "status": exc.code,
                "contentType": exc.headers.get_content_type(),
                "body": text,
                "error": str(exc),
                "cookies": [c.name + "=" + c.value for c in opener.cookie_jar],
                "hiddenFields": parse_hidden_fields(text),
                "detectedLoginFields": detect_login_fields(text),
                "forms": extract_forms(text),
                "scriptUrls": extract_script_urls(text),
                "payload": encoded_payload,
            }, exc.code)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, 500)

    def build_url(self, target, query_string):
        parsed = urllib.parse.urlsplit(target)
        if not query_string:
            return target
        existing = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        incoming = urllib.parse.parse_qsl(query_string, keep_blank_values=True)
        existing.extend(incoming)
        new_query = urllib.parse.urlencode(existing, doseq=True)
        return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, new_query, parsed.fragment))

    def serve_html(self, path):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(path.read_bytes())

    def serve_static(self, path):
        file_path = ROOT / path.lstrip("/")
        if not file_path.exists():
            self.send_json({"error": "Not found"}, 404)
            return
        content_type, _ = mimetypes.guess_type(str(file_path))
        if not content_type:
            content_type = "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(file_path.read_bytes())

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def main():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), NexPanelHandler)
    print(f"NexPanel listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
