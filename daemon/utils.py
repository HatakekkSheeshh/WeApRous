#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

from urllib.parse import parse_qs, urlparse, unquote
import json 

def parse_form_or_json(raw_body):
    """
    - JSON:
        {
            "username": "admin",
            "password": "password"
        }
    - form-url-encoded:
        username=admin&password=password
    Return: dict {"username": "...", "password": "..."}.
    """

    if raw_body is None:
        return {}

    # bytes -> str
    if isinstance(raw_body, (bytes, bytearray)):
        raw_body = raw_body.decode("utf-8", "ignore")

    if not isinstance(raw_body, str):
        return {}
    raw_body = raw_body.lstrip("\ufeff").strip()
    if not raw_body or raw_body == "anonymous":
        return {}

    looks_like_form = (
        ("=" in raw_body) and
        not raw_body.lstrip().startswith("{")
    )

    if looks_like_form:
        parsed = parse_qs(raw_body, keep_blank_values=True)
        return {k: v[0] if v else "" for k, v in parsed.items()}

    try:
        return json.loads(raw_body)
    except Exception:
        return {}

def get_auth_from_url(url):
    parsed = urlparse(url)
    try:
        user = unquote(parsed.username) if parsed.username else ""
        pwd  = unquote(parsed.password) if parsed.password else ""
    except (AttributeError, TypeError):
        user, pwd = "", ""
    return {"username": user, "password": pwd}

