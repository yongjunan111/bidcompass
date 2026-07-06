**Target**
Build a simulator-first recommendation path that maximizes `P(개찰순위 1위)` for 건설 적격심사 notices, without claiming `P(final win)`. Keep the current deterministic 0.9000 formula only as a fallback when current notice lacks full prelim-price data. Estimated total: `59h`.

**Phase 0: Scope & Rules**
- Input: current scope gates in [g2b_construction_sync.py](/home/dydwn/bidcompass/g2b/services/g2b_construction_sync.py), [ui_api.py](/home/dydwn/bidcompass/g2b/ui_api.py), rules in [bid_engine.py](/home/dydwn/bidcompass/g2b/services/bid_engine.py).
- Output: one canonical `support/fallback/reject` decision used by UI API and recommendation service.
- Support exactly: `procurement_type='공사'`, `win_method` contains `적격`, `0 < presume_price < 10_000_000_000`, `WorkType.CONSTRUCTION` only, `TableType in {TABLE_1,TABLE_2A,TABLE_3,TABLE_4,TABLE_5}`, and current notice has confirmed `A값`.
- Simulator-only support: current notice must also have `15` non-zero `BidApiPrelimPrice.basis_planned_price` rows. If only placeholder `sequence_no=0` base amount exists, fall back to deterministic mode.
- Historical training set: same construction-only scope, `openg_rank='1'` exists, `estimated_price>0`, `bid_amt>0`, `success_lowest_rate>0`, and only first opening round `COALESCE(NULLIF(bid_progress_ord,''),'1')='1'` to avoid rebid contamination.
- Rule variations to handle: construction table routing only, floor rate by `get_floor_rate`, optional explicit `net_construction_cost` hard floor, reserve-price draw weighting by historical prelim-selection patterns, and region/time relaxation only. Never relax across table type.
- Key files: create [prebid_scope.py](/home/dydwn/bidcompass/g2b/services/prebid_scope.py), modify [prebid_recommend.py](/home/dydwn/bidcompass/g2b/services/prebid_recommend.py), [ui_api.py](/home/dydwn/bidcompass/g2b/ui_api.py), [views.py](/home/dydwn/bidcompass/g2b/views.py).
- Effort: `3h`.
- Depends on: none.
- Risk: specialty notices slipping in through text heuristics. Mitigation: hard gate on construction scope helper before recommendation, and reject `SPECIALTY/TABLE_2B` explicitly.

**Phase 1: Data Preparation**
- Input: `BidResult`, `BidContract`, `BidAnnouncement`, `BidApiAValue`, `BidApiPrelimPrice`.
- Output: two materialized views plus one small weight table refreshed after the daily pipeline.
- Create `g2b_prebid_notice_pool`: `notice_key`, `bid_ntce_no`, `bid_ntce_ord`, `table_type`, `presume_price`, `estimated_price`, `base_amount`, `a_value_total`, `bidder_cnt`, `rank1_bid_amt`, `rank1_bid_rate`, `region_group`, `region_limited`, `openg_date`, `has_prelim15`.
- Create `g2b_prebid_bid_pool`: `notice_key`, `company_bizno`, `bid_amt`, `estimated_price`, `nominal_rate`, `amount_rank`.
- Create `g2b_prebid_prelim_weight`: `table_type`, `bidder_bucket`, `sorted_pos`, `weight`, `sample_size`, `updated_at`.
- Query 1 for `notice_pool`: `DISTINCT ON (bid_ntce_no,bid_ntce_ord)` rank-1 rows from `g2b_bidresult`, joined to eligible contracts, plus `SUM` of A-value fields from `g2b_bidapiavalue`, plus `MAX(base_amount)` and `COUNT(*) FILTER (basis_planned_price>0)` from `g2b_bidapiprelimprice`.
- Query 2 for `bid_pool`: join eligible `g2b_bidresult` rows to `notice_pool`, compute `nominal_rate = ROUND(bid_amt::numeric / NULLIF(estimated_price,0) * 100, 4)`, and `ROW_NUMBER() OVER (PARTITION BY notice_key ORDER BY bid_amt ASC, company_bizno ASC)`.
- Query 3 for `prelim_weight`: select notices with exactly `15` non-zero prelims and `4` drawn rows, then reuse the duplicate-safe sorted-position mapping logic from [analyze_prelim_selection.py](/home/dydwn/bidcompass/g2b/management/commands/analyze_prelim_selection.py) in Python to aggregate counts by `(table_type, bidder_bucket, sorted_pos)`.
- Indexes: unique index on `notice_pool.notice_key`, btree on `(table_type, openg_date DESC)`, `(table_type, region_group, openg_date DESC)`, and on `bid_pool(notice_key, amount_rank)`.
- Key files: create migration [0008_prebid_bootstrap_cache.py](/home/dydwn/bidcompass/g2b/migrations/0008_prebid_bootstrap_cache.py), create [refresh_prebid_bootstrap_cache.py](/home/dydwn/bidcompass/g2b/management/commands/refresh_prebid_bootstrap_cache.py), optionally create [prebid_cache.py](/home/dydwn/bidcompass/g2b/services/prebid_cache.py).
- Effort: `12h`.
- Depends on: Phase 0.
- Risk: refresh too slow or locks reads. Mitigation: materialized views, `REFRESH MATERIALIZED VIEW CONCURRENTLY`, and only eligible-construction subset.

**Phase 2: Bootstrap Simulator**
- Input: current notice context plus `15` current prelim prices and cached historical cohort tables.
- Output: `ScenarioSet` of about `2,000` market scenarios, each reduced to `est_price`, `effective_floor`, `lowest_valid_competitor_bid`, `tie_count_at_lowest`, `bidder_cnt`, `sampled_notice_key`.
- Cohort query: same `table_type`, last `24` months, same `region_group` if cohort `>=300`; else drop region; if still `<150`, extend to `36` months; if still `<80`, return fallback. Never mix table types.
- Sample bidder count and competitor set together by sampling one historical `notice_key` from `g2b_prebid_notice_pool`; that sampled event’s full bid list from `g2b_prebid_bid_pool` is the anonymous competitor market realization.
- Sample 예정가격 from the current notice’s own 15 prelims, not from historical notices. Sort current prelims ascending, fetch position weights from `g2b_prebid_prelim_weight` for `(table_type, sampled bidder bucket)`, sample `4` unique positions without replacement, then compute `est_price = floor(mean(selected 4))`. If weight row missing, fall back to `(table_type, ALL)`; if still missing, use uniform `4-of-15`.
- Convert sampled historical competitor `nominal_rate` to current-notice competitor bids with integer won amounts using `Decimal + ROUND_HALF_UP`, not Python `round()`.
- Apply current hard floor per scenario: `effective_floor = max(floor_rate_bid(est_price), explicit_net_cost_floor_if_provided)`. If no explicit net cost is given, estimated net-cost threshold stays advisory only.
- Discard competitor bids below `effective_floor`, then store the scenario minimum valid competitor bid and tie count. This keeps the simulator aligned with “safe to submit” recommendations.
- Use deterministic RNG seed `f"{bid_ntce_no}:{bid_ntce_ord}:{cache_refresh_date}"` so the same notice produces the same result between daily refreshes.
- Key files: create [prebid_bootstrap.py](/home/dydwn/bidcompass/g2b/services/prebid_bootstrap.py), create [prebid_market_loader.py](/home/dydwn/bidcompass/g2b/services/prebid_market_loader.py), reuse logic from [optimal_bid.py](/home/dydwn/bidcompass/g2b/services/optimal_bid.py).
- Effort: `14h`.
- Depends on: Phase 1.
- Risk: sparse cohorts or too many invalid competitor bids after floor filtering. Mitigation: stepwise cohort relaxation, minimum valid-competitor threshold per scenario, otherwise fallback.

**Phase 3: Optimizer**
- Input: `ScenarioSet`, current `a_value`, `table_type`, `base_amount`, `presume_price`.
- Output: `PreBidResult` with `optimal_bid`, `safe_bid`, `aggressive_bid`, `p_open_rank1`, `p_tie_rank1`, `scenario_count`, `cohort_count`, and expected price score.
- Do not brute-force scan wide ranges. Build candidate set from scenario breakpoints: `max_floor`, and for every scenario `lowest_valid_competitor_bid - 1` and `lowest_valid_competitor_bid`. That is where strict-win/tie/loss outcomes change.
- Hard lower bound is `max(scenario.effective_floor)` across all sampled scenarios. This guarantees the recommendation is valid under every sampled reserve-price outcome.
- Objective: maximize `strict_win_rate + 0.5 * tie_rate`, where `strict_win` means our bid is below the scenario minimum valid competitor bid.
- Tiebreaker 1: higher `strict_win_rate`.
- Tiebreaker 2: higher expected price score across the same scenarios, using the fast helper pattern from [optimal_bid.py](/home/dydwn/bidcompass/g2b/services/optimal_bid.py), then verify top candidates with `calc_price_score` from [bid_engine.py](/home/dydwn/bidcompass/g2b/services/bid_engine.py).
- Tiebreaker 3: higher bid amount among equal candidates, so the selected base bid is the safer point on the same probability plateau.
- Strategy band: `elite = candidates with objective within 0.01 absolute probability of best`. `aggressive_bid = min(elite)`, `safe_bid = max(elite)`, `optimal_bid = elite candidate with best expected price score`.
- Key files: create [prebid_optimizer.py](/home/dydwn/bidcompass/g2b/services/prebid_optimizer.py), modify [prebid_recommend.py](/home/dydwn/bidcompass/g2b/services/prebid_recommend.py).
- Effort: `8h`.
- Depends on: Phase 2.
- Risk: noisy optimizer output across reruns. Mitigation: fixed scenario set per notice, breakpoint-only search, deterministic seed.

**Phase 4: Integration**
- Input: simulator/optimizer service, existing UI/API payload shape.
- Output: production recommendation path with bootstrap-first, fallback-second behavior.
- Refactor [prebid_recommend.py](/home/dydwn/bidcompass/g2b/services/prebid_recommend.py) so `prebid_recommend(...)` accepts optional `preliminary_prices`, `bid_ntce_no`, `bid_ntce_ord`. If `15` prelim prices are present, run bootstrap mode; otherwise call `_legacy_fixed_ratio_recommend()` and mark `source='fallback_base_only'`.
- Extend `PreBidResult` but keep existing fields for compatibility. Change `optimal_score` meaning to “expected price score under sampled scenarios”, not “table max score”.
- Modify [ui_api.py](/home/dydwn/bidcompass/g2b/ui_api.py) `_build_recommendation_payload` to load current prelim rows, call the new service, preserve existing keys, and add an optional `simulation` block: `source`, `scenarioCount`, `cohortCount`, `pRank1`, `pTie1`, `reservePriceRange`.
- Modify [views.py](/home/dydwn/bidcompass/g2b/views.py) legacy recommend path similarly, so legacy pages and AI-report flow stop using the raw 0.9000 formula when full prelims exist.
- Add feature flag in [settings.py](/home/dydwn/bidcompass/config/settings.py): `PREBID_RECOMMEND_MODE = 'legacy' | 'bootstrap'`. Start with `'legacy'`, run validation, then flip to `'bootstrap'`.
- Add daily post-pipeline step: `uv run python manage.py refresh_prebid_bootstrap_cache`. This is stage 6 logically, but it should not block the existing 5-stage ingestion if it fails; request path can still fall back.
- Update tests in [tests.py](/home/dydwn/bidcompass/g2b/tests.py) and optionally UI display types in [types.ts](/home/dydwn/bidcompass/frontend/src/bidcompass-ui/types.ts) and [RecommendationResultPage.tsx](/home/dydwn/bidcompass/frontend/src/bidcompass-ui/pages/RecommendationResultPage.tsx).
- Effort: `10h`.
- Depends on: Phase 3.
- Risk: breaking existing UI/commands. Mitigation: preserve payload shape, keep fallback path, gate rollout with feature flag.

**Validation**
- Input: historical notices with confirmed A-values, 15 prelim prices, actual `estimated_price`, and actual rank-1 bid amount.
- Output: fold-by-fold backtest report and go/no-go decision.
- Create [backtest_prebid_rank1.py](/home/dydwn/bidcompass/g2b/management/commands/backtest_prebid_rank1.py).
- Method: monthly walk-forward. Use `12` months warm-up, train on all notices with `openg_date < test_month_start`, test on the next calendar month, then roll forward one month at a time.
- For each fold, rebuild temporary training-only `notice_pool`, `bid_pool`, and `prelim_weight`. Do not use the global daily cache inside the backtest command.
- For each test notice, run the recommendation using only data available before the test month. Current notice’s own A/prelim data are allowed; future notices are not.
- Primary metrics: `strict_top1_rate`, `strict_or_tie_top1_rate`, `floor_violation_rate`, and uplift vs current baseline `prebid_recommend` 0.9000 formula.
- Secondary metrics: calibration of predicted `p_open_rank1` by decile, mean actual price score of recommended bid, and fallback rate due to missing 15-prelim data.
- Pass criteria for rollout: `floor_violation_rate = 0`, strict-or-tie top1 uplift over baseline is positive, and calibration error is not obviously broken.
- Effort: `12h`.
- Depends on: Phases 1–4.
- Risk: time leakage and hidden reuse of future cache rows. Mitigation: fold-local temp tables with explicit `openg_date < cutoff` filter.

**What Not To Build**
- `P(final win)` or 낙찰확률.
- Bidder/company-specific models or bidder embeddings.
- Specialty/electrical/telecom/fire/heritage notices.
- Rebid/유찰 multi-round strategy modeling.
- ML models, feature stores, or per-request online learning.
- Full frontend redesign.
- Any request-path query that scans `32M+` raw `BidResult` rows.

**Suggested execution order**
- `uv run python manage.py migrate`
- `uv run python manage.py refresh_prebid_bootstrap_cache`
- `uv run python manage.py backtest_prebid_rank1 --start 2025-01 --end 2026-02`
- Flip `PREBID_RECOMMEND_MODE` to `bootstrap` only after the walk-forward report passes.