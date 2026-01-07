#!/usr/bin/env python3
import argparse
import concurrent.futures as cf
import csv
import hashlib
import os
import re
import sys
import time
import urllib.request
import urllib.error
from urllib.parse import urlparse

DEFAULT_TIMEOUT = 12

JS_CTYPES = (
    "application/javascript",
    "text/javascript",
    "application/x-javascript",
    "application/ecmascript",
    "text/ecmascript",
)

HTML_SIGS = (b"<!doctype html", b"<html", b"<head", b"<body")


def sanitize_filename(name: str) -> str:
    name = re.sub(r"[^\w.\-]+", "_", name).strip("_")
    return name[:180] if name else "file.js"


def filename_from_url(url: str) -> str:
    p = urlparse(url)
    base = os.path.basename(p.path.rstrip("/"))
    if not base:
        h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
        base = f"script_{h}.js"
    if not base.lower().endswith(".js"):
        base += ".js"

    # If query params exist, add a stable suffix so versions don't collide
    if p.query:
        qh = hashlib.sha1(p.query.encode("utf-8")).hexdigest()[:6]
        root, ext = os.path.splitext(base)
        base = f"{root}_{qh}{ext}"

    return sanitize_filename(base)


def request_url(url: str, method: str, timeout: int):
    req = urllib.request.Request(
        url,
        method=method,
        headers={
            "User-Agent": "Mozilla/5.0 (JS-URL-Checker)",
            "Accept": "*/*",
        },
    )
    return urllib.request.urlopen(req, timeout=timeout)


def looks_like_js_content(ctype: str, url: str) -> bool:
    c = (ctype or "").lower()
    if any(x in c for x in JS_CTYPES) or "javascript" in c:
        return True
    # Some servers use octet-stream/text/plain for JS. Allow if URL ends in .js
    return url.lower().split("?")[0].endswith(".js")


def is_probably_html(data_prefix: bytes) -> bool:
    p = (data_prefix or b"").lstrip().lower()
    return any(p.startswith(sig) for sig in HTML_SIGS)


def is_active_once(url: str, timeout: int, check_js_header: bool):
    """
    Returns:
      ok(bool), status(str/int), content_type(str), final_url(str)
    """
    # HEAD first
    try:
        with request_url(url, "HEAD", timeout) as resp:
            status = getattr(resp, "status", resp.getcode())
            ctype = resp.headers.get("Content-Type", "") or ""
            final_url = getattr(resp, "url", url)

            if not (200 <= status < 400):
                return False, status, ctype, final_url

            if check_js_header and not looks_like_js_content(ctype, url):
                # fallback to GET to confirm
                raise urllib.error.HTTPError(url, status, "Suspicious content-type", resp.headers, None)

            return True, status, ctype, final_url

    except Exception:
        # Fallback GET
        try:
            with request_url(url, "GET", timeout) as resp:
                status = getattr(resp, "status", resp.getcode())
                ctype = resp.headers.get("Content-Type", "") or ""
                final_url = getattr(resp, "url", url)

                if not (200 <= status < 400):
                    return False, status, ctype, final_url

                if check_js_header and not looks_like_js_content(ctype, url):
                    return False, f"{status} (non-js content-type)", ctype, final_url

                return True, status, ctype, final_url

        except urllib.error.HTTPError as e:
            return False, f"HTTPError {e.code}", "", url
        except urllib.error.URLError as e:
            return False, f"URLError {e.reason}", "", url
        except Exception as e:
            return False, f"Error {type(e).__name__}: {e}", "", url


def is_active(url: str, timeout: int, check_js_header: bool, retries: int, backoff: float):
    last = None
    for attempt in range(retries + 1):
        ok, status, ctype, final_url = is_active_once(url, timeout, check_js_header)
        last = (ok, status, ctype, final_url)
        if ok:
            return last
        if attempt < retries:
            time.sleep(backoff * (2 ** attempt))
    return last


def download_file(url: str, out_dir: str, timeout: int):
    os.makedirs(out_dir, exist_ok=True)
    out_name = filename_from_url(url)
    out_path = os.path.join(out_dir, out_name)

    # Avoid overwriting if exact same filename exists
    if os.path.exists(out_path):
        h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
        root, ext = os.path.splitext(out_name)
        out_path = os.path.join(out_dir, f"{root}_{h}{ext}")

    with request_url(url, "GET", timeout) as resp:
        ctype = resp.headers.get("Content-Type", "") or ""
        data = resp.read()

    # Basic safety: don't save HTML pages as JS
    if is_probably_html(data[:200]):
        raise ValueError(f"Downloaded content looks like HTML, not JS (Content-Type: {ctype})")

    with open(out_path, "wb") as f:
        f.write(data)

    return out_path, len(data), ctype


def main():
    ap = argparse.ArgumentParser(description="Check JS URLs and split active/inactive.")
    ap.add_argument("-i", "--input", default="js_files.txt", help="Input file with URLs (one per line).")
    ap.add_argument("-t", "--timeout", type=int, default=DEFAULT_TIMEOUT, help="Timeout per request (seconds).")
    ap.add_argument("-w", "--workers", type=int, default=20, help="Number of parallel workers.")
    ap.add_argument("--retries", type=int, default=2, help="Retries for transient failures.")
    ap.add_argument("--backoff", type=float, default=0.5, help="Backoff base seconds (exponential).")
    ap.add_argument("--check-js-header", action="store_true",
                    help="Require Content-Type to look like JavaScript (falls back to URL .js).")
    ap.add_argument("--download", action="store_true", help="Download active JS files.")
    ap.add_argument("--outdir", default="active_js_downloads", help="Download folder (if --download).")
    ap.add_argument("--csv", default="report.csv", help="CSV report file.")
    args = ap.parse_args()

    if not os.path.exists(args.input):
        print(f"[!] Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    urls = []
    seen = set()
    with open(args.input, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            u = line.strip()
            if not u or u.startswith("#"):
                continue
            if u not in seen:
                seen.add(u)
                urls.append(u)

    if not urls:
        print("[!] No URLs found in input.")
        sys.exit(0)

    active, inactive = [], []
    rows = []

    def worker(u):
        ok, status, ctype, final_url = is_active(u, args.timeout, args.check_js_header, args.retries, args.backoff)
        return u, ok, status, ctype, final_url

    print(f"[*] Checking {len(urls)} URLs with {args.workers} workers ...")

    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for u, ok, status, ctype, final_url in ex.map(worker, urls):
            rows.append([u, ok, status, ctype, final_url])
            if ok:
                active.append(u)
                print(f"[OK]  {u}  ({status})")
            else:
                inactive.append(u)
                print(f"[BAD] {u}  ({status})")

    with open("active_js_urls.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(active) + ("\n" if active else ""))
    with open("inactive_js_urls.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(inactive) + ("\n" if inactive else ""))

    with open(args.csv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["url", "active", "status", "content_type", "final_url"])
        w.writerows(rows)

    print("\n[*] Saved:")
    print(f"    active_js_urls.txt   ({len(active)})")
    print(f"    inactive_js_urls.txt ({len(inactive)})")
    print(f"    {args.csv} ({len(rows)} rows)")

    if args.download and active:
        print(f"\n[*] Downloading {len(active)} active files to: {args.outdir}")
        for u in active:
            try:
                path, size, ctype = download_file(u, args.outdir, args.timeout)
                print(f"[DL] {u} -> {path} ({size} bytes, {ctype})")
            except Exception as e:
                print(f"[DL-FAIL] {u} -> {e}")


if __name__ == "__main__":
    main()
