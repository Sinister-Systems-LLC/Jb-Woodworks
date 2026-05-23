# Author: RKOJ-ELENO :: 2026-05-23
"""JB Woodworks - Flask app entrypoint."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, url_for

APP_ROOT = Path(__file__).resolve().parent
DATA_DIR = APP_ROOT / "data"

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


def _load_json(name: str):
    path = DATA_DIR / name
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


@app.context_processor
def inject_globals():
    return {
        "site": {
            "name": "JB Woodworks",
            "tagline": "Premium Craftsmanship. Built to Last.",
            "subtagline": "We specialize in custom woodworking, from stunning decks and boat docks to unique furniture and pergolas. Transforming your vision into a reality.",
            "phone": "(407) 561-1453",
            "phone_tel": "4075611453",
            "email": "jbwoodworks8@gmail.com",
            "form_action": "https://formsubmit.co/jbwoodworks8@gmail.com",
            "service_area": "Orlando, Florida and surrounding areas",
            "year": datetime.now().year,
            "instagram": "https://www.instagram.com/jb.woodworkss",
            "facebook": "https://www.facebook.com/people/JB-Woodworks/61581118061434",
            "tiktok": "https://www.tiktok.com/@jbwoodworks_",
            "twitter": "https://x.com/jbwoodworks8",
        }
    }


@app.route("/")
def index():
    return render_template(
        "index.html",
        services=_load_json("services.json"),
        portfolio=_load_json("portfolio.json")[:4],
        hero_media=_load_json("hero_media.json"),
        faq=_load_json("faq.json"),
    )


@app.route("/services")
def services():
    return render_template("services.html", services=_load_json("services.json"))


@app.route("/portfolio")
def portfolio():
    return render_template("portfolio.html", portfolio=_load_json("portfolio.json"))


@app.route("/portfolio/<slug>")
def portfolio_item(slug):
    items = _load_json("portfolio.json")
    item = next((x for x in items if x["slug"] == slug), None)
    if item is None:
        abort(404)
    return render_template("portfolio_item.html", item=item)


@app.route("/about")
def about():
    return render_template("about.html", faq=_load_json("faq.json"))


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        # Real implementation would email/queue this. Logged to instance/ for now.
        payload = {
            "name": request.form.get("name", "").strip(),
            "email": request.form.get("email", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "project": request.form.get("project", "").strip(),
            "message": request.form.get("message", "").strip(),
            "ts": datetime.utcnow().isoformat() + "Z",
        }
        inbox = APP_ROOT / "instance" / "inquiries.jsonl"
        inbox.parent.mkdir(parents=True, exist_ok=True)
        with inbox.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload) + "\n")
        return redirect(url_for("contact_thanks"))
    return render_template("contact.html")


@app.route("/contact/thanks")
def contact_thanks():
    return render_template("contact_thanks.html")


@app.route("/healthz")
def healthz():
    return {"ok": True, "ts": datetime.utcnow().isoformat() + "Z"}


@app.route("/robots.txt")
def robots():
    body = "User-agent: *\nAllow: /\nSitemap: {}sitemap.xml\n".format(request.host_url)
    return body, 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.route("/sitemap.xml")
def sitemap():
    paths = ["", "services", "portfolio", "about", "contact"]
    for item in _load_json("portfolio.json"):
        paths.append("portfolio/" + item["slug"])
    today = datetime.utcnow().date().isoformat()
    urls = "\n".join(
        '  <url><loc>{}{}</loc><lastmod>{}</lastmod></url>'.format(request.host_url, p, today)
        for p in paths
    )
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + urls + "\n</urlset>\n"
    )
    return body, 200, {"Content-Type": "application/xml; charset=utf-8"}


@app.after_request
def add_security_headers(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    resp.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    return resp


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
