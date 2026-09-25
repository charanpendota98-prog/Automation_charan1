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
        # v94: last uploaded media (schema image property kosam)
        self.last_media_id = None
        self.last_media_url = ""
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
        """Return the published count for inventory reporting; no Google threshold claim."""
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

    def get_page_for_edit(self, slug: str) -> Optional[Dict]:
        """Read a page body so managed-page commands can preserve manual edits."""
        r = self._request("GET", "pages", params={
            "slug": slug, "status": "publish,draft",
            "context": "edit", "per_page": 1,
        })
        if not r.ok or not r.json():
            return None
        page = r.json()[0]
        content = page.get("content") or {}
        title = page.get("title") or {}
        return {
            "id": page.get("id"), "link": page.get("link"),
            "content": content.get("raw") or content.get("rendered") or "",
            "title": title.get("raw") or title.get("rendered") or "",
        }

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

    # ------------------------------------------------- v28: themes + plugins
    def list_themes(self) -> List[Dict]:
        """Return a small, normalized view of installed WP themes.

        The endpoint is read-only here: theme activation is intentionally not
        automated because a theme switch can change menus, widgets, and layout.
        """
        r = self._request("GET", "themes", params={
            "context": "edit", "per_page": 100,
            "_fields": "stylesheet,template,name,slug,status,version,author",
        })
        if not r.ok:
            return []
        themes = []
        for item in r.json():
            author = item.get("author")
            if isinstance(author, dict):
                author = author.get("raw") or author.get("rendered") or ""
            themes.append({
                "stylesheet": item.get("stylesheet", ""),
                "template": item.get("template", ""),
                "name": item.get("name", ""),
                "slug": item.get("slug", ""),
                "status": item.get("status", ""),
                "version": item.get("version", ""),
                "author": author or "",
            })
        return themes

    def list_plugins(self) -> List[Dict]:
        """Return installed plugins in a stable shape for setup audits."""
        r = self._request("GET", "plugins", params={
            "context": "edit", "per_page": 100,
            "_fields": "plugin,name,status,version,textdomain,slug",
        })
        if not r.ok:
            return []
        plugins = []
        for item in r.json():
            plugin_id = item.get("plugin", "")
            slug = item.get("slug", "") or plugin_id.split("/", 1)[0]
            plugins.append({
                "plugin": plugin_id,
                "slug": slug.lower(),
                "name": item.get("name", ""),
                "status": item.get("status", "inactive"),
                "version": item.get("version", ""),
                "textdomain": item.get("textdomain", ""),
            })
        return plugins

    def install_plugin(self, slug: str, activate: bool = True) -> Dict:
        """Install one WordPress.org plugin and optionally activate it.

        This method never accepts an arbitrary download URL; callers pass a
        reviewed WordPress.org slug. A separate activation request handles WP
        versions that ignore ``status`` during installation.
        """
        slug = (slug or "").strip().lower()
        if not slug or "/" in slug or " " in slug:
            raise ValueError("plugin slug must be a simple WordPress.org slug")
        r = self._request("POST", "plugins", json={
            "slug": slug, "status": "active" if activate else "inactive",
        })
        if r.status_code not in (200, 201):
            raise WordPressError(
                f"Plugin '{slug}' install failed: HTTP {r.status_code}: {r.text[:300]}"
            )
        data = r.json() if r.content else {}
        plugin_id = data.get("plugin", "")
        status = data.get("status", "active" if activate else "inactive")
        if activate and status != "active" and plugin_id:
            ar = self._request("POST", f"plugins/{plugin_id}",
                               json={"status": "active"})
            if ar.status_code not in (200, 201):
                raise WordPressError(
                    f"Plugin '{slug}' activation failed: HTTP "
                    f"{ar.status_code}: {ar.text[:300]}"
                )
            data = ar.json() if ar.content else data
        return {
            "plugin": data.get("plugin", plugin_id),
            "slug": slug,
            "name": data.get("name", slug),
            "status": data.get("status", status),
            "installed": True,
        }

    def activate_plugin(self, plugin_id: str) -> Dict:
        """Activate an already installed plugin by WP plugin identifier."""
        if not plugin_id or ".." in plugin_id:
            raise ValueError("invalid plugin identifier")
        r = self._request("POST", f"plugins/{plugin_id}",
                          json={"status": "active"})
        if r.status_code not in (200, 201):
            raise WordPressError(
                f"Plugin activation failed: HTTP {r.status_code}: {r.text[:300]}"
            )
        data = r.json() if r.content else {}
        return {"plugin": data.get("plugin", plugin_id),
                "name": data.get("name", ""),
                "status": data.get("status", "active"),
                "installed": False}

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

    #: v96 BUG FIX — file extension ↔ MIME map. Ippati varaku `.webp` files
    #: kuda `image/jpeg` ga upload ayyevi (v81 lo webp default ayyaka vachina
    #: regression). WordPress `wp_check_filetype_and_ext()` mismatch valla
    #: hosting batti upload REJECT avvachu ("Sorry, you are not allowed to
    #: upload this file type") → post featured image ledu → Discover/Article
    #: schema image ledu. Ippudu extension nunchi real MIME pampistunnam.
    _MIME = {
        ".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif", ".avif": "image/avif",
    }

    def upload_media(self, image_path: Path, title: str, alt_text: str,
                     filename: str = "") -> Optional[int]:
        """Featured image upload. `filename` ivvakapote path name vadatam
        (v96: SEO thumbnail name — seo.image_filename())."""
        name = (filename or image_path.name).strip() or image_path.name
        mime = self._MIME.get(Path(name).suffix.lower(), "image/jpeg")
        try:
            with open(image_path, "rb") as fh:
                resp = self._request(
                    "POST",
                    "media",
                    files={"file": (name, fh, mime)},
                    data={"title": title, "alt_text": alt_text},
                    headers={
                        "Content-Disposition": f'attachment; filename="{name}"'
                    },
                )
            if resp.status_code not in (200, 201):
                log.error("Media upload failed: %s %s", resp.status_code, resp.text[:300])
                return None
            data = resp.json()
            media_id = data["id"]
            # v94: source_url ni cache cheyyadam — Article schema ki `image`
            # property kavali (Google Article rich result ki adi REQUIRED).
            # Ippati varaku idi discard ayyedi, anduke schema lo image ledu.
            self.last_media_url = str(data.get("source_url") or "")
            self.last_media_id = media_id
            log.info("Uploaded featured image id=%s url=%s", media_id, self.last_media_url)
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
        except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
            log.debug("block skip: %s", exc)
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

    def write_seo_meta(self, post_id: int, meta: Dict[str, object]) -> bool:
        """Write Rank Math fields through StudentUp's authenticated bridge.

        WordPress' generic posts endpoint can reject Rank Math keys depending on
        plugin registration order. The bridge allow-lists keys server-side and
        uses the same ``edit_post`` capability, so this is a safe deterministic
        fallback rather than silently publishing without SEO fields.
        """
        # First use Rank Math's own authenticated endpoint. Application Password
        # auth works on current WordPress/Rank Math installs and avoids depending
        # on the active theme. The plugin still performs its own sanitization.
        native_url = f"{self.site}/wp-json/rankmath/v1/updateMeta"
        native_ok = False
        try:
            native = self.session.post(native_url, json={
                "objectID": int(post_id), "objectType": "post", "meta": meta,
            }, timeout=config.HTTP_TIMEOUT)
            native_data = {}
            try:
                native_data = native.json() if native.content else {}
            except ValueError:
                native_data = {}
            native_ok = (native.status_code in (200, 201)
                         and native_data.get("success", True) is not False)
            if native_ok:
                log.info("Rank Math native meta endpoint accepted post %s", post_id)
            else:
                log.info("Rank Math native endpoint unavailable (%s) — StudentUp bridge try",
                         native.status_code)
        except requests.RequestException as exc:
            log.info("Rank Math native endpoint failed (%s) — bridge try", exc)

        url = f"{self.site}/wp-json/studentup/v1/posts/{int(post_id)}/seo"
        try:
            resp = self.session.post(
                url, json={"meta": meta}, timeout=config.HTTP_TIMEOUT)
        except requests.RequestException as exc:
            log.warning("SEO bridge request failed: %s", exc)
            return native_ok
        if resp.status_code != 200:
            log.warning("SEO bridge unavailable: HTTP %s: %s",
                        resp.status_code, resp.text[:240])
            return native_ok
        try:
            data = resp.json()
        except ValueError:
            return native_ok
        saved = data.get("saved") or {}
        bridge_ok = bool(data.get("ok")) and all(
            bool(str(saved.get(key, "")).strip()) for key in meta
        )
        # A native success may have saved fields before the bridge response;
        # the following readback remains the source of truth for each value.
        return bridge_ok or native_ok

    def read_rankmath_state(self, post_id: int) -> Dict:
        """Read persisted fields and Rank Math's own stored score, if available.

        The score is read-only. This client never calculates or writes it, so an
        absent value remains ``None`` rather than being replaced by a local guess.
        """
        url = f"{self.site}/wp-json/studentup/v1/posts/{int(post_id)}/seo"
        try:
            resp = self.session.get(url, timeout=config.HTTP_TIMEOUT)
            if resp.status_code != 200:
                return {"ok": False, "rank_math_ui_score": None,
                        "reason": f"HTTP {resp.status_code}"}
            data = resp.json()
            score = data.get("rank_math_ui_score")
            return {"ok": bool(data.get("ok")), "fields": data.get("fields") or {},
                    "rank_math_ui_score": int(score) if score is not None else None,
                    "score_note": data.get("score_note", "")}
        except (requests.RequestException, ValueError, TypeError):
            return {"ok": False, "rank_math_ui_score": None,
                    "reason": "bridge read failed"}

    def set_post_status(self, post_id: int, status: str) -> Dict:
        """Promote a verified staged draft (or move a post back to draft)."""
        if status not in {"draft", "pending", "private", "publish"}:
            raise ValueError(f"unsupported post status: {status}")
        resp = self._request("POST", f"posts/{int(post_id)}", json={"status": status})
        if resp.status_code not in (200, 201):
            raise WordPressError(
                f"Post status update failed: HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        return {"id": data.get("id"), "link": data.get("link"),
                "status": data.get("status")}

    def verify_meta(self, post_id: int, keys: List[str]) -> Dict[str, bool]:
        """Post lo meta keys nijamainaa land ayyaya? (SEO silent-fail pattadaniki).

        Returns {key: True/False}. Post read fail ayithe anni False.
        """
        try:
            data = self.get_post(post_id)
        except WordPressError:
            return {k: False for k in keys}
        if not isinstance(data, dict):
            return {k: False for k in keys}
        meta = data.get("meta") or {}
        if not isinstance(meta, dict):
            meta = {}
        out = {}
        for k in keys:
            val = meta.get(k)
            if isinstance(val, list):
                val = ", ".join(str(x) for x in val)
            out[k] = bool(str(val or "").strip())
        return out

    def verify_rankmath_meta(self, post_id: int, keys: List[str]) -> Dict[str, bool]:
        """Verify through core REST first, then the SEO bridge.

        Some WordPress/Rank Math combinations save the fields correctly but do
        not expose them in ``wp/v2/posts/<id>?context=edit``. Treating that
        read-path limitation as a missing field caused the bot to report empty
        SEO keys even after the authenticated bridge had saved them.
        """
        result = self.verify_meta(post_id, keys)
        if all(result.values()):
            return result
        try:
            state = self.read_rankmath_state(post_id)
            fields = state.get("fields") or {}
            for key in keys:
                if fields.get(key):
                    result[key] = True
        except Exception:  # noqa: BLE001 — preserve the core REST result
            log.debug("Rank Math bridge readback unavailable", exc_info=True)
        return result

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
