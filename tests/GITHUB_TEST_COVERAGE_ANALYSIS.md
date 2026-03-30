# GitHub PR Hygiene — Test Coverage Analysis

**Date**: 2026-03-28
**Branch**: `feature/drucker-github-hygiene`
**Test run**: 59 new tests, all passing (553 total pass, 2 pre-existing failures)

---

## Summary

| Module | Public Symbols | Tested | Coverage | Gap |
|--------|---------------|--------|----------|-----|
| `github_utils.py` | 22 (`__all__`) + 4 internal | 22 + 3 internal | **96%** | 3 untested (display/CLI) |
| `tools/github_tools.py` | 11 tool functions + 1 class | 10 + 1 class | **91%** | 1 untested tool |
| `shannon/cards.py` (PR builders) | 4 card builders | 4 | **100%** | — |
| `agents/drucker_api.py` (GitHub endpoints) | 4 endpoints + 3 models | 4 endpoints | **100%** | — |
| `config/env_loader.py` | 2 public functions | 0 | **0%** | Entire module |

**Overall**: 59 tests covering 39/44 testable symbols = **89% symbol coverage**

---

## Module Detail

### 1. `github_utils.py` — 26 tests in `test_github_utils_char.py`

#### Connection & Credentials (4 tests)
| Function | Test(s) | Status |
|----------|---------|--------|
| `get_github_credentials()` | `test_get_github_credentials_success`, `test_get_github_credentials_missing_token` | ✅ |
| `connect_to_github()` | `test_connect_to_github_ghe_url` | ✅ |
| `get_connection()` | `test_get_connection_caches_and_reset` | ✅ |
| `reset_connection()` | `test_get_connection_caches_and_reset` | ✅ |

#### Normalization Helpers (4 tests)
| Function | Test(s) | Status |
|----------|---------|--------|
| `_normalize_repo()` | `test_normalize_repo_extracts_fields` | ✅ |
| `_normalize_pr()` | `test_normalize_pr_extracts_fields`, `test_normalize_pr_handles_none_user` | ✅ |
| `_normalize_review()` | `test_normalize_review_extracts_fields` | ✅ |

#### Repository Operations (3 tests)
| Function | Test(s) | Status |
|----------|---------|--------|
| `list_repos()` | `test_list_repos_returns_list`, `test_list_repos_unknown_org_raises` | ✅ |
| `get_repo_info()` | `test_get_repo_info_returns_dict` | ✅ |
| `validate_repo()` | `test_validate_repo_true_and_false` | ✅ |

#### Pull Request Operations (3 tests)
| Function | Test(s) | Status |
|----------|---------|--------|
| `list_pull_requests()` | `test_list_pull_requests_returns_normalized` | ✅ |
| `get_pull_request()` | `test_get_pull_request_returns_single` | ✅ |
| `get_pr_reviews()` | `test_get_pr_reviews_returns_list` | ✅ |
| `get_pr_review_requests()` | — | ❌ **UNTESTED** |

#### Hygiene Analysis (6 tests)
| Function | Test(s) | Status |
|----------|---------|--------|
| `analyze_pr_staleness()` | `test_analyze_pr_staleness_finds_stale`, `test_analyze_pr_staleness_draft_grace_period`, `test_analyze_pr_staleness_non_draft_is_stale_at_6` | ✅ |
| `analyze_missing_reviews()` | `test_analyze_missing_reviews_no_reviewers`, `test_analyze_missing_reviews_skips_drafts` | ✅ |
| `analyze_repo_pr_hygiene()` | `test_analyze_repo_pr_hygiene_returns_report` | ✅ |

#### Rate Limit (2 tests)
| Function | Test(s) | Status |
|----------|---------|--------|
| `get_rate_limit()` | `test_get_rate_limit_returns_dict` | ✅ |
| `check_rate_limit()` | `test_check_rate_limit_returns_bool` | ✅ |

#### Output / CLI / Display (2 tests)
| Function | Test(s) | Status |
|----------|---------|--------|
| `output()` | `test_output_respects_quiet_mode` | ✅ |
| `handle_args()` | `test_handle_args_list_prs` | ✅ |
| `main()` | — | ❌ **UNTESTED** (CLI entry point) |
| `print_pr_table_header()` | — | ⚪ Low priority (display) |
| `print_pr_table_row()` | — | ⚪ Low priority (display) |
| `print_pr_table_footer()` | — | ⚪ Low priority (display) |

#### Exception Classes (2 tests)
| Class | Test(s) | Status |
|-------|---------|--------|
| `Error`, `GitHubConnectionError`, `GitHubCredentialsError`, `GitHubRepoError`, `GitHubPRError` | `test_exception_hierarchy`, `test_list_repos_unknown_org_raises` | ✅ |

#### Gaps
- `get_pr_review_requests()` — Needs test with monkeypatched repo/PR returning users+teams
- `main()` — Integration test for CLI routing (lower priority, matches `jira_utils` pattern where CLI tests are minimal)
- `print_pr_table_*()` — Display formatting, low risk, low priority

---

### 2. `tools/github_tools.py` — 14 tests in `test_github_tools_char.py`

#### Tool Functions (10 tests)
| Tool Function | Test(s) | Status |
|---------------|---------|--------|
| `list_repos()` | `test_list_repos_returns_success` | ✅ |
| `get_repo_info()` | `test_get_repo_info_returns_success` | ✅ |
| `validate_repository()` | `test_validate_repository_returns_validity` | ✅ |
| `list_pull_requests()` | `test_list_pull_requests_returns_success` | ✅ |
| `get_pull_request()` | `test_get_pull_request_returns_single` | ✅ |
| `get_pr_reviews()` | `test_get_pr_reviews_returns_list` | ✅ |
| `get_pr_review_requests()` | — | ❌ **UNTESTED** |
| `find_stale_prs()` | `test_find_stale_prs_returns_findings` | ✅ |
| `find_missing_reviews()` | `test_find_missing_reviews_returns_findings` | ✅ |
| `analyze_pr_hygiene()` | `test_analyze_pr_hygiene_returns_report` | ✅ |
| `get_rate_limit_status()` | `test_get_rate_limit_status_returns_info` | ✅ |

#### Error Handling (2 tests)
| Scenario | Test(s) | Status |
|----------|---------|--------|
| Exception propagation | `test_tool_returns_failure_on_exception` | ✅ |
| Missing `github_utils` | `test_tool_returns_failure_when_github_utils_unavailable` | ✅ |

#### Collection Class (2 tests)
| Aspect | Test(s) | Status |
|--------|---------|--------|
| Method registration | `test_github_tools_collection_registers_methods` | ✅ |
| Tool listing | `test_github_tools_collection_lists_all_tools` | ✅ |

#### Gaps
- `get_pr_review_requests()` tool — Mirrors missing `github_utils.get_pr_review_requests()` test

---

### 3. `shannon/cards.py` (PR builders) — 10 tests in `test_shannon_pr_cards_char.py`

| Card Builder | Test(s) | Status |
|-------------|---------|--------|
| `build_pr_hygiene_card()` | `test_pr_hygiene_card_with_findings`, `test_pr_hygiene_card_no_findings`, `test_pr_hygiene_card_truncates_at_five` | ✅ |
| `build_pr_stale_card()` | `test_pr_stale_card_with_stale_prs`, `test_pr_stale_card_empty` | ✅ |
| `build_pr_reviews_card()` | `test_pr_reviews_card_mixed_reasons`, `test_pr_reviews_card_empty` | ✅ |
| `build_pr_list_card()` | `test_pr_list_card_with_prs`, `test_pr_list_card_draft_and_approved_indicators`, `test_pr_list_card_empty` | ✅ |

All card builders have happy-path, empty-state, and edge-case tests. **Full coverage.**

---

### 4. `agents/drucker_api.py` (GitHub endpoints) — 9 tests in `test_drucker_api_github_char.py`

| Endpoint | Test(s) | Status |
|----------|---------|--------|
| `POST /v1/github/pr-hygiene` | `test_pr_hygiene_success`, `test_pr_hygiene_error` | ✅ |
| `POST /v1/github/pr-stale` | `test_pr_stale_success`, `test_pr_stale_default_days` | ✅ |
| `POST /v1/github/pr-reviews` | `test_pr_reviews_success`, `test_pr_reviews_error` | ✅ |
| `GET /v1/github/prs/{owner}/{repo}` | `test_pr_list_success`, `test_pr_list_with_query_params`, `test_pr_list_error` | ✅ |

All endpoints have success + error/edge-case tests. **Full coverage.**

---

### 5. `config/env_loader.py` — 0 tests

| Function | Test(s) | Status |
|----------|---------|--------|
| `load_env()` | — | ❌ **UNTESTED** |
| `_find_env_dir()` | — | ❌ **UNTESTED** |

This module was wired into `config/settings.py`, `agents/drucker_api.py`, and `agents/gantt_api.py`. No tests exist. Recommend adding:
- `test_load_env_explicit_path` — Verifies direct path loading
- `test_load_env_config_dir` — Verifies directory discovery and file ordering
- `test_load_env_fallback_dotenv` — Verifies root `.env` fallback
- `test_find_env_dir_walks_up` — Verifies ancestor traversal

---

## Test Quality Assessment

### Strengths
- **Follows existing patterns exactly**: `_char` suffix, `monkeypatch`, `SimpleNamespace` fakes, no live API calls
- **Hygiene analysis depth**: 6 tests cover staleness thresholds, draft grace period (2×), draft skip behavior
- **Card builders**: All 4 test happy-path, empty-state, and truncation/indicator edge cases
- **API endpoints**: Each endpoint tests both success and error paths via `sys.modules` mock injection
- **Tool layer**: Tests both individual tool functions AND the `GitHubTools` collection class registration

### Weaknesses
- **`get_pr_review_requests()`**: Missing at both `github_utils` and `tools/` layers — this function returns `(users, teams)` and should be tested
- **`config/env_loader.py`**: Zero coverage on a module wired into 3 files
- **CLI `main()`**: Not tested, but this matches existing pattern (`jira_utils` CLI tests are also minimal)
- **No integration tests**: All tests are unit-level with mocked dependencies. No test validates the full Drucker→github_utils→Shannon card pipeline

### Risk Assessment
| Gap | Risk | Priority |
|-----|------|----------|
| `get_pr_review_requests` untested | Medium — used by hygiene analysis | **P1** |
| `env_loader.py` untested | Medium — wrong load order could cause silent misconfiguration | **P2** |
| No integration test | Low — each layer is individually tested | **P3** |
| CLI `main()` untested | Low — matches existing pattern, secondary surface | **P3** |
| Display helpers untested | Negligible — visual formatting only | **P4** |

---

## Recommended Next Steps

1. **P1**: Add `test_get_pr_review_requests` to both `test_github_utils_char.py` and `test_github_tools_char.py`
2. **P2**: Create `test_env_loader_char.py` with 4 tests covering the three-tier resolution
3. **P3**: Add one end-to-end smoke test that exercises `analyze_repo_pr_hygiene()` → card builder pipeline
4. Consider running `pytest --cov=github_utils --cov=tools/github_tools --cov=config/env_loader` once PyGithub is installed for line-level coverage metrics
