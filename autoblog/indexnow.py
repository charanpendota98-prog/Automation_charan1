"""IndexNow protocol — Bing/Yandex ki instant indexing ping.

Google Indexing API separate auth kavali; IndexNow free & key-based.
Key file: https://studentup.in/{KEY}.key lo unna file hosting cheyali
(cPanel/FTP lo okkasari — README chudandi). Key set unte publish
appudu automatic ga URL submit avtundi.
"""

import logging
from urllib.parse import urlparse

import requests

from . import config

log = logging.getLogger("autoblog.indexnow")

ENDPOINT = "https://api.indexnow.org/indexnow"


def submit(urls) -> bool:
    key = config.INDEXNOW_KEY
    if not key:
        return False
    if isinstance(urls, str):
        urls = [urls]
    host = urlparse(config.WP_SITE).netloc.replace("www.", "")
    payload = {
        "host": host,
        "key": key,
        "keyLocation": f"{config.WP_SITE}/{key}.key",
        "urlList": urls[:100],
    }
    try:
        resp = requests.post(ENDPOINT, json=payload, timeout=config.HTTP_TIMEOUT)
        # 200/202 = accepted; 400/403/422 = key/host problem; 429 = quota
        if resp.status_code in (200, 202):
            log.info("IndexNow submitted %d URLs ✔", len(urls))
            return True
        log.warning("IndexNow %s: %s", resp.status_code, resp.text[:120])
    except Exception:
        log.exception("IndexNow submit failed")
    return False
