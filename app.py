import ipaddress
import logging
import threading
import time

import requests
from flask import Flask, render_template, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
from src.feeds import discover_ipv4_feeds
from src.edl_checker import preload_subnets, check_ip_against_cache

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1, x_proto=1, x_host=1, x_port=1)
limiter = Limiter(get_remote_address, app=app, default_limits=["30 per minute"])

CACHE_REFRESH_INTERVAL = 6 * 3600  # 6 hours

_cache = {
    "feeds": [],
    "subnets": {},
    "ready": threading.Event(),
    "lock": threading.Lock(),
}


def _refresh_cache():
    logger.info("Refreshing feed cache...")
    try:
        feeds = discover_ipv4_feeds()
        subnets = preload_subnets(feeds)
        with _cache["lock"]:
            _cache["feeds"] = feeds
            _cache["subnets"] = subnets
        _cache["ready"].set()
        logger.info(f"Cache ready: {len(feeds)} feeds loaded.")
    except Exception:
        logger.exception("Failed to refresh feed cache")


def _cache_refresh_loop():
    _refresh_cache()
    while True:
        time.sleep(CACHE_REFRESH_INTERVAL)
        _refresh_cache()


threading.Thread(target=_cache_refresh_loop, daemon=True).start()


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/lookup", methods=["POST"])
def lookup():
    if not _cache["ready"].wait(timeout=120):
        return jsonify({"error": "Feed cache is still loading, please retry in a moment."}), 503

    ip_str = request.form.get("ip", "").strip()
    if not ip_str:
        return jsonify({"error": "Please provide an IP address or network"}), 400

    try:
        if "/" in ip_str:
            target = ipaddress.IPv4Network(ip_str, strict=False)
        else:
            target = ipaddress.IPv4Address(ip_str)
    except ValueError:
        return jsonify({"error": f"Invalid IPv4 address or network: {ip_str}"}), 400

    try:
        with _cache["lock"]:
            feeds = _cache["feeds"]
            subnets = _cache["subnets"]

        matches = check_ip_against_cache(target, feeds, subnets)

        return jsonify({
            "target": str(target),
            "feeds_checked": len(feeds),
            "matches": [
                {"name": name, "url": url, "subnets": [str(s) for s in matched_subnets]}
                for name, url, matched_subnets in matches
            ],
        })
    except Exception:
        logger.exception("Lookup error")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
