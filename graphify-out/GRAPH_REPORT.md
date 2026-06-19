# Graph Report - .  (2026-06-19)

## Corpus Check
- 348 files · ~187,436 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1522 nodes · 3305 edges · 96 communities (78 shown, 18 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 613 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_CLI Processing Pipeline|CLI Processing Pipeline]]
- [[_COMMUNITY_ImageMagick Proxy Adapters|ImageMagick Proxy Adapters]]
- [[_COMMUNITY_Collection Query API|Collection Query API]]
- [[_COMMUNITY_Face Detection Schema|Face Detection Schema]]
- [[_COMMUNITY_API Security Auth|API Security Auth]]
- [[_COMMUNITY_Gallery Hard-Link Creation|Gallery Hard-Link Creation]]
- [[_COMMUNITY_CLI Entry Point|CLI Entry Point]]
- [[_COMMUNITY_InsightFace Adapter|InsightFace Adapter]]
- [[_COMMUNITY_Job Endpoint Tests|Job Endpoint Tests]]
- [[_COMMUNITY_OpenAgents Agent Framework|OpenAgents Agent Framework]]
- [[_COMMUNITY_Person CRUD Operations|Person CRUD Operations]]
- [[_COMMUNITY_Job State Machine|Job State Machine]]
- [[_COMMUNITY_Job Store Cancel Logic|Job Store Cancel Logic]]
- [[_COMMUNITY_Claude Agent Config|Claude Agent Config]]
- [[_COMMUNITY_CLI Service Tests|CLI Service Tests]]
- [[_COMMUNITY_Collection Query Tests|Collection Query Tests]]
- [[_COMMUNITY_Context System Commands|Context System Commands]]
- [[_COMMUNITY_Query Grammar Validation|Query Grammar Validation]]
- [[_COMMUNITY_Architecture Decisions|Architecture Decisions]]
- [[_COMMUNITY_Query Evaluator Tests|Query Evaluator Tests]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 87|Community 87]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_Community 90|Community 90]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 93|Community 93]]
- [[_COMMUNITY_Community 94|Community 94]]

## God Nodes (most connected - your core abstractions)
1. `FailedIngestItem` - 55 edges
2. `parse_query()` - 46 edges
3. `QueryValidationError` - 34 edges
4. `execute_proxy_generation()` - 30 edges
5. `QueryParseResult` - 28 edges
6. `TestClient` - 26 edges
7. `Job` - 25 edges
8. `FaceDetectionSuccess` - 24 edges
9. `JobStore` - 24 edges
10. `IngestPlan` - 24 edges

## Surprising Connections (you probably didn't know these)
- `Graphify PreToolUse Hook` --rationale_for--> `ContextScout`  [INFERRED]
  .claude/settings.json → .opencode/agent/subagents/core/contextscout.md
- `add-context command` --references--> `External Context Manifest`  [INFERRED]
  .opencode/command/add-context.md → .tmp/external-context/.manifest.json
- `Session: FR-022 Query Behavior Documentation Baseline` --produces--> `tests/integration/query/test_fr_022_query_behavior_docs.py`  [INFERRED]
  .tmp/sessions/2026-03-28-fr-022-query-behavior-docs/context.md → tests/integration/query/test_fr_022_query_behavior_docs.py
- `Session: Query Evaluation Semantics v1` --references--> `tests/integration/query/test_query_evaluation_contract_v1.py`  [EXTRACTED]
  .tmp/sessions/2026-03-29-query-evaluation-semantics-v1/context.md → tests/integration/query/test_query_evaluation_contract_v1.py
- `Session: Query Evaluator Baseline v1` --references--> `src/rapidcull/query_grammar.py`  [EXTRACTED]
  .tmp/sessions/2026-03-29-query-evaluator-baseline-v1/context.md → src/rapidcull/query_grammar.py

## Import Cycles
- 1-file cycle: `src/rapidcull/api.py -> src/rapidcull/api.py`
- 1-file cycle: `src/rapidcull/api_jobs.py -> src/rapidcull/api_jobs.py`
- 1-file cycle: `src/rapidcull/security.py -> src/rapidcull/security.py`
- 1-file cycle: `tests/integration/api/test_security_auth.py -> tests/integration/api/test_security_auth.py`
- 1-file cycle: `tests/integration/api/test_security_cors.py -> tests/integration/api/test_security_cors.py`
- 2-file cycle: `src/rapidcull/api_jobs.py -> src/rapidcull/jobs.py -> src/rapidcull/api_jobs.py`

## Communities (96 total, 18 thin omitted)

### Community 0 - "CLI Processing Pipeline"
Cohesion: 0.06
Nodes (58): _make_extraction_result(), _make_proxy_result(), Report correct counts for 3 files with 1 skipped., process-new output follows 'Processed: N | Skipped: N | Failed: N' format., process-new sums failures from both extraction and proxy generation stages., process-new reports only extraction failures when proxy generation succeeds., Build an IngestMetadataExtractionResult with one metadata entry per path., process-new reports only proxy failures when metadata extraction fully succeeds. (+50 more)

### Community 1 - "ImageMagick Proxy Adapters"
Cohesion: 0.10
Nodes (58): detect_heif_support(), ImageMagickAdapter, ImageMagickProxyOutcome, RawTherapeeAdapter, RawTherapeeProxyOutcome, ImageMagickAdapter, MonkeyPatch, OrphanCleanupReport (+50 more)

### Community 2 - "Collection Query API"
Cohesion: 0.06
Nodes (31): client(), _query_url(), Populate the in-memory registry before each test and clean up after., setup_and_teardown_registry(), TestCollectionNotFound, TestParseError, TestValidQuery, assert_envelope() (+23 more)

### Community 3 - "Face Detection Schema"
Cohesion: 0.06
Nodes (54): Cursor, Integration tests for FR-023: Schema v2 with faces and persons tables., PersonRecord is a frozen dataclass with expected fields., FaceDetectionResult has processed/skipped/failed accounting., Schema version must be 2 to include faces and persons tables., Schema init creates persons table with expected columns., Schema init creates faces table with expected columns., Opening a v1 DB with v2 schema code raises SchemaVersionMismatchError. (+46 more)

### Community 4 - "API Security Auth"
Cohesion: 0.06
Nodes (39): lan_client(), localhost_client(), _make_app(), Integration tests for authentication middleware (FR-043, FR-044)., Build a minimal test app with given settings applied., FR-043: In localhost mode, auth is disabled by default., FR-044: In LAN mode, mutating endpoints require Bearer token., Read-only endpoints never require auth, even in LAN mode. (+31 more)

### Community 5 - "Gallery Hard-Link Creation"
Cohesion: 0.13
Nodes (51): test_fr_012_creates_gallery_hardlinks_without_modifying_masters(), test_fr_013_creates_gallery_from_query_picks_and_face_sample_modes(), test_fr_013_returns_valid_empty_gallery_with_message_when_mode_matches_no_assets(), test_fr_014_rebuilds_metadata_for_all_galleries(), test_fr_014_rebuilds_single_gallery_metadata_json(), test_fr_014_returns_explicit_error_for_missing_gallery_path(), test_fr_015_continues_index_rebuild_when_one_gallery_metadata_is_invalid(), test_fr_015_rebuilds_central_galleries_index_from_current_gallery_metadata() (+43 more)

### Community 6 - "CLI Entry Point"
Cohesion: 0.09
Nodes (28): Context, cli(), main(), _port_in_use(), _process_alive(), process_new(), Stop the RapidCull API server., Restart the RapidCull API server. (+20 more)

### Community 7 - "InsightFace Adapter"
Cohesion: 0.09
Nodes (28): _insightface_available(), InsightFaceAdapter, _make_embedding(), Integration tests for FR-023: Face detection adapter seam., FaceDetectionSuccess holds a list of DetectedFace., FaceDetectionFailure carries a canonical reason string., pipeline_available returns True iff insightface is importable., detect() returns FaceDetectionFailure when pipeline_available is False. (+20 more)

### Community 8 - "Job Endpoint Tests"
Cohesion: 0.09
Nodes (11): client(), FR-041: HTTP integration tests for /api/v1/jobs endpoints.  Uses FastAPI TestCli, List returns jobs in creation order on repeated calls., Clear the in-memory JobStore before each test., reset_job_store(), TestCancelJob, TestCreateJob, TestGetJob (+3 more)

### Community 9 - "OpenAgents Agent Framework"
Cohesion: 0.08
Nodes (36): Agent Creation Workflow (4 Steps), CLI Architecture: router.sh + skill-cli.ts, Context Bundle Pattern, Agent Eval Test Types (smoke/approval-gate/context-loading/tool-usage), ExternalScout: Fetch Live External Library Docs, GitHub Issues and Project Board Workflow, Installation Profiles (essential/developer/business/full/advanced), Installer Wildcard Context ID Path Alignment Fix (+28 more)

### Community 10 - "Person CRUD Operations"
Cohesion: 0.13
Nodes (31): _add_face_for_person(), _add_image(), _add_person(), _ConstDetector, db_path(), _make_embedding(), Integration tests for FR-025, FR-028: Person identity CRUD and deletion., merge_persons: all faces of source reassigned to target; source deleted. (+23 more)

### Community 11 - "Job State Machine"
Cohesion: 0.10
Nodes (20): _drive_path(), _drive_to(), _make_job(), FR-040: Pure unit tests for Job state machine transitions.  Covers all 25 state-, Directly setting job.state must raise FrozenInstanceError., Directly setting job.result must raise FrozenInstanceError., Directly setting job.error must raise FrozenInstanceError., The transition() method must still succeed via object.__setattr__. (+12 more)

### Community 12 - "Job Store Cancel Logic"
Cohesion: 0.11
Nodes (16): TestJobStoreCancelTerminal, Job, JobStore, Create a new job in QUEUED state and return it., Return the job with the given id, or None if not found., Return all jobs sorted by (created_at, job_id), optionally filtered by state., Transition a job to RUNNING. Raises InvalidJobTransition if not allowed., Transition a job to SUCCEEDED and optionally set result. (+8 more)

### Community 13 - "Claude Agent Config"
Cohesion: 0.18
Nodes (30): Approval Gate Pattern, BuildAgent, Claude Settings Hooks, Claude Settings Local Permissions, CodeReviewer, CoderAgent, add-context command, analyze-patterns command (+22 more)

### Community 14 - "CLI Service Tests"
Cohesion: 0.12
Nodes (17): Stop command kills the process and removes the PID file., Stop command errors when no PID file exists., Stop command removes a stale PID file when the process is no longer alive., Stop command escalates to SIGKILL when process does not exit after SIGTERM., Restart command stops a running process and then starts a new one., Start command writes PID to file and reports success., Restart starts fresh when no existing PID file is present., Start command errors when an existing process is alive. (+9 more)

### Community 15 - "Collection Query Tests"
Cohesion: 0.10
Nodes (28): collection(), Test exact match on single-value field (camera)., 5-10 images with realistic EXIF-like metadata., Test exact match on multi-value field (person)., Test pattern match on multi-value keyword field., Test numeric comparison on iso field., Test date range comparison., Test AND boolean composition of two conditions. (+20 more)

### Community 16 - "Context System Commands"
Cohesion: 0.15
Nodes (29): Context Manager Command, Function-Based Context Structure, Lazy Load Strategy, Minimal Viable Information Principle, Context Subagent Routing, ContextOrganizer Subagent, ContextScout Subagent, Pattern A: Function-Based Organization (+21 more)

### Community 17 - "Query Grammar Validation"
Cohesion: 0.25
Nodes (28): test_fr_017_parses_valid_grammar_query_into_typed_expression_tree(), test_fr_018_rejects_unknown_field_with_actionable_suggestion(), test_fr_019_rejects_non_integer_iso_value_with_expected_format_message(), test_fr_019_rejects_non_numeric_fnumber_value_with_expected_format_message(), test_fr_019_rejects_operator_not_supported_for_field_type(), test_fr_021_rejects_and_followed_by_or_with_actionable_error(), test_fr_021_rejects_bad_date_with_expected_format_message(), test_fr_021_rejects_double_equals_operator_with_expected_guidance() (+20 more)

### Community 18 - "Architecture Decisions"
Cohesion: 0.13
Nodes (28): Decision: Allowlist-based gallery mutation boundaries, Decision: Continue-on-error by default, Decision: Deterministic result contracts, Decision: External media tools behind adapter seams, Decision: Linux-first, local-first posture, Decision: Modular local-first monolith, Decision: Python 3.11+ baseline, Decision: Requirement-mapped integration tests as primary contract guard (+20 more)

### Community 19 - "Query Evaluator Tests"
Cohesion: 0.13
Nodes (25): test_fr_020_honors_boolean_parentheses_and_not_precedence(), evaluate_query must raise ValueError with context when ISO value is not an integ, evaluate_query must raise ValueError with context when fnumber value is not a nu, test_evaluate_comparison_raises_descriptive_error_for_non_float_fnumber_value(), test_evaluate_comparison_raises_descriptive_error_for_non_int_iso_value(), test_query_evaluator_applies_ordered_numeric_and_date_comparisons(), test_query_evaluator_honors_boolean_composition_for_canonical_contract_example(), test_query_evaluator_matches_any_value_in_multi_value_person_field() (+17 more)

### Community 20 - "Community 20"
Cohesion: 0.24
Nodes (20): DetectedFace, FaceDetectionFailure, FaceDetectionSuccess, FaceDetector, ClusterMode, DetectedFace, FaceClusterResult, FaceDetectionFailure (+12 more)

### Community 21 - "Community 21"
Cohesion: 0.12
Nodes (22): Exception, create_app(), api_error_handler(), err(), http_exception_handler(), Standard response envelope helpers and exception handlers for the RapidCull API., Register all envelope exception handlers on a FastAPI application., Build an error envelope (body only — HTTP status set by the caller). (+14 more)

### Community 22 - "Community 22"
Cohesion: 0.18
Nodes (21): db_path(), _image_id_for(), _make_embedding(), Integration tests for FR-023: Face detection orchestration and DB storage., Running detection twice on same image skips on second run., Image not in DB (no image_id) skipped with canonical reason., Adapter failure for one image does not abort remaining images., Embedding stored as bytes and retrieved identically. (+13 more)

### Community 23 - "Community 23"
Cohesion: 0.15
Nodes (24): db_path(), _image_id_for(), _make_embedding(), Integration tests for FR-024, FR-027: Face clustering and re-cluster modes., Two faces with identical embeddings land in same cluster → 1 person., Two faces with maximally different embeddings land in separate clusters → 2 pers, Isolated face (no neighbours) with min_samples=2 becomes noise (person_id=NULL)., NEW_ONLY mode leaves already-assigned faces untouched. (+16 more)

### Community 24 - "Community 24"
Cohesion: 0.12
Nodes (24): AI Development Navigation, Mastra Agent, Mastra Agents and Tools, Mastra Tool, LibSQLStore, Mastra Core Concept, Mastra Instance, Mastra Evaluations (+16 more)

### Community 25 - "Community 25"
Cohesion: 0.11
Nodes (23): Delegation Testing Mode, Subagent Testing Modes, Standalone Testing Mode, Agent Metadata System, Valid OpenCode Agent Frontmatter Fields, Centralized Agent Metadata Schema, Agent Category System, Agents Core Concept (+15 more)

### Community 26 - "Community 26"
Cohesion: 0.18
Nodes (18): BaseModel, datetime, JobProgressEntry, ApiError, Structured API error that maps to the standard error envelope., CreateJobRequest, query_collection(), QueryRequest (+10 more)

### Community 27 - "Community 27"
Cohesion: 0.10
Nodes (22): Context Root Navigation, Full-Stack Development Navigation, Common Full-Stack Technology Stacks, Infrastructure Navigation, Integration Navigation, Development Navigation, API Design Patterns, GraphQL API Patterns (+14 more)

### Community 28 - "Community 28"
Cohesion: 0.19
Nodes (20): ok(), Build a success envelope., cancel_job(), create_job(), get_job(), get_job_progress(), _job_to_dict(), list_jobs() (+12 more)

### Community 29 - "Community 29"
Cohesion: 0.18
Nodes (19): cmdBlocked(), cmdComplete(), cmdDeps(), cmdNext(), cmdParallel(), cmdStatus(), cmdValidate(), COMPLETED_DIR (+11 more)

### Community 30 - "Community 30"
Cohesion: 0.20
Nodes (20): Context Path Resolution Order, Git/PR Approval Workflow Gate, Lazy Loading Context Strategy, Lessons Learned Development Gate, Mypy as Blocking Type-Check Gate, Project Intelligence Living Documentation, Pure Functions Pattern, Essential Patterns - Core Development Guidelines (+12 more)

### Community 31 - "Community 31"
Cohesion: 0.26
Nodes (19): Component Plan (master-plan + component spec), 4-Stage Design Iteration Workflow, Design Plan File (.tmp/design-plans/), Image Specialist Subagent, OpenFrontendSpecialist Subagent, Visual Development Context, Code Review Guidelines, Component-Based Planning Workflow (+11 more)

### Community 32 - "Community 32"
Cohesion: 0.14
Nodes (18): cluster_faces(): DBSCAN-based face clustering, detect_and_store_faces(): face detection orchestration, FR-023: Face Detection and Embedding Storage, FR-025: Person Identity Management, FR-026: Face Boxes and Person Labels API, FR-027: Re-cluster-all and New-Faces-Only Modes, InsightFaceAdapter: face detection seam, Person CRUD: rename, merge, delete, list persons (+10 more)

### Community 33 - "Community 33"
Cohesion: 0.19
Nodes (17): Docs-Smoke Test Pattern for Machine-Checkable Examples, Query Evaluation Contract v1 Spec, evaluate_query() Pure Boolean Evaluator Entry Point, Query Grammar v1 Parser and Typed AST, QueryParseResult Typed Contract, QueryValidationError Typed Contract, FR-017..021 Query Parser Foundation Lessons Learned, FR-017..021 Query Value Validation Lessons Learned (+9 more)

### Community 34 - "Community 34"
Cohesion: 0.15
Nodes (17): Lookup: Command Reference, Installation Commands, Registry Commands, Testing Commands, Validation Commands, Workflow: Adding a New Agent, Lookup: File Locations, OpenAgents Lookup Navigation (+9 more)

### Community 35 - "Community 35"
Cohesion: 0.36
Nodes (5): _invalid_boolean_pair_error(), _missing_expression_after_boolean_error(), _Parser, _Token, QueryExpression

### Community 36 - "Community 36"
Cohesion: 0.15
Nodes (16): foundation.py Separation of Concerns Refactor, Gallery Creation via Hard Links (FR-012), Gallery Mutation Security (allowlist, traversal rejection, FR-016), Gallery Mutation Structured Errors (GalleryMutationError, ok/error payload), Gallery Source Selection Modes (query/picks/face sample), Proxy Baseline Modeling (plan/result dataclasses), RED-GREEN-REFACTOR TDD Cadence, Video Proxy Baseline (GeneratedProxy video_mp4_h264) (+8 more)

### Community 37 - "Community 37"
Cohesion: 0.15
Nodes (16): Code Review Guidelines, Lazy Initialization Pattern, Session Manifest JSON, Session Management, Session Directory Structure, CoderAgent, ContextScout Agent, Task Delegation Flow (+8 more)

### Community 38 - "Community 38"
Cohesion: 0.18
Nodes (9): test_fr_022_documented_query_examples_match_current_parser_contract(), _double_operator_error(), _is_integer_value(), _is_number_value(), _read_atom(), _read_operator(), _tokenize(), _validate_comparison() (+1 more)

### Community 39 - "Community 39"
Cohesion: 0.14
Nodes (14): RapidCull Business-Tech Bridge, Business to Technical Core Mapping, Gallery Lifecycle Mapping, Ingest and Metadata Foundation Mapping, Common Misalignments to Watch, Proxy Generation Mapping, Trade-off Decisions, RapidCull Business Constraints (+6 more)

### Community 40 - "Community 40"
Cohesion: 0.24
Nodes (13): Codebase References in Context Files, HTML Comment Frontmatter Format, Function-Based Folder Organization, MVI - Minimal Viable Information Principle, 8-Stage Organize Workflow, 8-Stage Update Workflow, Organize Operation, Update Operation (+5 more)

### Community 41 - "Community 41"
Cohesion: 0.22
Nodes (13): Dependency Alignment (pyproject.toml canonical, bootstrap, verify_system_deps), HEIC/HEIF Runtime Capability Preflight, ImageMagickAdapter (proxy seam with heif_supported injection), Proxy Batch Accounting (per-item generated/failed, tool_summary), Proxy Failure Reason Taxonomy Normalization, RAW Reason Normalization Guardrail (rawtherapee_pipeline_unavailable / rawtherapee_failed), RawTherapeeAdapter (RAW proxy seam with _run_command), Dependency Alignment Bootstrap and System Deps Lessons Learned (+5 more)

### Community 42 - "Community 42"
Cohesion: 0.27
Nodes (11): Continue-on-error pipeline pattern, ExifTool Persistent Batch Mode (-stay_open, -executeN), ExifTool Transport Recovery (restart + single retry), Galleries Index Refresh (galleries_index.json, FR-015), Gallery Metadata Rebuild (gallery.json, FR-014), FR-014 Single-Gallery Metadata Rebuild Lessons Learned, FR-014 Rebuild-All Galleries Metadata Lessons Learned, FR-015 Galleries Index Refresh Lessons Learned (+3 more)

### Community 43 - "Community 43"
Cohesion: 0.40
Nodes (10): QueryRecordValue, _as_int(), _as_number(), _compare_ordered_number(), _compare_ordered_text(), _evaluate_comparison(), _evaluate_date_comparison(), _evaluate_numeric_comparison() (+2 more)

### Community 44 - "Community 44"
Cohesion: 0.38
Nodes (10): FR-021: Query Grammar Validation, FR-022: Query Behavior Documentation, Session: FR-021 NOT Diagnostic Hardening, Session: FR-021 Open-Group EOF Diagnostics, Session: FR-022 Query Behavior Documentation Baseline, Session: FR-022 Query Docs Expansion, Session: FR-022 Query Docs Final Invalid Examples, src/rapidcull/query_grammar.py (+2 more)

### Community 45 - "Community 45"
Cohesion: 0.24
Nodes (10): Framer Motion useScroll/useTransform Pattern, React Functional Components and Hooks Best Practices, Scrollytelling: Scroll-Linked Image Sequence Animation, Tailwind CSS Utility-First Styling with Flowbite, Guide: Building Scrollytelling Pages, Lookup: Scroll Animation Image Generation Prompts, Web Design Patterns Navigation, Web UI Context Navigation (+2 more)

### Community 46 - "Community 46"
Cohesion: 0.20
Nodes (10): Custom Agent Definition, Custom Agents in OpenCode, Plugin Best Practices and Limitations, Message Injection Workarounds, Plugin Security Practices, OpenCode Plugin Context Library, Plugin Lifecycle and Packaging, Plugin Manifest (plugin.json) (+2 more)

### Community 47 - "Community 47"
Cohesion: 0.24
Nodes (10): Claude Code Hook to OpenCode Event Mapping, Command Events, OpenCode Plugin Events, Session Events, tool.execute.after Hook, tool.execute.before Hook, Hook-Based Delivery Pattern, Skill Lookup Map O(1) Optimization (+2 more)

### Community 48 - "Community 48"
Cohesion: 0.44
Nodes (9): ContextScout Subagent, External Context Cache (.tmp/external-context/), ExternalScout Subagent, TaskManager Subagent, Delegation Context Template, External Context Integration Guide, External Context Management, External Libraries FAQ (+1 more)

### Community 49 - "Community 49"
Cohesion: 0.42
Nodes (9): Query Evaluation Contract: AST-based record matching semantics, Query Grammar v1: field-operator-value structured grammar, Query Evaluation Contract v1, Query Grammar v1 Behavior, Session: Query Evaluation Contract v1, Session: Query Evaluation Semantics v1, Session: Query Evaluator Baseline v1, Session: Query Stale Doc Cleanup v1 (+1 more)

### Community 50 - "Community 50"
Cohesion: 0.61
Nodes (8): FR-024: Face Clustering, FR-028: Person Data and Embedding Deletion, Photo Library Acceptance Test Matrix, Photo Library Execution Checklist, Photo Fixture and Dataset Test Plan, Photo Library Requirements, Photo Library Test Plan, RapidCull README

### Community 51 - "Community 51"
Cohesion: 0.62
Nodes (7): Animation Micro-Syntax Notation, Advanced Animation Patterns, Animation Basics, Chat UI Animation Patterns, Component Animation Patterns, Form Animation Patterns, Loading State Animations

### Community 52 - "Community 52"
Cohesion: 0.33
Nodes (7): task-cli.ts CLI Script, JSON-Driven Task Management Schema, Guide: Managing Task Lifecycle, Guide: Splitting Features into Tasks, Task CLI Commands Lookup, Task Management Navigation, Task JSON Schema Standard

### Community 53 - "Community 53"
Cohesion: 0.29
Nodes (7): Subagent Agent Map, Subagent Framework Maps, Subagent Parent Map, Subagent Path Map, Delegation Mode Testing, Standalone Mode Testing, Subagent Testing Commands Quick Reference

### Community 54 - "Community 54"
Cohesion: 0.62
Nodes (6): detect_and_store_faces(), _faces_already_stored(), _generate_face_id(), _lookup_image_id(), _store_faces(), Path

### Community 55 - "Community 55"
Cohesion: 0.53
Nodes (6): Deterministic Orchestration via Injected Success Adapters, ImageMagick Adapter _run_command Subprocess Seam, ImageMagick HEIC Failure Reason Taxonomy, FR-006/007/008 Slice 3d Lessons Learned: ImageMagick Subprocess Seam Checkpoint, FR-006/007/008 Slice 3e Lessons Learned: HEIC Subprocess Path + Taxonomy Hardening, FR-007 Slice 3f Lessons Learned: HEIC Adapter Failure Subclasses

### Community 56 - "Community 56"
Cohesion: 0.60
Nodes (6): FR-021 Parser Diagnostics Hardening Series, FR-021 Grouped Expression Diagnostics Hardening Lessons Learned, FR-021 NOT Diagnostic Hardening Lessons Learned, FR-021 Grouped-Start Boolean Diagnostics Lessons Learned, FR-021 Open-Group EOF Diagnostics Lessons Learned, FR-021 Malformed Boolean-Pair Diagnostics Lessons Learned

### Community 57 - "Community 57"
Cohesion: 0.33
Nodes (6): OpenAgents Quality Navigation, check-context-deps Command, CI/CD Integration for Registry Validation, Component Dependency Types, Registry Dependency Validation, Registry Validation Workflow

### Community 59 - "Community 59"
Cohesion: 0.50
Nodes (5): Check Context Dependencies Command, Context Dependency Validation, Registry Integrity Validation, Validate Repository Command, registry.json Component Registry

### Community 60 - "Community 60"
Cohesion: 0.40
Nodes (5): Approval-First Commit Gate, Commit Command, Conventional Commit Message Format, Approval-First PR Gate, PR Command

### Community 61 - "Community 61"
Cohesion: 0.70
Nodes (5): Context7 API: Live Library Documentation Fetching, Context7 External Library Registry, Context7 Skill Navigation, Context7 Skill README, Context7 Skill Definition

### Community 62 - "Community 62"
Cohesion: 0.60
Nodes (5): FR-021 Query Grammar Parser Diagnostics (Grouped Expressions, Boolean Pairs), Session Context: FR-021 Grouped Expression Diagnostics Hardening, Session Context: FR-021 Grouped-Start Boolean Diagnostics, Session Context: FR-021 Malformed Boolean-Pair Diagnostics, Session Context: Query Grammar v1 Parser Foundation

### Community 63 - "Community 63"
Cohesion: 0.50
Nodes (4): ExifTool Persistent Process Protocol (-stay_open), FR-006/007/008 Real-Tool Proxy Adapters (ImageMagick, RawTherapee), ExifTool Persistent Batch Mode Python, Session Context: FR-006/007/008 Slice 1 Real-Tool Proxy Adapters

### Community 64 - "Community 64"
Cohesion: 0.83
Nodes (4): Pyenv Python 3.11 Project-Local Venv Setup, Pyenv Linux User-Space Noninteractive Python 3.11 Venv, Pytest Venv Invocation Remediation, Python Packaging requires-python Editable Install 3.10 vs 3.11

### Community 65 - "Community 65"
Cohesion: 0.50
Nodes (4): Backend Development Navigation (top-level), Backend Development Navigation (inner), Data Layer Navigation, Frontend Development Navigation

### Community 67 - "Community 67"
Cohesion: 0.67
Nodes (3): @opencode-ai/plugin dependency, dependencies, @opencode-ai/plugin

### Community 68 - "Community 68"
Cohesion: 0.50
Nodes (4): Middleware Pattern for Plugins, OpenCode Plugins Overview, Plugin Context Object, Plugin Registration Locations

### Community 69 - "Community 69"
Cohesion: 0.50
Nodes (4): Scroll-Linked Animation Technique, Scrollytelling Headphone Next.js Implementation, Concept: Scroll-Linked Animations, Example: Scrollytelling Headphone Animation

### Community 70 - "Community 70"
Cohesion: 0.50
Nodes (4): Context Bundle Best Practices, Context Bundle Sections, Context Bundle Template, OpenAgents Templates Navigation

### Community 71 - "Community 71"
Cohesion: 1.00
Nodes (3): Mypy Src Layout Configuration (py.typed, mypy_path), Mypy Missing py.typed Marker Src Layout Remediation, Mypy Python 3.11 Pyproject Best Practices

### Community 72 - "Community 72"
Cohesion: 0.67
Nodes (3): TDD red-green-refactor workflow, Lessons Learned: FR-004..005 Image ID and Failure Summary, Lessons Learned: Photo Library PR Plan (FR-001..003)

### Community 73 - "Community 73"
Cohesion: 0.67
Nodes (3): Design Theme: Modern Dark Mode Style, Design Theme: Neo-Brutalism Style, Design Systems

### Community 75 - "Community 75"
Cohesion: 0.67
Nodes (3): Building Custom Tools, Shell-Based Tools via Bun API, Custom Tool Zod Schema Definition

## Knowledge Gaps
- **201 isolated node(s):** `fs`, `path`, `PROJECT_ROOT`, `TASKS_DIR`, `COMPLETED_DIR` (+196 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `datetime` connect `Community 26` to `Face Detection Schema`, `Person CRUD Operations`, `Job Store Cancel Logic`, `Community 54`, `Community 28`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Why does `FailedIngestItem` connect `ImageMagick Proxy Adapters` to `CLI Processing Pipeline`, `Face Detection Schema`, `Gallery Hard-Link Creation`, `CLI Entry Point`, `Community 20`, `Community 54`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `ApiError` connect `Community 26` to `Community 28`, `Community 21`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Are the 38 inferred relationships involving `FailedIngestItem` (e.g. with `TestProcessNewEmptyDir` and `TestProcessNewHappyPath`) actually correct?**
  _`FailedIngestItem` has 38 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `Path` (e.g. with `ImageMagickProxyOutcome` and `FailedIngestItem`) actually correct?**
  _`Path` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `fs`, `path`, `PROJECT_ROOT` to the rest of the system?**
  _387 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `CLI Processing Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.05942571785268414 - nodes in this community are weakly interconnected._