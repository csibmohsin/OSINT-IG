"""Independent Instagram data provider backed by instagrapi."""
from pathlib import Path
from typing import Optional

from osint_ig.config.settings import DEFAULT_SESSION_PATH
from osint_ig.instagram.auth import ProviderBackendError


class InstagramProvider:
    """Normalized Instagram client wrapper around an authenticated ``instagrapi.Client``."""

    def __init__(self, username: str = "", password: str = "", session_path: str = DEFAULT_SESSION_PATH):
        session_file = Path(session_path)
        if not session_file.exists():
            raise ProviderBackendError(
                f"No saved Instagram session at {session_path}. Configure it in "
                "Settings -> Instagram Connection or run `python -m osint_ig auth --sessionid <cookie>`."
            )

        from instagrapi import Client

        self._cl = Client()
        self._cl.load_settings(session_file)
        if username:
            self._cl.username = username
        if password:
            self._cl.password = password
        if not self._cl.user_id:
            if not (username and password):
                raise ProviderBackendError(
                    "Saved session has no active user_id and no username/password configured."
                )
            try:
                self._cl.login(username, password)
            except Exception as exc:
                raise ProviderBackendError(
                    f"Instagram login failed: {exc}. Please update your session in {session_path}."
                ) from exc

    # ---- Normalization helpers ----

    @staticmethod
    def _full_user_to_dict(user) -> dict:
        d = {
            "pk": user.pk,
            "username": user.username,
            "full_name": user.full_name,
            "is_private": user.is_private,
            "is_verified": user.is_verified,
            "biography": getattr(user, "biography", None),
            "follower_count": getattr(user, "follower_count", None),
            "following_count": getattr(user, "following_count", None),
            "media_count": getattr(user, "media_count", None),
            "is_business": getattr(user, "is_business", None),
            "public_email": getattr(user, "public_email", None),
            "contact_phone_number": getattr(user, "contact_phone_number", None),
            "city_name": getattr(user, "city_name", None),
            "address_street": getattr(user, "address_street", None),
            "category": getattr(user, "category", None),
        }
        for field in (
            "external_url",
            "account_type",
            "category_name",
            "business_category_name",
            "business_contact_method",
            "public_phone_country_code",
            "public_phone_number",
            "zip",
            "latitude",
            "longitude",
            "instagram_location_id",
        ):
            value = getattr(user, field, None)
            if value not in (None, ""):
                d[field] = str(value) if field == "external_url" else value
        pic_hd = getattr(user, "profile_pic_url_hd", None)
        if pic_hd:
            d["hd_profile_pic_url_info"] = {"url": str(pic_hd)}
        return d

    @staticmethod
    def _short_user_to_dict(user) -> dict:
        return {
            "pk": user.pk,
            "username": user.username,
            "full_name": user.full_name,
            "is_private": user.is_private,
            "is_verified": user.is_verified,
        }

    @staticmethod
    def _media_to_dict(media) -> dict:
        d = {
            "id": media.id,
            "code": media.code,
            "product_type": media.product_type,
            "comment_count": media.comment_count or 0,
            "like_count": media.like_count or 0,
            "media_type": media.media_type,
            "accessibility_caption": getattr(media, "accessibility_caption", None),
            "caption": {"text": media.caption_text} if media.caption_text else None,
            "taken_at": int(media.taken_at.timestamp()) if media.taken_at else None,
            "user": InstagramProvider._short_user_to_dict(media.user) if media.user else {},
            "usertags": [
                {
                    "user": {
                        "pk": tag.user.pk,
                        "username": tag.user.username,
                        "full_name": tag.user.full_name,
                    }
                }
                for tag in (media.usertags or [])
                if tag.user
            ],
        }
        if media.location and media.location.lat is not None and media.location.lng is not None:
            d["location"] = {"lat": media.location.lat, "lng": media.location.lng}

        if media.media_type == 8 and media.resources:
            d["carousel_media"] = []
            for resource in media.resources:
                item = {
                    "id": resource.pk,
                    "media_type": resource.media_type,
                    "accessibility_caption": getattr(resource, "accessibility_caption", None),
                }
                if resource.thumbnail_url:
                    item["image_versions2"] = {"candidates": [{"url": str(resource.thumbnail_url)}]}
                if resource.media_type == 2 and resource.video_url:
                    item["video_versions"] = [{"url": str(resource.video_url)}]
                d["carousel_media"].append(item)
        else:
            candidates = []
            if media.image_versions2 and media.image_versions2.candidates:
                candidates = [{"url": str(c.url)} for c in media.image_versions2.candidates]
            elif media.thumbnail_url:
                candidates = [{"url": str(media.thumbnail_url)}]
            if candidates:
                d["image_versions2"] = {"candidates": candidates}
            if media.media_type == 2 and media.video_url:
                d["video_versions"] = [{"url": str(media.video_url)}]
        return d

    @staticmethod
    def _comment_to_dict(comment) -> dict:
        user = comment.user
        return {
            "user_id": user.pk if user else None,
            "user": {"pk": user.pk, "username": user.username, "full_name": user.full_name} if user else {},
            "text": comment.text,
        }

    @staticmethod
    def _story_to_dict(story) -> dict:
        d = {"id": story.id, "media_type": story.media_type}
        if story.thumbnail_url:
            d["image_versions2"] = {"candidates": [{"url": str(story.thumbnail_url)}]}
        if story.media_type == 2 and story.video_url:
            d["video_versions"] = [{"url": str(story.video_url)}]
        return d

    # ---- Provider API methods ----

    def fetch_profile_by_username(self, username: str) -> dict:
        try:
            user = self._cl.user_info_by_username_v1(username)
        except Exception as exc:
            if "not found" in str(exc).lower() or type(exc).__name__ == "UserNotFound":
                return {"detail": str(exc)}
            return {"error": str(exc)}
        return {"user": self._full_user_to_dict(user)}

    def fetch_profile_by_id(self, user_id) -> dict:
        try:
            user = self._cl.user_info_v1(str(user_id))
        except Exception as exc:
            return {"error": str(exc)}
        return {"user": self._full_user_to_dict(user)}

    def fetch_user_media_page(self, user_id, next_page_id: Optional[str] = None) -> dict:
        medias, cursor = self._cl.user_medias_paginated_v1(str(user_id), amount=33, end_cursor=next_page_id or "")
        return {
            "response": {"items": [self._media_to_dict(m) for m in medias]},
            "next_page_id": cursor or None,
        }

    def fetch_media_comments_page(self, media_id, page_id: str = "") -> dict:
        try:
            comments, cursor = self._cl.media_comments_chunk(str(media_id), max_amount=20, min_id=page_id or None)
        except Exception as exc:
            if type(exc).__name__ == "MediaNotFound":
                raise RuntimeError(f"Entries not found: {exc}") from exc
            raise
        return {
            "response": {"comments": [self._comment_to_dict(c) for c in comments]},
            "next_page_id": cursor or None,
        }

    def fetch_followers_page(self, user_id, page_id: Optional[str] = None) -> dict:
        users, cursor = self._cl.user_followers_v1_chunk(str(user_id), max_amount=50, max_id=page_id or "")
        return {
            "response": {"users": [self._short_user_to_dict(u) for u in users]},
            "next_page_id": cursor or None,
        }

    def fetch_following_page(self, user_id, page_id: Optional[str] = None) -> dict:
        users, cursor = self._cl.user_following_v1_chunk(str(user_id), max_amount=50, max_id=page_id or "")
        return {
            "response": {"users": [self._short_user_to_dict(u) for u in users]},
            "next_page_id": cursor or None,
        }

    def fetch_tagged_media_page(self, user_id, page_id: str = "") -> dict:
        medias, cursor = self._cl.usertag_medias_paginated_v1(str(user_id), amount=33, end_cursor=page_id or "")
        return {
            "response": {"items": [self._media_to_dict(m) for m in medias]},
            "next_page_id": cursor or None,
        }

    def fetch_user_stories(self, user_id) -> dict:
        stories = self._cl.user_stories_v1(str(user_id))
        return {"reel": {"items": [self._story_to_dict(s) for s in stories]}}

    def fetch_user_highlights(self, user_id, **kwargs) -> dict:
        tray = []
        for h in self._cl.user_highlights(str(user_id)):
            cover = getattr(h, "cover_media", None)
            url = getattr(getattr(cover, "cropped_image_version", None), "url", None) if cover else None
            tray.append({
                "id": f"highlight:{h.pk}",
                "title": h.title,
                "media_count": h.media_count,
                "cover_media": {"cropped_image_version": {"url": str(url)} if url else {}},
                "created_at": None,
                "latest_reel_media": None,
            })
        return {"response": {"tray": tray}}

    def _hashtag_chunk(self, name: str, tab_key: str, page_id) -> dict:
        chunked = getattr(self._cl, "hashtag_medias_v1_chunk", None)
        if chunked is not None:
            medias, cursor = chunked(name, max_amount=30, tab_key=tab_key, max_id=page_id or None)
        else:
            one_shot = getattr(self._cl, f"hashtag_medias_{tab_key}_v1")
            medias = one_shot(name, amount=30) if not page_id else []
            cursor = None
        return {
            "response": {"items": [self._media_to_dict(m) for m in medias]},
            "next_page_id": cursor or None,
        }

    def fetch_hashtag_media(self, name: str, sort: str = "recent", page_id=None, **kwargs) -> dict:
        tab = "top" if sort == "top" else "recent"
        return self._hashtag_chunk(name, tab, page_id)

    def search_places(self, query: str, **kwargs) -> dict:
        places = self._cl.fbsearch_places(query)
        return {
            "items": [
                {
                    "location": {
                        "pk": location.pk,
                        "name": location.name,
                        "address": location.address,
                        "city": location.city,
                        "lat": location.lat,
                        "lng": location.lng,
                    }
                }
                for location in places
                if location.pk
            ]
        }

    def fetch_location_media(self, location_pk, max_id=None, **kwargs) -> list:
        chunked = getattr(self._cl, "location_medias_v1_chunk", None)
        if chunked is not None:
            medias, cursor = chunked(int(location_pk), max_amount=30, tab_key="recent", max_id=max_id or None)
        else:
            medias = self._cl.location_medias_recent_v1(int(location_pk), amount=30) if not max_id else []
            cursor = None
        return [[self._media_to_dict(m) for m in medias], cursor or None]

    def resolve_media_pk_from_url(self, url: str, **kwargs) -> str:
        return str(self._cl.media_pk_from_url(url))

    def resolve_media_pk_from_code(self, code: str, **kwargs) -> str:
        return str(self._cl.media_pk_from_code(code))
