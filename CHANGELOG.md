# CHANGELOG

<!-- version list -->

## v2.3.0 (2026-03-12)

### Features

- Add review workflows for python and js sdk
  ([`ec1f139`](https://github.com/bhoshaga/struai/commit/ec1f139f6b255c90a27c56754f47bb213038f35c))


## v2.2.0 (2026-02-19)

### Documentation

- Add page-12 cookbook with full docquery examples
  ([`6aeef85`](https://github.com/bhoshaga/struai/commit/6aeef857d6b81e89486d015c203b74550a486b81))

### Features

- Align Python and JS SDKs to v3 DocQuery contract
  ([`eb5c28d`](https://github.com/bhoshaga/struai/commit/eb5c28d22a5f3bb0edf0321d30c593ee15b9e50f))


## v2.2.1 (2026-02-21)

### Bug Fixes

- Fix `AsyncJobBatch.wait_all()` and `status_all()` to poll jobs concurrently via `asyncio.gather()` (was sequential)
- Fix cookbook cypher query to exclude Sheet/Zone nodes for crop demo (avoids OOM on full-page renders)

## v2.3.0 (2026-03-12)

### Features

- Add first-class review support to the Python and JavaScript SDKs:
  - `client.reviews.create/list/get/open`
  - review handles with `refresh/status/wait/questions/issues`
  - typed review, question, and issue models for `/v1/reviews`

### Documentation

- Add page-13 review cookbook (`examples/page13_review_cookbook.py`)
- Sanitize examples for public release: remove hardcoded API keys, personal paths, localhost defaults
- Document review status values, wait semantics, and file-upload usage for the new reviews surface

### Breaking Changes

- Hard-cut SDK contracts to current drawing router API:
  - Removed Tier 1 `drawings.get` / `drawings.delete` in Python and JS.
  - Switched DocQuery routes to `/projects/{project_id}/{command}` (removed `/docquery` prefix).
  - Updated node/sheet/search/neighbors/cypher result models to slim payload contract.
  - Replaced local crop pipeline with server-side `POST /v1/projects/{project_id}/crop` PNG flow.
- Updated cookbook/examples/tests to the new contract and response shapes.

## v2.1.0 (2026-02-18)

### Features

- Add full docquery crop parity to python and js sdk
  ([`14d3856`](https://github.com/bhoshaga/struai/commit/14d38563618d88be36fd7c90583e8485c114d548))


## v2.0.0 (2026-02-18)

### Features

- Hard-cut SDK to docquery traversal contract
  ([`42b5aeb`](https://github.com/bhoshaga/struai/commit/42b5aeb6ef8013c99a563d933c23748e79c296d6))


## v1.3.1 (2026-02-08)

### Bug Fixes

- **ci**: Publish only when semantic-release creates a release
  ([`881a513`](https://github.com/bhoshaga/struai/commit/881a513405775e73b65ae0d569085c4cc83b0534))

### Documentation

- **sdk**: Add complete method refs and real workflow examples
  ([`c8f00b1`](https://github.com/bhoshaga/struai/commit/c8f00b1f5b120f0b1319d8fc93bdff9d508cc5fb))


## v1.3.0 (2026-02-08)

### Features

- **sdk**: Rebuild Python/JS SDK contracts for full projects API surface
- **sdk**: Add multi-job sheet ingest support (`page` selectors + batch wait helpers)
- **sdk**: Add sheet annotations endpoint support

### Documentation

- **docs**: Refresh README/examples for current drawings + projects APIs

## v1.2.1 (2026-02-04)

### Documentation

- **docs**: Add full page-12 cookbook example

### Bug Fixes

- **sdk**: Allow nullable sheet fields in list responses

## v1.2.0 (2026-02-04)

### Features

- **sdk**: Cache reuse for tier2 sheets
  ([`2e43eb1`](https://github.com/bhoshaga/struai/commit/2e43eb146e76d1cf8982caa894f66ab3c7b20733))


## v1.1.1 (2026-02-04)

### Bug Fixes

- **sdk**: Send form data without files
  ([`a2132e8`](https://github.com/bhoshaga/struai/commit/a2132e8b8923d24973f33351b785db1b7d3bb7f7))


## v1.1.0 (2026-02-04)

### Features

- **sdk**: Auto cache check for drawings
  ([`2a6c006`](https://github.com/bhoshaga/struai/commit/2a6c0062dcd4bc5efba94f472de5441d30ed5300))


## v1.0.4 (2026-02-04)

### Bug Fixes

- **ci**: Checkout release tag for publish jobs
  ([`6b78004`](https://github.com/bhoshaga/struai/commit/6b78004629cee3dff309836f7879da417dd69ac9))


## v1.0.3 (2026-02-04)

### Bug Fixes

- Trigger release v1.0.3
  ([`a611906`](https://github.com/bhoshaga/struai/commit/a611906590f693d9222b2b95aa2c42830e92c156))

### Documentation

- Clarify auth and endpoints
  ([`9703efe`](https://github.com/bhoshaga/struai/commit/9703efe1354168cb32d3ed6eacea642e22bea593))


## v1.0.2 (2026-02-04)

### Bug Fixes

- **ci**: Add publish_only option for re-publishing
  ([`0806b1e`](https://github.com/bhoshaga/struai/commit/0806b1eb6dba6d518df9f43a199b9255d1776d6a))

- **ci**: Consolidate to single release workflow
  ([`91e94b0`](https://github.com/bhoshaga/struai/commit/91e94b00f5eb6e123adb2cfae01a473ed4cd5cbd))


## v1.0.1 (2026-02-04)

### Bug Fixes

- **ci**: Include publish jobs directly in release workflow
  ([`02436eb`](https://github.com/bhoshaga/struai/commit/02436eb55c63cbaa54eac8ca456a54d30125fada))


## v1.0.0 (2026-02-04)

- Initial Release
