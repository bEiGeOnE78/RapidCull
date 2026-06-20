# RapidCull API Reference

## Base URL

```
http://127.0.0.1:8000
```

All API endpoints are prefixed with `/api/v1/`.

Live interactive docs (OpenAPI/Swagger UI) are available at `http://127.0.0.1:8000/docs` when the server is running.

Proxy/thumbnail static files are served under `/proxies/`.

---

## Standard Response Envelope

Every `/api/v1/*` endpoint returns one of two shapes.

**Success**

```json
{
  "ok": true,
  "data": { ... },
  "meta": null
}
```

**Error**

```json
{
  "ok": false,
  "error": {
    "code": "UPPER_SNAKE_CODE",
    "message": "Human-readable description.",
    "details": null
  }
}
```

`meta` and `details` are `null` unless explicitly populated.

---

## Authentication

No authentication is required. The server is designed for local/LAN use only.

---

## Images

### GET /api/v1/images/{image_id}

Retrieve full detail for a single image, including its current cull decision and face count.

**Path parameters**

| Parameter  | Type   | Required | Description          |
|------------|--------|----------|----------------------|
| `image_id` | string | Yes      | Unique image ID      |

**Response body** (`data`)

```json
{
  "image_id": "string",
  "path": "string",
  "metadata": {},
  "decision": "pick | reject | null",
  "face_count": 0
}
```

| Field        | Type            | Description                                      |
|--------------|-----------------|--------------------------------------------------|
| `image_id`   | string          | Unique identifier                                |
| `path`       | string          | Absolute filesystem path to the original image   |
| `metadata`   | object          | Reserved; currently always `{}`                  |
| `decision`   | string or null  | Current cull decision (`"pick"`, `"reject"`) or `null` if undecided |
| `face_count` | integer         | Number of detected faces stored for this image   |

**Error codes**

| HTTP | Code              | Description                  |
|------|-------------------|------------------------------|
| 404  | `IMAGE_NOT_FOUND` | No image with that ID exists |

---

### GET /api/v1/images/{image_id}/decision

Retrieve the current cull decision for an image.

**Path parameters**

| Parameter  | Type   | Required | Description     |
|------------|--------|----------|-----------------|
| `image_id` | string | Yes      | Unique image ID |

**Response body** (`data`)

Returns `null` if no decision has been recorded, otherwise:

```json
{
  "image_id": "string",
  "decision": "pick | reject",
  "decided_at": "string"
}
```

| Field        | Type   | Description                              |
|--------------|--------|------------------------------------------|
| `image_id`   | string | Unique identifier                        |
| `decision`   | string | `"pick"` or `"reject"`                   |
| `decided_at` | string | ISO-8601 timestamp of when decision was recorded |

**Error codes**

| HTTP | Code              | Description                  |
|------|-------------------|------------------------------|
| 404  | `IMAGE_NOT_FOUND` | No image with that ID exists |

---

### POST /api/v1/images/{image_id}/decision

Set or update the cull decision for an image.

**Path parameters**

| Parameter  | Type   | Required | Description     |
|------------|--------|----------|-----------------|
| `image_id` | string | Yes      | Unique image ID |

**Request body**

```json
{
  "decision": "pick | reject"
}
```

| Field      | Type   | Required | Description             |
|------------|--------|----------|-------------------------|
| `decision` | string | Yes      | Must be `"pick"` or `"reject"` |

**Response body** (`data`)

```json
{
  "image_id": "string",
  "success": true
}
```

**Error codes**

| HTTP | Code               | Description                            |
|------|--------------------|----------------------------------------|
| 404  | `IMAGE_NOT_FOUND`  | No image with that ID exists           |
| 422  | `VALIDATION_ERROR` | `decision` field missing or invalid value |

---

### DELETE /api/v1/images/{image_id}/decision

Remove (undo) the cull decision for an image, returning it to an undecided state.

**Path parameters**

| Parameter  | Type   | Required | Description     |
|------------|--------|----------|-----------------|
| `image_id` | string | Yes      | Unique image ID |

**Response body** (`data`)

```json
{
  "image_id": "string",
  "success": true
}
```

**Error codes**

| HTTP | Code              | Description                  |
|------|-------------------|------------------------------|
| 404  | `IMAGE_NOT_FOUND` | No image with that ID exists |

---

### GET /api/v1/images/{image_id}/faces

Return all face detection boxes and person assignments for an image.

**Path parameters**

| Parameter  | Type   | Required | Description     |
|------------|--------|----------|-----------------|
| `image_id` | string | Yes      | Unique image ID |

**Response body** (`data`)

```json
{
  "image_id": "string",
  "faces": [
    {
      "face_id": "string",
      "person_id": "string | null",
      "person_name": "string | null",
      "bbox": {
        "x": 0,
        "y": 0,
        "w": 0,
        "h": 0
      },
      "score": 0.0
    }
  ]
}
```

| Field         | Type            | Description                                            |
|---------------|-----------------|--------------------------------------------------------|
| `face_id`     | string          | Unique face identifier                                 |
| `person_id`   | string or null  | Person this face is assigned to, or `null`             |
| `person_name` | string or null  | Display name of the assigned person, or `null`         |
| `bbox.x`      | integer         | Left edge of bounding box in pixels                    |
| `bbox.y`      | integer         | Top edge of bounding box in pixels                     |
| `bbox.w`      | integer         | Width of bounding box in pixels                        |
| `bbox.h`      | integer         | Height of bounding box in pixels                       |
| `score`       | float           | Detection confidence score (0.0–1.0)                   |

**Error codes**

| HTTP | Code              | Description                  |
|------|-------------------|------------------------------|
| 404  | `IMAGE_NOT_FOUND` | No image with that ID exists |

---

## Galleries

Gallery IDs are URL-safe base64 encodings of the directory path. A gallery is derived from the unique set of directories containing ingested images.

### GET /api/v1/galleries

List all galleries (unique directories) along with their image counts.

**Response body** (`data`)

```json
{
  "galleries": [
    {
      "gallery_id": "string",
      "name": "string",
      "path": "string",
      "image_count": 0
    }
  ]
}
```

| Field         | Type    | Description                                          |
|---------------|---------|------------------------------------------------------|
| `gallery_id`  | string  | URL-safe base64 encoding of the directory path       |
| `name`        | string  | Directory basename (or full path for root-level)     |
| `path`        | string  | Absolute directory path                              |
| `image_count` | integer | Number of ingested images in this directory          |

---

### POST /api/v1/galleries

Create a virtual gallery of hardlinked images from picks or a query expression. Returns HTTP 201 on success.

**Request body**

```json
{
  "name": "string",
  "mode": "picks | query",
  "query": "string (optional)"
}
```

| Field   | Type            | Required | Description                                                         |
|---------|-----------------|----------|---------------------------------------------------------------------|
| `name`  | string          | Yes      | Gallery directory name; created under `<db_dir>/galleries/<name>/`  |
| `mode`  | string          | Yes      | `"picks"` to include all picked images; `"query"` for a filter expression |
| `query` | string or null  | Conditional | Required when `mode` is `"query"`; a query grammar expression    |

**Response body** (`data`)

```json
{
  "gallery_path": "string",
  "created_count": 0
}
```

| Field           | Type    | Description                                      |
|-----------------|---------|--------------------------------------------------|
| `gallery_path`  | string  | Absolute path to the created gallery directory   |
| `created_count` | integer | Number of hardlinks created                      |

**Error codes**

| HTTP | Code               | Description                                              |
|------|--------------------|----------------------------------------------------------|
| 422  | `QUERY_REQUIRED`   | `mode` is `"query"` but `query` field is absent or empty |
| 422  | `QUERY_PARSE_ERROR`| The query expression could not be parsed                 |
| 422  | `INVALID_MODE`     | `mode` is not `"picks"` or `"query"`                     |
| 422  | `VALIDATION_ERROR` | Request body validation failed                           |

---

### GET /api/v1/galleries/{gallery_id}/images

List images in a gallery, paginated.

**Path parameters**

| Parameter    | Type   | Required | Description                               |
|--------------|--------|----------|-------------------------------------------|
| `gallery_id` | string | Yes      | URL-safe base64 encoded directory path    |

**Query parameters**

| Parameter   | Type    | Required | Default | Description                     |
|-------------|---------|----------|---------|---------------------------------|
| `page`      | integer | No       | `1`     | Page number (1-based)           |
| `page_size` | integer | No       | `50`    | Maximum images per page         |

**Response body** (`data`)

```json
{
  "images": [
    {
      "image_id": "string",
      "path": "string",
      "thumbnail_path": null,
      "decision": "pick | reject | null"
    }
  ],
  "total": 0,
  "page": 1,
  "page_size": 50
}
```

| Field            | Type            | Description                                          |
|------------------|-----------------|------------------------------------------------------|
| `image_id`       | string          | Unique image identifier                              |
| `path`           | string          | Absolute filesystem path                             |
| `thumbnail_path` | null            | Reserved; always `null` currently                    |
| `decision`       | string or null  | Current cull decision or `null` if undecided         |
| `total`          | integer         | Total images in the gallery (all pages)              |
| `page`           | integer         | Current page number                                  |
| `page_size`      | integer         | Page size used                                       |

**Error codes**

| HTTP | Code                 | Description                          |
|------|----------------------|--------------------------------------|
| 404  | `GALLERY_NOT_FOUND`  | No gallery with that ID exists       |

---

## Persons

Persons are named identity records that face detections can be assigned to via clustering.

### GET /api/v1/persons

List all persons with their face counts.

**Response body** (`data`)

```json
{
  "persons": [
    {
      "person_id": "string",
      "name": "string",
      "created_at": "string",
      "face_count": 0
    }
  ]
}
```

| Field        | Type    | Description                                        |
|--------------|---------|----------------------------------------------------|
| `person_id`  | string  | Unique person identifier                           |
| `name`       | string  | Display name                                       |
| `created_at` | string  | ISO-8601 creation timestamp                        |
| `face_count` | integer | Number of face detections currently assigned to this person |

---

### PATCH /api/v1/persons/{person_id}

Rename a person.

**Path parameters**

| Parameter   | Type   | Required | Description        |
|-------------|--------|----------|--------------------|
| `person_id` | string | Yes      | Unique person ID   |

**Request body**

```json
{
  "name": "string"
}
```

| Field  | Type   | Required | Description      |
|--------|--------|----------|------------------|
| `name` | string | Yes      | New display name |

**Response body** (`data`)

```json
{
  "person_id": "string",
  "name": "string"
}
```

**Error codes**

| HTTP | Code               | Description                        |
|------|--------------------|------------------------------------|
| 404  | `PERSON_NOT_FOUND` | No person with that ID exists      |
| 422  | `VALIDATION_ERROR` | Request body validation failed     |

---

### POST /api/v1/persons/{person_id}/merge

Merge a person into another, reassigning all their face detections to the target person and deleting the source.

**Path parameters**

| Parameter   | Type   | Required | Description              |
|-------------|--------|----------|--------------------------|
| `person_id` | string | Yes      | Person to merge (source) |

**Request body**

```json
{
  "into_person_id": "string"
}
```

| Field            | Type   | Required | Description                               |
|------------------|--------|----------|-------------------------------------------|
| `into_person_id` | string | Yes      | ID of the person to merge the source into |

**Response body** (`data`)

```json
{
  "reassigned_count": 0,
  "deleted_person_id": "string"
}
```

| Field               | Type    | Description                                           |
|---------------------|---------|-------------------------------------------------------|
| `reassigned_count`  | integer | Number of face records reassigned to the target person |
| `deleted_person_id` | string  | ID of the source person that was deleted              |

**Error codes**

| HTTP | Code               | Description                                           |
|------|--------------------|-------------------------------------------------------|
| 404  | `PERSON_NOT_FOUND` | Source or target person ID does not exist             |
| 422  | `VALIDATION_ERROR` | Request body validation failed                        |

---

### DELETE /api/v1/persons/{person_id}

Delete a person record. All face detections assigned to this person are unlinked (their `person_id` is set to `null`); face embeddings are preserved.

**Path parameters**

| Parameter   | Type   | Required | Description      |
|-------------|--------|----------|------------------|
| `person_id` | string | Yes      | Unique person ID |

**Response body** (`data`)

```json
{
  "deleted_person_id": "string",
  "deleted_face_count": 0,
  "unlinked_face_count": 0
}
```

| Field                | Type    | Description                                              |
|----------------------|---------|----------------------------------------------------------|
| `deleted_person_id`  | string  | ID of the person that was deleted                        |
| `deleted_face_count` | integer | Always `0` (embeddings are retained, not deleted)        |
| `unlinked_face_count`| integer | Number of face records that had their `person_id` cleared |

**Error codes**

| HTTP | Code               | Description                   |
|------|--------------------|-------------------------------|
| 404  | `PERSON_NOT_FOUND` | No person with that ID exists |

---

## Trash

The trash holds images whose files have been moved to `.trash/` adjacent to the database. Images remain in the `images` table with a `trashed_at` timestamp.

### GET /api/v1/trash

List all trashed images.

**Response body** (`data`)

```json
{
  "items": [
    {
      "image_id": "string",
      "original_path": "string",
      "trashed_at": "string"
    }
  ],
  "count": 0
}
```

| Field           | Type    | Description                                        |
|-----------------|---------|----------------------------------------------------|
| `image_id`      | string  | Unique image identifier                            |
| `original_path` | string  | Filesystem path the image occupied before trashing |
| `trashed_at`    | string  | ISO-8601 timestamp of when the image was trashed   |
| `count`         | integer | Total number of trashed items                      |

---

### POST /api/v1/trash/{image_id}/restore

Restore a trashed image to its original filesystem path and clear its trash record.

**Path parameters**

| Parameter  | Type   | Required | Description                   |
|------------|--------|----------|-------------------------------|
| `image_id` | string | Yes      | ID of the image to restore    |

**Response body** (`data`)

```json
{
  "image_id": "string",
  "success": true
}
```

**Error codes**

| HTTP | Code                   | Description                                                 |
|------|------------------------|-------------------------------------------------------------|
| 404  | `TRASH_RESTORE_FAILED` | Image not found in trash, or file could not be moved back   |

---

## Jobs

Jobs represent asynchronous background tasks (ingest, proxy generation, face detection, etc.). Jobs are created in `QUEUED` state and processed by the internal `JobExecutor`.

### POST /api/v1/jobs

Create a new job and enqueue it for execution. Returns HTTP 201.

**Request body**

```json
{
  "kind": "string",
  "params": {}
}
```

| Field    | Type   | Required | Description                                           |
|----------|--------|----------|-------------------------------------------------------|
| `kind`   | string | Yes      | Job type identifier (e.g. `"ingest"`, `"proxy"`)      |
| `params` | object | No       | Job-kind-specific parameters; defaults to `{}`        |

**Response body** (`data`) — same shape as the job object returned by GET /api/v1/jobs/{job_id}:

```json
{
  "job_id": "string",
  "kind": "string",
  "params": {},
  "state": "queued",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z",
  "result": null,
  "error": null
}
```

**Error codes**

| HTTP | Code               | Description                    |
|------|--------------------|--------------------------------|
| 422  | `VALIDATION_ERROR` | Request body validation failed |

---

### GET /api/v1/jobs

List all jobs, optionally filtered by state.

**Query parameters**

| Parameter | Type   | Required | Description                                                  |
|-----------|--------|----------|--------------------------------------------------------------|
| `state`   | string | No       | Filter by job state: `queued`, `running`, `done`, `cancelled`, `failed` |

**Response body** (`data`)

```json
{
  "jobs": [ { ... } ]
}
```

Each item in `jobs` is the same job object shape as described under POST /api/v1/jobs.

**Error codes**

| HTTP | Code                   | Description                                         |
|------|------------------------|-----------------------------------------------------|
| 400  | `INVALID_STATE_FILTER` | Provided `state` value is not a valid `JobState`    |

---

### GET /api/v1/jobs/{job_id}

Get the full status of a single job.

**Path parameters**

| Parameter | Type   | Required | Description    |
|-----------|--------|----------|----------------|
| `job_id`  | string | Yes      | Unique job ID  |

**Response body** (`data`)

```json
{
  "job_id": "string",
  "kind": "string",
  "params": {},
  "state": "queued | running | done | cancelled | failed",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z",
  "result": null,
  "error": null
}
```

| Field        | Type            | Description                                                  |
|--------------|-----------------|--------------------------------------------------------------|
| `job_id`     | string          | Unique job identifier                                        |
| `kind`       | string          | Job type                                                     |
| `params`     | object          | Parameters the job was created with                          |
| `state`      | string          | One of: `queued`, `running`, `done`, `cancelled`, `failed`   |
| `created_at` | string          | ISO-8601 creation time (UTC, `Z` suffix)                     |
| `updated_at` | string          | ISO-8601 last-updated time (UTC, `Z` suffix)                 |
| `result`     | any or null     | Job output payload when state is `done`; otherwise `null`    |
| `error`      | string or null  | Error message when state is `failed`; otherwise `null`       |

**Error codes**

| HTTP | Code            | Description                 |
|------|-----------------|-----------------------------|
| 404  | `JOB_NOT_FOUND` | No job with that ID exists  |

---

### DELETE /api/v1/jobs/{job_id}

Cancel a job. Only jobs in a non-terminal state can be cancelled.

**Path parameters**

| Parameter | Type   | Required | Description    |
|-----------|--------|----------|----------------|
| `job_id`  | string | Yes      | Unique job ID  |

**Response body** (`data`) — the updated job object (same shape as GET /api/v1/jobs/{job_id}).

**Error codes**

| HTTP | Code                   | Description                                              |
|------|------------------------|----------------------------------------------------------|
| 404  | `JOB_NOT_FOUND`        | No job with that ID exists                               |
| 409  | `JOB_NOT_CANCELLABLE`  | Job is already in a terminal state (`done`, `failed`, `cancelled`) |

---

### GET /api/v1/jobs/{job_id}/progress

Return all progress entries for a job in append order.

**Path parameters**

| Parameter | Type   | Required | Description    |
|-----------|--------|----------|----------------|
| `job_id`  | string | Yes      | Unique job ID  |

**Response body** (`data`)

```json
{
  "entries": [
    {
      "timestamp": "2026-01-01T00:00:00Z",
      "message": "string",
      "percent": 0
    }
  ]
}
```

| Field       | Type            | Description                                       |
|-------------|-----------------|---------------------------------------------------|
| `timestamp` | string          | ISO-8601 UTC timestamp of the progress event      |
| `message`   | string          | Human-readable progress description               |
| `percent`   | integer or null | Completion percentage (0–100) if reported         |

**Error codes**

| HTTP | Code            | Description                 |
|------|-----------------|-----------------------------|
| 404  | `JOB_NOT_FOUND` | No job with that ID exists  |

---

## Collections

Collections are in-memory, server-lifetime registries of image sets keyed by a caller-assigned `collection_id`. They support structured query expressions to filter images.

### POST /api/v1/collections/{collection_id}/query

Query a collection using the RapidCull query grammar; returns matching image IDs.

**Path parameters**

| Parameter       | Type   | Required | Description                                      |
|-----------------|--------|----------|--------------------------------------------------|
| `collection_id` | string | Yes      | Identifier of an existing in-memory collection   |

**Request body**

```json
{
  "query_text": "string"
}
```

| Field        | Type   | Required | Description                                 |
|--------------|--------|----------|---------------------------------------------|
| `query_text` | string | Yes      | Query grammar expression to evaluate        |

**Response body** (`data`)

```json
{
  "matching_ids": ["string"],
  "total_count": 0,
  "query_expression": "string"
}
```

| Field              | Type             | Description                                      |
|--------------------|------------------|--------------------------------------------------|
| `matching_ids`     | array of strings | Image IDs that matched the query expression      |
| `total_count`      | integer          | Count of matching images                         |
| `query_expression` | string           | Canonical form of the parsed query expression    |

**Error codes**

| HTTP | Code                   | Description                                        |
|------|------------------------|----------------------------------------------------|
| 400  | `QUERY_PARSE_ERROR`    | The query expression could not be parsed           |
| 404  | `COLLECTION_NOT_FOUND` | No collection with that ID exists in memory        |

---

## Common Error Codes Reference

| Code                   | HTTP | Where raised                                    |
|------------------------|------|-------------------------------------------------|
| `IMAGE_NOT_FOUND`      | 404  | Image endpoints                                 |
| `GALLERY_NOT_FOUND`    | 404  | Gallery endpoints                               |
| `PERSON_NOT_FOUND`     | 404  | Person endpoints                                |
| `JOB_NOT_FOUND`        | 404  | Job endpoints                                   |
| `COLLECTION_NOT_FOUND` | 404  | Collection query endpoint                       |
| `TRASH_RESTORE_FAILED` | 404  | Trash restore endpoint                          |
| `INVALID_MODE`         | 422  | Gallery create — unrecognised `mode` value      |
| `QUERY_REQUIRED`       | 422  | Gallery create — `mode=query` without `query`   |
| `QUERY_PARSE_ERROR`    | 400/422 | Gallery create, collection query             |
| `INVALID_STATE_FILTER` | 400  | Job list — unrecognised `state` query parameter |
| `JOB_NOT_CANCELLABLE`  | 409  | Job cancel — job is already terminal            |
| `VALIDATION_ERROR`     | 422  | Any endpoint — request body fails Pydantic validation |
| `HTTP_<status>`        | varies | Generic FastAPI/Starlette HTTP exceptions     |
| `INTERNAL_ERROR`       | 500  | Unexpected server-side error                    |
