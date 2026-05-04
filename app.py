import ipaddress
import logging
import threading
from typing import List, Tuple, Union

import requests
from flask import Flask, render_template, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
from src.feeds import discover_ipv4_feeds
from src.edl_checker import check_ip_against_feeds

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1, x_proto=1, x_host=1, x_port=1)
limiter = Limiter(get_remote_address, app=app, default_limits=["30 per minute"])

_cache = {"feeds": None, "lock": threading.Lock()}


def get_feeds():
    if _cache["feeds"] is not None:
        return _cache["feeds"]

    with _cache["lock"]:
        if _cache["feeds"] is not None:
            return _cache["feeds"]
        feeds = discover_ipv4_feeds()
        _cache["feeds"] = feeds
        return feeds


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/lookup", methods=["POST"])
def lookup():
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
        feeds = get_feeds()
        matches = check_ip_against_feeds(target, feeds)

        return jsonify({
            "target": str(target),
            "feeds_checked": len(feeds),
            "matches": [
                {"name": name, "url": url, "subnets": [str(s) for s in subnets]}
                for name, url, subnets in matches
            ],
        })
    except Exception as e:
        logger.exception("Lookup error")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
