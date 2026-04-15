"""Community module schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Category ──────────────────────────────────────────────

class CategoryInfo(BaseModel):
    value: str
    label: str
    color: str = "#909399"


# ── Author ────────────────────────────────────────────────

class AuthorInfo(BaseModel):
    id: int
    username: str


# ── Post ──────────────────────────────────────────────────

class PostListResponse(BaseModel):
    id: int
    title: str
    content: str
    summary: Optional[str] = None
    tags: list[str] = []
    category: Optional[CategoryInfo] = None
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    is_essence: bool = False
    is_top: bool = False
    created_at: str
    updated_at: str
    author: AuthorInfo
    is_liked: Optional[bool] = None
    is_favorited: Optional[bool] = None


class PostPaginatedResponse(BaseModel):
    list: list[PostListResponse]
    total: int
    page: int
    per_page: int
    total_pages: Optional[int] = None


class PostCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    summary: Optional[str] = None
    tags: Optional[list[str]] = None


class PostUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    summary: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None


# ── Comment ───────────────────────────────────────────────

class CommentResponse(BaseModel):
    id: int
    content: str
    like_count: int = 0
    created_at: str
    author: AuthorInfo
    replies: list["CommentResponse"] = []
    is_liked: Optional[bool] = None


class CommentCreateRequest(BaseModel):
    content: str = Field(..., min_length=1)
    parent_id: Optional[int] = None


# ── Action ────────────────────────────────────────────────

class LikeResponse(BaseModel):
    message: str
    action: str  # "liked" / "unliked"
    like_count: int


class FavoriteResponse(BaseModel):
    message: str
    action: str  # "favorited" / "unfavorited"


# ── Stats ─────────────────────────────────────────────────

class CommunityStatsResponse(BaseModel):
    total_posts: int
    total_users: int
    today_posts: int
    online_users: int


# ── Admin ─────────────────────────────────────────────────

class AdminPostListResponse(BaseModel):
    list: list[PostListResponse]
    total: int
    page: int
    per_page: int


class AdminCommentResponse(BaseModel):
    id: int
    content: str
    like_count: int = 0
    created_at: str
    author: AuthorInfo
    post_id: int


class AdminCommentListResponse(BaseModel):
    list: list[AdminCommentResponse]
    total: int
    page: int
    per_page: int
