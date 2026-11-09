# API contract

What the backend promises to the frontend. We agree on this first, so the
React app and the Flask API can be built separately and still fit together.

## Data stored in Firestore

| Path | Fields |
| --- | --- |
| `staff/{auto id}` | `name`, `email`, `department`, `active`, `created_at` |
| `links/{code}` | `staff_id`, `title`, `destination_url`, `click_count`, `active`, `created_at` |
| `links/{code}/clicks/{auto id}` | `clicked_at`, `referrer`, `user_agent` |

The short code is the document ID of a link, so the redirect can fetch it
directly and Firestore guarantees that two links never share a code.

## Endpoints

| Method | Path | Purpose | Success |
| --- | --- | --- | --- |
| GET | `/api/health` | Check that the server is up | 200 |
| GET | `/api/staff` | List staff | 200 |
| POST | `/api/staff` | Add a staff member | 201 |
| PATCH | `/api/staff/{id}` | Edit or deactivate a staff member | 200 |
| GET | `/api/links?staff_id=` | List links, optionally for one staff member | 200 |
| POST | `/api/links` | Create a link and generate its short code | 201 |
| PATCH | `/api/links/{code}` | Edit or deactivate a link | 200 |
| GET | `/api/links/{code}/clicks?limit=` | Recent clicks on a link | 200 |
| GET | `/api/stats` | Click totals, overall and per staff member | 200 |
| GET | `/r/{code}` | Log a click and redirect to the destination | 302 |

## Request bodies

| Endpoint | Fields |
| --- | --- |
| `POST /api/staff` | `name` and `email` required; `department` and `active` optional |
| `PATCH /api/staff/{id}` | Any of `name`, `email`, `department`, `active` |
| `POST /api/links` | `staff_id`, `title` and `destination_url`, all required |
| `PATCH /api/links/{code}` | Any of `title`, `destination_url`, `active` |

Any other field is rejected with 400. The server sets `click_count` and
`created_at`, and a link's `staff_id` can't change once the link exists.

## Rules

- **Errors** always look like
  `{"error": {"code": "not_found", "message": "Link not found"}}`
  and use status 400 (invalid input), 404 (not found) or 410 (deactivated link).
- **`/r/{code}` returns 302, not 301.** Browsers remember a 301 and skip the
  server next time, so repeat clicks would never be counted.
- **`destination_url` must start with `http://` or `https://`.** This stops a
  link from pointing at something like `javascript:...`.
- **Nothing is deleted.** Staff and links are deactivated instead, which keeps
  their click history. A deactivated link returns 410.
- **IP addresses are not stored.** Click counts don't need them, and they are
  personal data.
- **Authentication is required before deployment.** Every `/api/*` route except
  `/api/health` exposes or changes staff data, so it must be locked down before
  the API goes public. `/r/{code}` stays public because anyone can click a link.
