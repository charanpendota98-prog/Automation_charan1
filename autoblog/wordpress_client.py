"""WordPress REST API client — publishes posts to studentup.in.

Auth: WordPress Application Password (HTTP Basic).
Handles category/tag lookup+creation, featured image upload, post creation.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import requests
from requests.auth import HTTPBasicAuth

from . import config, state

log = logging.getLogger("autoblog.wp")


class WordPressAuthError(Exception):
    pass


class WordPressError(Exception):
    pass


class WordPressClient:
    def __init__(self, site: str = None, username: str = None, password: str = None):
        self.site = (site or config.WP_SITE).rstrip("/")
        self.auth = HTTPBasicAuth(username or config.WP_USERNAME, password or config.WP_APP_PASSWORD)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers["User-Agent"] = "studentup-autoblog/1.0"

    # ---------------------------------------------------------------- helpers

    def _url(self, path: str) -> str:
        return f"{self.site}/wp-json/wp/v2/{path.lstrip('/')}"

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = self._url(path)
        kwargs.setdefault("timeout", config.HTTP_TIMEOUT)
        resp = self.session.request(method, url, **kwargs)
        if resp.status_code in (401, 403):
            raise WordPressAuthError(
                f"WordPress authentication failed ({resp.status_code}). "
                "Application Password or username tappiyindi — .env file lo "
                "WP_USERNAME / WP_APP_PASSWORD check cheyandi. "
                f"Response: {resp.text[:200]}"
            )
        return resp

    def check_connection(self) -> Dict:
        """Verify credentials against /users/me."""
        resp = self._request("GET", "users/me", params={"context": "edit"})
        if resp.status_code != 200:
            raise WordPressError(f"users/me -> HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        log.info("WordPress connected as: %s (roles: %s)", data.get("name"), data.get("roles"))
        return data

    # ---------------------------------------------------------------- terms

    def get_or_create_term(self, name: str, term_type: str) -> int:
        """term_type: 'categories' or 'tags'. Returns WP term id."""
        cached = state.get_term_id(config.STATE_PATH, name, term_type)
        if cached:
            return cached

        resp = self._request("GET", term_type, params={"search": name, "per_page": 100})
        if resp.status_code == 200:
            for item in resp.json():
                if item["name"].strip().lower() == name.strip().lower():
                    state.save_term_id(config.STATE_PATH, name, term_type, item["id"])
                    return item["id"]

        resp = self._request("POST", term_type, json={"name": name})
        if resp.status_code not in (200, 201):
            # race/exists -> search again
            resp2 = self._request("GET", term_type, params={"search": name, "per_page": 100})
            if resp2.status_code == 200:
                for item in resp2.json():
                    if item["name"].strip().lower() == name.strip().lower():
                        state.save_term_id(config.STATE_PATH, name, term_type, item["id"])
                        return item["id"]
            raise WordPressError(
                f"Could not create {term_type} '{name}': HTTP {resp.status_code} {resp.text[:200]}"
            )
        term_id = resp.json()["id"]
        state.save_term_id(config.STATE_PATH, name, term_type, term_id)
        log.info("Created WP %s '%s' (id=%s)", term_type, name, term_id)
        return term_id

    def ensure_categories(self) -> List[int]:
        return [self.get_or_create_term(c, "categories") for c in config.CATEGORIES]

    # ---------------------------------------------------------------- media

    def upload_media(self, image_path: Path, title: str, alt_text: str) -> Optional[int]:
        try:
            with open(image_path, "rb") as fh:
                resp = self._request(
                    "POST",
                    "media",
                    files={"file": (image_path.name, fh, "image/jpeg")},
                    data={"title": title, "alt_text": alt_text},
                    headers={
                        "Content-Disposition": f'attachment; filename="{image_path.name}"'
                    },
                )
            if resp.status_code not in (200, 201):
                log.error("Media upload failed: %s %s", resp.status_code, resp.text[:300])
                return None
            media_id = resp.json()["id"]
            log.info("Uploaded featured image id=%s", media_id)
            return media_id
        except WordPressAuthError:
            raise
        except Exception:
            log.exception("Media upload error")
            return None

    # ---------------------------------------------------------------- post

    def get_recent_published(self, per_page: int = 8) -> List[Dict]:
        """Recent live posts — internal linking kosam."""
        try:
            resp = self._request(
                "GET", "posts",
                params={"status": "publish", "per_page": per_page, "orderby": "date",
                        "order": "desc", "_fields": "id,link,title,categories"},
            )
            if resp.status_code != 200:
                return []
            out = []
            for p in resp.json():
                title = (p.get("title") or {}).get("rendered", "")
                out.append({"id": p.get("id"), "link": p.get("link", ""),
                            "title": title, "categories": p.get("categories", [])})
            return out
        except Exception:
            log.exception("get_recent_published failed")
            return []

    def create_post(
        self,
        title: str,
        content_html: str,
        slug: str,
        category_id: Optional[int],
        tag_ids: List[int],
        excerpt: str,
        media_id: Optional[int],
        status: Optional[str] = None,
        meta: Optional[Dict[str, str]] = None,
    ) -> Dict:
        payload: Dict = {
            "title": title,
            "content": content_html,
            "status": status or config.DEFAULT_POST_STATUS,
            "excerpt": {"raw": excerpt},
        }
        if slug:
            payload["slug"] = slug
        if category_id:
            payload["categories"] = [category_id]
        if tag_ids:
            payload["tags"] = tag_ids
        if media_id:
            payload["featured_media"] = media_id
        if meta:
            payload["meta"] = meta

        resp = self._request("POST", "posts", json=payload)
        if resp.status_code == 400 and meta and "meta" in resp.text.lower():
            # Rank Math plugin active ledu -> meta keys register avvaledu;
            # post content lo SEO already untundi kabbatti meta leni retry
            log.info("Rank Math meta REST lo accept avvaledu — meta leni retry")
            payload.pop("meta", None)
            resp = self._request("POST", "posts", json=payload)
        if resp.status_code not in (200, 201):
            raise WordPressError(
                f"Post creation failed: HTTP {resp.status_code}: {resp.text[:400]}"
            )
        data = resp.json()
        return {
            "id": data.get("id"),
            "link": data.get("link"),
            "status": data.get("status"),
        }
