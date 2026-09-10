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

    def published_count(self) -> int:
        """X-WP-Total header — AdSense '20+ substantial posts' readiness."""
        try:
            r = self._request("GET", "posts",
                              params={"status": "publish", "per_page": 1,
                                      "_fields": "id"})
            return int(r.headers.get("X-WP-Total", 0)) if r.ok else 0
        except Exception:
            return 0

    def search_posts(self, term: str, per_page: int = 10) -> List[Dict]:
        """Published posts matching term (hub pages kosam)."""
        try:
            r = self._request("GET", "posts", params={
                "search": term, "status": "publish", "per_page": per_page,
                "orderby": "date", "order": "desc",
                "_fields": "id,link,title,date"})
            if not r.ok:
                return []
            return [{"id": p.get("id"), "link": p.get("link", ""),
                     "title": (p.get("title") or {}).get("rendered", ""),
                     "date": p.get("date", "")} for p in r.json()]
        except Exception:
            log.exception("search_posts failed")
            return []

    def get_page_by_slug(self, slug: str) -> Optional[Dict]:
        r = self._request("GET", "pages",
                          params={"slug": slug, "status": "publish,draft",
                                  "per_page": 1})
        if r.ok and r.json():
            pg = r.json()[0]
            return {"id": pg.get("id"), "link": pg.get("link")}
        return None

    def upsert_page(self, title: str, content_html: str, slug: str) -> Dict:
        """Slug-based idempotent page create/update (hub pages)."""
        existing = self.get_page_by_slug(slug)
        if existing:
            r = self._request("PUT", f"pages/{existing['id']}",
                              json={"title": title, "content": content_html})
        else:
            r = self._request("POST", "pages",
                              json={"title": title, "content": content_html,
                                    "slug": slug, "status": "publish"})
        r.raise_for_status()
        data = r.json()
        return {"id": data.get("id"), "link": data.get("link")}

    # ------------------------------------------------- v22: site admin (REST)
    def get_settings(self) -> Dict:
        r = self._request("GET", "settings")
        return r.json() if r.ok else {}

    def save_settings(self, payload: Dict) -> bool:
        r = self._request("POST", "settings", json=payload)
        return r.ok

    def rest_namespaces(self) -> List[str]:
        try:
            r = self.session.get(f"{self.site}/wp-json/", timeout=30)
            return list(r.json().get("namespaces", [])) if r.ok else []
        except Exception:
            return []

    def public_get_status(self, path: str) -> tuple:
        """Unauthenticated GET site+path -> (status_code, first 4KB text)."""
        try:
            r = self.session.get(f"{self.site}{path}", timeout=30)
            return r.status_code, (r.text or "")[:4000]
        except Exception:
            return 0, ""

    def list_categories(self) -> List[Dict]:
        r = self._request("GET", "categories",
                          params={"per_page": 60, "orderby": "count",
                                  "order": "desc"})
        if not r.ok:
            return []
        return [{"id": c["id"], "slug": c.get("slug", ""),
                 "name": c.get("name", ""),
                 "description": (c.get("description") or "").strip(),
                 "count": c.get("count", 0)} for c in r.json()]

    def update_category(self, cat_id: int, description: str) -> bool:
        r = self._request("POST", f"categories/{cat_id}",
                          json={"description": description})
        return r.ok

    def get_menus(self) -> List[Dict]:
        r = self._request("GET", "menus", params={"per_page": 30})
        return r.json() if r.ok else []

    def create_menu(self, name: str, slug: str) -> Optional[int]:
        r = self._request("POST", "menus", json={"name": name})
        if not r.ok:
            return None
        return r.json().get("id")

    def update_menu(self, menu_id: int, payload: Dict) -> bool:
        r = self._request("POST", f"menus/{menu_id}", json=payload)
        return r.ok

    def get_menu_items(self, menu_id: int) -> List[Dict]:
        r = self._request("GET", "menu-items",
                          params={"menus": menu_id, "per_page": 100})
        return r.json() if r.ok else []

    def add_menu_item(self, menu_id: int, object_id: int, title: str,
                      obj: str = "page") -> bool:
        r = self._request("POST", "menu-items", json={
            "menus": [menu_id], "object": obj, "object_id": object_id,
            "title": title, "status": "publish"})
        return r.ok

    def get_locations(self) -> List[Dict]:
        r = self._request("GET", "locations")
        return r.json() if r.ok else []

    def page_exists(self, slug: str) -> bool:
        r = self._request("GET", "/pages",
                          params={"slug": slug,
                                  "status": "publish,draft,pending,private",
                                  "per_page": 1})
        return r.ok and bool(r.json())

    def create_page(self, title: str, content_html: str, slug: str) -> Dict:
        """AdSense-required static page (Privacy Policy / About / Contact)."""
        r = self._request("POST", "/pages",
                          json={"title": title, "content": content_html,
                                "slug": slug, "status": "publish"})
        r.raise_for_status()
        data = r.json()
        return {"id": data.get("id"), "link": data.get("link")}

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
        cats = list(config.CATEGORIES)
        quiz_cat = getattr(config, "QUIZ_CATEGORY", "")
        if quiz_cat and quiz_cat not in cats:
            cats.append(quiz_cat)  # v26: Daily Quiz category
        return [self.get_or_create_term(c, "categories") for c in cats]

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

    def get_term_link(self, term_id: int, term_type: str = "categories") -> Optional[str]:
        """Category/tag archive URL (internal-link fallback kosam)."""
        try:
            resp = self._request("GET", f"{term_type}/{term_id}", params={"_fields": "link"})
            if resp.status_code == 200:
                return resp.json().get("link")
        except Exception:
            pass
        return None

    def get_post(self, post_id: int) -> Dict:
        """Edit context lo post teesukovali (update flow kosam)."""
        resp = self._request("GET", f"posts/{post_id}", params={"context": "edit"})
        if resp.status_code != 200:
            raise WordPressError(
                f"Post {post_id} teeyaledi: HTTP {resp.status_code}: {resp.text[:200]}")
        return resp.json()

    def update_post(
        self,
        post_id: int,
        content_html: str,
        title: Optional[str] = None,
        excerpt: Optional[str] = None,
        meta: Optional[Dict[str, str]] = None,
    ) -> Dict:
        """Existing post ni update cheyadam (URL/slug same untundi — SEO safe)."""
        payload: Dict = {"content": content_html}
        if title:
            payload["title"] = title
        if excerpt:
            payload["excerpt"] = {"raw": excerpt}
        if meta:
            payload["meta"] = meta
        resp = self._request("POST", f"posts/{post_id}", json=payload)
        if resp.status_code == 400 and meta and "meta" in resp.text.lower():
            log.info("Rank Math meta accept avvaledu — meta leni retry")
            payload.pop("meta", None)
            resp = self._request("POST", f"posts/{post_id}", json=payload)
        if resp.status_code not in (200, 201):
            raise WordPressError(
                f"Post update failed: HTTP {resp.status_code}: {resp.text[:400]}"
            )
        data = resp.json()
        return {"id": data.get("id"), "link": data.get("link"),
                "status": data.get("status")}

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
            # v22: spam/ping trackback ledu (AdSense quality + security)
            "comment_status": "closed",
            "ping_status": "closed",
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
