# Integration evidence (Milestone 12)

Seam definitions, tiers and the Mermaid map are in `docs/architecture.md` section 9.1. This file maps each Tier 1 seam to its tests and records one run of exactly those tests.

## Tier 1 seams and their tests

| Seam | Tests (relative to repo root) | Notes |
|---|---|---|
| S1 Browser form to Flask routes | `tests/integration/test_dispatcher_ui_http.py::test_all_four_actions_work_through_the_page_forms`, `::test_a_refused_action_is_explained_in_words_on_the_page_and_changes_nothing`, `::test_the_action_urls_only_accept_posts_so_a_link_or_a_prefetch_cannot_trigger_them`, `::test_a_flagged_node_is_confirmed_recovered_from_the_page` | In-process Flask test client, real SQLite file |
| S2 Flask to SQLite, migrations, triggers | `tests/integration/test_database_rule.py::test_cannot_assign_a_unit_whose_proposal_is_not_approved[None]`, `::test_cannot_insert_a_unit_as_assigned_for_an_undecided_proposal`, `::test_migration_runner_applies_the_triggers_on_a_fresh_database`; `tests/integration/test_timestamps_and_concurrency_http.py::test_eight_threads_reserving_one_unit_exactly_one_wins` | Real SQLite, nothing mocked |
| S3 Money path | `tests/integration/test_notify_responder_http.py::test_auto_approved_report_notifies_but_held_one_does_not_until_approved`, `tests/integration/test_human_decision_http.py::test_demo_escalation_beat_through_the_routes`, `tests/integration/test_data_families_http.py::test_happy_reports_are_accepted_and_confirmed[happy-01]` | Rules model, not live Ollama |
| S4 Scenario CLI to running app | `tests/integration/test_scenario_live_server.py::test_the_command_line_plays_the_demo_scenario_into_a_real_running_server` (real server, real socket; passed 2026-11-15), `tests/integration/test_scenario_http.py::test_the_command_line_stops_loudly_when_the_app_is_not_running`, `::test_the_command_line_reports_a_bad_file_and_a_bad_speed_without_playing_anything`, `::test_the_demo_scenario_plays_through_the_real_route_in_order_with_the_right_spacing` | Gap: no test of the CLI against a live server |
| S5 Heartbeat processes to shared SQLite | `tests/integration/test_node_failure_detection.py::test_five_killed_node_processes_are_each_detected_within_thirty_seconds` (real processes), `::test_the_report_names_the_limit_and_the_worst_case`; `tests/integration/test_heartbeat_http.py::test_a_flagged_node_is_recovered_only_when_a_dispatcher_confirms_through_the_route` | The 33 s real-process test was not run for this file |
| S6 Classify service to Ollama over HTTP | `tests/unit/test_ollama_client.py::test_nothing_listening_is_reported_as_unavailable`, `::test_a_slow_server_times_out_instead_of_waiting_forever`, `::test_a_busy_or_rate_limited_server_is_reported_as_busy[429]`, `[503]`, `::test_a_changed_or_malformed_response_is_reported_as_bad[no_message]`, `::test_a_redirect_is_never_followed`; the ten `tests/integration/test_ollama_chaos_http.py` tests and `tests/integration/test_model_chain_http.py` test listed under Results | Real loopback HTTP stub (`tests/ollama_stub.py`); the real model was run once by hand (CR-011) |
| S9 Purge job to database | `tests/integration/test_privacy_http.py::test_the_command_line_purge_removes_old_data_and_reports_what_it_did`, `::test_the_command_line_purge_fails_loudly_and_changes_nothing`; `tests/integration/test_reconcile_http.py::test_the_purge_removes_versions_and_their_log_after_24_hours` | First two run the real script in a subprocess |

Tier 2 seams (S7 files, S8 CI runner) are in section 9.1; S7 cites `tests/integration/test_data_families_http.py::test_the_data_is_reproducible_from_the_fixed_seed`, which is included in the run below.

## Results

- Date: 2026-11-15
- Command (run from the repository root; a bash array of the ids below was passed as arguments):
  `./.venv/Scripts/python -m pytest <the 37 node ids listed below> -p no:cacheprovider -q -rA --no-cov`
- Outcome: **37 passed, 0 failed**, 38.58 s.
- Not run here: `tests/integration/test_node_failure_detection.py::test_five_killed_node_processes_are_each_detected_within_thirty_seconds` (33 s, CPU heavy): **run separately by the release engineer**.
- Parametrised cases not run here (they exist but are not cited): the other `[...]` variants of the chaos, client and data-family tests. Whole-suite results are in `docs/test-results.md`.

| # | Test id | Result |
|---|---|---|
| 1 | tests/integration/test_dispatcher_ui_http.py::test_all_four_actions_work_through_the_page_forms | pass |
| 2 | tests/integration/test_dispatcher_ui_http.py::test_a_refused_action_is_explained_in_words_on_the_page_and_changes_nothing | pass |
| 3 | tests/integration/test_dispatcher_ui_http.py::test_the_action_urls_only_accept_posts_so_a_link_or_a_prefetch_cannot_trigger_them | pass |
| 4 | tests/integration/test_dispatcher_ui_http.py::test_a_flagged_node_is_confirmed_recovered_from_the_page | pass |
| 5 | tests/integration/test_database_rule.py::test_cannot_assign_a_unit_whose_proposal_is_not_approved[None] | pass |
| 6 | tests/integration/test_database_rule.py::test_cannot_insert_a_unit_as_assigned_for_an_undecided_proposal | pass |
| 7 | tests/integration/test_database_rule.py::test_migration_runner_applies_the_triggers_on_a_fresh_database | pass |
| 8 | tests/integration/test_timestamps_and_concurrency_http.py::test_eight_threads_reserving_one_unit_exactly_one_wins | pass |
| 9 | tests/integration/test_notify_responder_http.py::test_auto_approved_report_notifies_but_held_one_does_not_until_approved | pass |
| 10 | tests/integration/test_human_decision_http.py::test_demo_escalation_beat_through_the_routes | pass |
| 11 | tests/integration/test_scenario_http.py::test_the_demo_scenario_plays_through_the_real_route_in_order_with_the_right_spacing | pass |
| 12 | tests/integration/test_scenario_http.py::test_the_command_line_stops_loudly_when_the_app_is_not_running | pass |
| 13 | tests/integration/test_scenario_http.py::test_the_command_line_reports_a_bad_file_and_a_bad_speed_without_playing_anything | pass |
| 14 | tests/integration/test_node_failure_detection.py::test_the_report_names_the_limit_and_the_worst_case | pass |
| 15 | tests/integration/test_heartbeat_http.py::test_a_flagged_node_is_recovered_only_when_a_dispatcher_confirms_through_the_route | pass |
| 16 | tests/unit/test_ollama_client.py::test_nothing_listening_is_reported_as_unavailable | pass |
| 17 | tests/unit/test_ollama_client.py::test_a_slow_server_times_out_instead_of_waiting_forever | pass |
| 18 | tests/unit/test_ollama_client.py::test_a_busy_or_rate_limited_server_is_reported_as_busy[429] | pass |
| 19 | tests/unit/test_ollama_client.py::test_a_busy_or_rate_limited_server_is_reported_as_busy[503] | pass |
| 20 | tests/unit/test_ollama_client.py::test_a_changed_or_malformed_response_is_reported_as_bad[no_message] | pass |
| 21 | tests/unit/test_ollama_client.py::test_a_redirect_is_never_followed | pass |
| 22 | tests/integration/test_ollama_chaos_http.py::test_with_the_model_up_the_proposal_comes_from_it_and_names_it | pass |
| 23 | tests/integration/test_ollama_chaos_http.py::test_with_the_model_server_down_the_report_is_still_classified_by_the_rules_tier_and_says_so | pass |
| 24 | tests/integration/test_ollama_chaos_http.py::test_each_failure_mode_of_the_model_server_falls_back_instead_of_failing_the_report[429] | pass |
| 25 | tests/integration/test_ollama_chaos_http.py::test_each_failure_mode_of_the_model_server_falls_back_instead_of_failing_the_report[503] | pass |
| 26 | tests/integration/test_ollama_chaos_http.py::test_each_failure_mode_of_the_model_server_falls_back_instead_of_failing_the_report[wrong_shape] | pass |
| 27 | tests/integration/test_ollama_chaos_http.py::test_each_failure_mode_of_the_model_server_falls_back_instead_of_failing_the_report[no_message] | pass |
| 28 | tests/integration/test_ollama_chaos_http.py::test_a_slow_model_server_is_cut_off_at_the_time_cap_and_the_report_still_goes_through | pass |
| 29 | tests/integration/test_ollama_chaos_http.py::test_the_model_dying_in_the_middle_of_a_scenario_degrades_the_rest_of_it_and_nothing_crashes | pass |
| 30 | tests/integration/test_ollama_chaos_http.py::test_the_kill_switch_takes_effect_on_the_next_report_with_no_restart_and_no_call_to_the_server | pass |
| 31 | tests/integration/test_ollama_chaos_http.py::test_a_model_that_answers_badly_every_time_never_gets_more_than_two_calls_per_report | pass |
| 32 | tests/integration/test_model_chain_http.py::test_with_every_model_down_the_report_goes_to_a_human_and_the_reply_says_so | pass |
| 33 | tests/integration/test_data_families_http.py::test_the_data_is_reproducible_from_the_fixed_seed | pass |
| 34 | tests/integration/test_data_families_http.py::test_happy_reports_are_accepted_and_confirmed[happy-01] | pass |
| 35 | tests/integration/test_privacy_http.py::test_the_command_line_purge_removes_old_data_and_reports_what_it_did | pass |
| 36 | tests/integration/test_privacy_http.py::test_the_command_line_purge_fails_loudly_and_changes_nothing | pass |
| 37 | tests/integration/test_reconcile_http.py::test_the_purge_removes_versions_and_their_log_after_24_hours | pass |
| - | tests/integration/test_node_failure_detection.py::test_five_killed_node_processes_are_each_detected_within_thirty_seconds | run separately by the release engineer |
