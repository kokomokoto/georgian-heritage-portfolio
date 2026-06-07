import os

from flask import render_template

from app import app


def main() -> None:
    ga_id = (os.environ.get("GA_MEASUREMENT_ID") or "").strip()
    if not ga_id:
        raise SystemExit("GA_MEASUREMENT_ID is not set")

    with app.test_request_context("/"):
        html = render_template("base.html")

    has_gtag_src = f"googletagmanager.com/gtag/js?id={ga_id}" in html
    has_config = f"gtag('config', '{ga_id}')" in html

    print("GA_MEASUREMENT_ID:", ga_id)
    print("Injected gtag.js:", has_gtag_src)
    print("Injected gtag config:", has_config)


if __name__ == "__main__":
    main()
