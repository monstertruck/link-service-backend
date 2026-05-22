# Dynamic Categories Plan

**Date:** 2026-05-22

## Goal

Allow categories to be managed dynamically (add new ones via API) and allow the `PATCH /links/{id}` endpoint to update a link's category.

## Changes

### New Files
- `app/models/category.py` — `CategoryRecord` SQLModel table (`id`, `name` unique)
- `app/crud/categories.py` — `list_categories`, `create_category`, `category_exists`

### Modified Files

#### `app/api/schemas/links.py`
- Add `CategoryCreate` request schema (`name: str`)
- Add `CategoryResponse` schema (`name: str`)
- Add `LinkUpdate` schema (`category: Optional[str]`, `status: Optional[LinkStatus]`)
- Change `LinkResponse.category` from `LinkCategory` → `str` (to allow new free-form categories)

#### `app/models/link.py`
- Change `category: LinkCategory` → `category: str`
  - No DB migration needed: SQLite stores enums as TEXT already

#### `app/crud/links.py`
- Add `update_link(session, link_id, update: LinkUpdate)` — updates category and/or status

#### `app/api/routes/links.py`
- `POST /categories` — create a new category (validates uniqueness)
- `PATCH /links/{link_id}` — update category and/or status using `LinkUpdate` body
  - Validates that the requested category exists in the categories table

#### `app/main.py`
- On startup, seed the `categories` table with the default `LinkCategory` enum values (idempotent)

## Notes
- The existing `LinkCategory` enum is kept in schemas for reference/LLM prompts but is no longer used for DB field typing
- `GET /categories` already exists and will continue to work; it will now also include dynamic categories
- The `list_links` category filter will use `str` instead of the enum
