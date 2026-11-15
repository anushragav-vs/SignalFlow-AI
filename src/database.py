"""
SignalFlow AI - SQLite History & Audit Persistence Layer
Preserves both original Strands Decider model classifications and human review actions without overwriting.
"""

import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from config import config
from src.deduplication import (
    normalize_headline,
    canonicalize_url,
    compute_article_fingerprint,
    extract_published_date,
)

DEFAULT_DB_PATH = config.sqlite_db_path


class SignalFlowDatabase:
    """
    Manages SQLite database storage for signals, cloud summaries, and the review queue.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or config.sqlite_db_path
        self._mem_conn = None
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self.db_path == ":memory:":
            if self._mem_conn is None:
                self._mem_conn = sqlite3.connect(":memory:")
                self._mem_conn.row_factory = sqlite3.Row
            return self._mem_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    headline TEXT NOT NULL,
                    canonical_url TEXT,
                    publisher TEXT NOT NULL,
                    is_live INTEGER DEFAULT 1,
                    
                    -- Original Model Output (Never Overwritten)
                    decider_sentiment TEXT NOT NULL,
                    decider_confidence REAL NOT NULL,
                    probabilities_json TEXT,
                    decider_latency_ms REAL DEFAULT 0.0,
                    decider_model_id TEXT,
                    
                    -- Policy Engine Routing
                    policy_action TEXT NOT NULL,
                    policy_reason TEXT,
                    
                    -- Human-in-the-Loop Review Audit Trail
                    review_status TEXT NOT NULL DEFAULT 'NONE', -- 'NONE', 'PENDING', 'CONFIRMED', 'RECLASSIFIED', 'DISMISSED'
                    reviewer_action TEXT,
                    reviewer_notes TEXT,
                    corrected_label TEXT,
                    reviewed_at TEXT,
                    
                    -- Google Gemini Cloud Analysis
                    gemini_model_id TEXT,
                    gemini_status TEXT, -- 'success', 'skipped_by_policy', 'queued_for_review', 'error_...'
                    event_summary TEXT,
                    transmission_mechanism TEXT,
                    affected_assets_json TEXT,
                    directional_implications TEXT,
                    uncertainties_json TEXT,
                    reported_facts_json TEXT,
                    analytical_hypotheses_json TEXT,
                    raw_summary TEXT,
                    cloud_latency_ms REAL DEFAULT 0.0,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    total_tokens INTEGER,
                    estimated_cost_usd REAL DEFAULT 0.0
                )
            """)
            conn.commit()

            # Dynamic column migration for seamless schema evolution
            cursor = conn.execute("PRAGMA table_info(signals)")
            existing_cols = {row["name"] for row in cursor.fetchall()}
            columns_to_ensure = [
                ("canonical_url", "TEXT"),
                ("is_live", "INTEGER DEFAULT 1"),
                ("decider_model_id", "TEXT"),
                ("reviewer_action", "TEXT"),
                ("reviewer_notes", "TEXT"),
                ("corrected_label", "TEXT"),
                ("reviewed_at", "TEXT"),
                ("event_summary", "TEXT"),
                ("transmission_mechanism", "TEXT"),
                ("directional_implications", "TEXT"),
                ("analytical_hypotheses_json", "TEXT"),
                ("catalyst_watchpoints_json", "TEXT"),
                ("market_impact_horizon", "TEXT"),
                ("institutional_risk_level", "TEXT"),
                ("peer_impact_json", "TEXT"),
                ("detected_entities_json", "TEXT"),
                ("affected_instruments_json", "TEXT"),
                ("currencies_json", "TEXT"),
                ("economic_events_json", "TEXT"),
                ("impact_score", "INTEGER"),
                ("impact_level", "TEXT"),
                ("impact_dimensions_json", "TEXT"),
                ("event_category", "TEXT"),
                ("volatility_assessment", "TEXT"),
                ("impact_explanation", "TEXT"),
                ("impact_methodology", "TEXT"),
                ("impact_limitations_json", "TEXT"),
                ("article_fingerprint", "TEXT"),
            ]
            for col_name, col_type in columns_to_ensure:
                if col_name not in existing_cols:
                    conn.execute(f"ALTER TABLE signals ADD COLUMN {col_name} {col_type}")
            conn.commit()

            # Create performance indices for article deduplication
            conn.execute("CREATE INDEX IF NOT EXISTS idx_signals_fingerprint ON signals (article_fingerprint)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_signals_canonical_url ON signals (canonical_url)")
            conn.commit()

            # Alerts & Rule Management Tables
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alert_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    condition_type TEXT NOT NULL,
                    target_value TEXT,
                    min_confidence REAL DEFAULT 0.80,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS market_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id INTEGER NOT NULL,
                    rule_id INTEGER,
                    alert_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'warning',
                    created_at TEXT NOT NULL,
                    is_read INTEGER DEFAULT 0
                )
            """)
            conn.commit()

            # Seed default alert rules if empty
            rules_count = conn.execute("SELECT COUNT(*) FROM alert_rules").fetchone()[0]
            if rules_count == 0:
                ts = datetime.now(timezone.utc).isoformat()
                conn.execute(
                    "INSERT INTO alert_rules (name, condition_type, target_value, min_confidence, enabled, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    ("Critical Market Impact Event", "critical_impact", None, 0.80, 1, ts),
                )
                conn.execute(
                    "INSERT INTO alert_rules (name, condition_type, target_value, min_confidence, enabled, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    ("High Market Impact Event", "high_impact", None, 0.80, 1, ts),
                )
                conn.execute(
                    "INSERT INTO alert_rules (name, condition_type, target_value, min_confidence, enabled, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    ("Federal Reserve Announcement", "central_bank_event", "Federal Reserve", 0.75, 1, ts),
                )
                conn.execute(
                    "INSERT INTO alert_rules (name, condition_type, target_value, min_confidence, enabled, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    ("EUR/USD Watchlist Transmission", "watchlist_pair", "EUR/USD", 0.80, 1, ts),
                )
                conn.commit()

    def find_existing_signal_id(
        self,
        fingerprint: Optional[str] = None,
        canonical_url: str = "",
        headline: str = "",
        publisher: str = "",
        published_at: Optional[str] = None,
    ) -> Optional[int]:
        """
        Finds an existing signal ID using the 3-tier identity priority:
        1. Exact article_fingerprint match
        2. Canonical URL match (normalized http/https)
        3. Normalized headline + publisher match (fallback)
        """
        with self._get_connection() as conn:
            # Priority 1: Match by fingerprint
            if fingerprint:
                row = conn.execute(
                    "SELECT id FROM signals WHERE article_fingerprint = ? LIMIT 1",
                    (fingerprint,),
                ).fetchone()
                if row:
                    return row["id"]

            # Priority 2: Match by canonical URL
            clean_url = canonicalize_url(canonical_url)
            if clean_url and clean_url.startswith(("http://", "https://")):
                row = conn.execute(
                    "SELECT id FROM signals WHERE canonical_url = ? OR canonical_url = ? LIMIT 1",
                    (clean_url, canonical_url),
                ).fetchone()
                if row:
                    return row["id"]

            # Priority 3: Fallback match by normalized headline + publisher
            norm_h = normalize_headline(headline)
            norm_pub = (publisher or "").strip().lower()
            if norm_h and norm_pub:
                rows = conn.execute(
                    "SELECT id, headline, publisher FROM signals ORDER BY id DESC LIMIT 250"
                ).fetchall()
                for r in rows:
                    if (
                        (r["publisher"] or "").strip().lower() == norm_pub
                        and normalize_headline(r["headline"]) == norm_h
                    ):
                        return r["id"]

        return None

    def insert_signal(
        self,
        headline: str,
        publisher: str,
        decider_sentiment: str,
        decider_confidence: float,
        policy_action: str,
        policy_reason: str,
        canonical_url: str = "",
        is_live: bool = True,
        probabilities: Optional[Dict[str, float]] = None,
        decider_latency_ms: float = 0.0,
        decider_model_id: str = "",
        review_status: str = "NONE",
        provider_article_id: Optional[str] = None,
        published_at: Optional[str] = None,
        article_fingerprint: Optional[str] = None,
    ) -> int:
        """
        Idempotently inserts or retrieves a signal. If the article already exists
        based on provider ID, canonical URL, or fallback fingerprint, returns the existing ID.
        """
        ts = published_at or datetime.now(timezone.utc).isoformat()
        clean_url = canonicalize_url(canonical_url)
        fp = article_fingerprint or compute_article_fingerprint(
            provider_article_id=provider_article_id,
            canonical_url=clean_url or canonical_url,
            headline=headline,
            publisher=publisher,
            published_at=ts,
        )

        # Idempotent deduplication check
        existing_id = self.find_existing_signal_id(
            fingerprint=fp,
            canonical_url=clean_url or canonical_url,
            headline=headline,
            publisher=publisher,
            published_at=ts,
        )
        if existing_id is not None:
            # Update missing canonical_url or fingerprint if existing row lacked them
            with self._get_connection() as conn:
                conn.execute(
                    """
                    UPDATE signals
                    SET article_fingerprint = COALESCE(article_fingerprint, ?),
                        canonical_url = CASE WHEN canonical_url IS NULL OR canonical_url = '' THEN ? ELSE canonical_url END
                    WHERE id = ?
                    """,
                    (fp, clean_url or canonical_url, existing_id),
                )
                conn.commit()
            return existing_id

        # Insert new unique signal
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO signals (
                    timestamp, headline, canonical_url, publisher, is_live,
                    decider_sentiment, decider_confidence, probabilities_json,
                    decider_latency_ms, decider_model_id, policy_action, policy_reason,
                    review_status, article_fingerprint
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ts,
                    headline,
                    clean_url or canonical_url,
                    publisher,
                    1 if is_live else 0,
                    decider_sentiment,
                    decider_confidence,
                    json.dumps(probabilities or {}),
                    decider_latency_ms,
                    decider_model_id,
                    policy_action,
                    policy_reason,
                    review_status,
                    fp,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def update_gemini_analysis(
        self,
        signal_id: int,
        gemini_model_id: str,
        gemini_status: str,
        raw_summary: str = "",
        event_summary: str = "",
        transmission_mechanism: str = "",
        affected_assets: Optional[List[str]] = None,
        directional_implications: str = "",
        uncertainties: Optional[List[str]] = None,
        reported_facts: Optional[List[str]] = None,
        analytical_hypotheses: Optional[List[str]] = None,
        cloud_latency_ms: float = 0.0,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        estimated_cost_usd: float = 0.0,
        catalyst_watchpoints: Optional[List[str]] = None,
        market_impact_horizon: str = "",
        institutional_risk_level: str = "",
        peer_impact: Optional[List[str]] = None,
    ):
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE signals
                SET gemini_model_id = ?,
                    gemini_status = ?,
                    raw_summary = ?,
                    event_summary = ?,
                    transmission_mechanism = ?,
                    affected_assets_json = ?,
                    directional_implications = ?,
                    uncertainties_json = ?,
                    reported_facts_json = ?,
                    analytical_hypotheses_json = ?,
                    catalyst_watchpoints_json = ?,
                    market_impact_horizon = ?,
                    institutional_risk_level = ?,
                    peer_impact_json = ?,
                    cloud_latency_ms = ?,
                    input_tokens = ?,
                    output_tokens = ?,
                    total_tokens = ?,
                    estimated_cost_usd = ?
                WHERE id = ?
                """,
                (
                    gemini_model_id,
                    gemini_status,
                    raw_summary,
                    event_summary,
                    transmission_mechanism,
                    json.dumps(affected_assets or []),
                    directional_implications,
                    json.dumps(uncertainties or []),
                    json.dumps(reported_facts or []),
                    json.dumps(analytical_hypotheses or []),
                    json.dumps(catalyst_watchpoints or []),
                    market_impact_horizon,
                    institutional_risk_level,
                    json.dumps(peer_impact or []),
                    cloud_latency_ms,
                    input_tokens,
                    output_tokens,
                    total_tokens,
                    estimated_cost_usd,
                    signal_id,
                ),
            )
            conn.commit()

    @staticmethod
    def merge_affected_instruments(
        existing_json: Optional[str],
        new_instruments: Optional[List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """
        Merges affected instruments by symbol without duplicates,
        upgrading relationship priority: direct > indirect > potential.
        """
        existing: List[Dict[str, Any]] = []
        if existing_json:
            try:
                parsed = json.loads(existing_json)
                if isinstance(parsed, list):
                    existing = parsed
            except Exception:
                existing = []

        if not new_instruments:
            return existing

        priority_map = {"direct": 3, "indirect": 2, "potential": 1}
        merged_by_symbol: Dict[str, Dict[str, Any]] = {}

        for item in existing:
            sym = item.get("symbol")
            if sym:
                merged_by_symbol[sym] = dict(item)

        for item in new_instruments:
            sym = item.get("symbol")
            if not sym:
                continue
            if sym not in merged_by_symbol:
                merged_by_symbol[sym] = dict(item)
            else:
                curr = merged_by_symbol[sym]
                curr_rel = (curr.get("relationship") or "indirect").lower()
                new_rel = (item.get("relationship") or "indirect").lower()
                curr_p = priority_map.get(curr_rel, 0)
                new_p = priority_map.get(new_rel, 0)

                if new_p > curr_p:
                    curr["relationship"] = new_rel
                    curr["confidence"] = max(curr.get("confidence", 0.0), item.get("confidence", 0.0))
                    if item.get("reason"):
                        curr["reason"] = item["reason"]
                    curr["mentioned_explicitly"] = curr.get("mentioned_explicitly", False) or item.get("mentioned_explicitly", False)
                elif new_p == curr_p:
                    curr["confidence"] = max(curr.get("confidence", 0.0), item.get("confidence", 0.0))
                    curr_reason = curr.get("reason", "")
                    new_reason = item.get("reason", "")
                    if new_reason and new_reason != curr_reason and new_reason not in curr_reason:
                        curr["reason"] = f"{curr_reason}; {new_reason}".strip("; ")

        return list(merged_by_symbol.values())

    def update_intelligence_analysis(
        self,
        signal_id: int,
        detected_entities: Optional[List[Dict[str, Any]]] = None,
        affected_instruments: Optional[List[Dict[str, Any]]] = None,
        currencies: Optional[List[str]] = None,
        economic_events: Optional[List[str]] = None,
        impact_score: Optional[int] = None,
        impact_level: Optional[str] = None,
        impact_dimensions: Optional[Dict[str, Any]] = None,
        event_category: Optional[str] = None,
        volatility_assessment: Optional[str] = None,
        impact_explanation: Optional[str] = None,
        impact_methodology: str = "rule_based",
        impact_limitations: Optional[List[str]] = None,
    ):
        """
        Stores Smart Ticker Detection and Market Impact Predictor results.
        Strictly preserves original decider sentiment and human review fields.
        Merges affected instruments cleanly without duplicates.
        """
        with self._get_connection() as conn:
            # Check existing instruments to merge cleanly
            cursor = conn.execute("SELECT affected_instruments_json FROM signals WHERE id = ?", (signal_id,))
            row = cursor.fetchone()
            existing_aff_json = row["affected_instruments_json"] if row else None
            merged_instruments = self.merge_affected_instruments(existing_aff_json, affected_instruments)

            conn.execute(
                """
                UPDATE signals
                SET detected_entities_json = ?,
                    affected_instruments_json = ?,
                    currencies_json = ?,
                    economic_events_json = ?,
                    impact_score = ?,
                    impact_level = ?,
                    impact_dimensions_json = ?,
                    event_category = ?,
                    volatility_assessment = ?,
                    impact_explanation = ?,
                    impact_methodology = ?,
                    impact_limitations_json = ?
                WHERE id = ?
                """,
                (
                    json.dumps(detected_entities or []),
                    json.dumps(merged_instruments),
                    json.dumps(currencies or []),
                    json.dumps(economic_events or []),
                    impact_score,
                    impact_level,
                    json.dumps(impact_dimensions or {}),
                    event_category,
                    volatility_assessment,
                    impact_explanation,
                    impact_methodology,
                    json.dumps(impact_limitations or []),
                    signal_id,
                ),
            )
            conn.commit()

    def deduplicate_existing_signals(self) -> Dict[str, Any]:
        """
        Safely scans existing signals in the database, identifies duplicates
        using the 3-tier identity priority, merges instruments and coverage,
        updates dependent alert records, and removes duplicate rows.
        """
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM signals ORDER BY id ASC")
            all_signals = [dict(r) for r in cursor.fetchall()]

            grouped: Dict[str, List[Dict[str, Any]]] = {}
            for s in all_signals:
                fp = s.get("article_fingerprint")
                can_u = canonicalize_url(s.get("canonical_url") or "")
                norm_h = normalize_headline(s.get("headline") or "")
                pub = (s.get("publisher") or "").strip().lower()

                if can_u and can_u.startswith(("http://", "https://")):
                    key = f"URL:{can_u}"
                elif fp and fp.startswith(("PID:", "URL:")):
                    key = fp
                else:
                    key = f"TEXT:{pub}|{norm_h}"

                grouped.setdefault(key, []).append(s)

            duplicates_removed = 0
            canonical_records_updated = 0

            for key, rows in grouped.items():
                if len(rows) <= 1:
                    s = rows[0]
                    if not s.get("article_fingerprint"):
                        fp = compute_article_fingerprint(
                            canonical_url=s.get("canonical_url"),
                            headline=s.get("headline", ""),
                            publisher=s.get("publisher", ""),
                            published_at=s.get("timestamp"),
                        )
                        conn.execute("UPDATE signals SET article_fingerprint = ? WHERE id = ?", (fp, s["id"]))
                    continue

                # Rank candidate rows to pick the best/canonical record:
                # 1. Has gemini_status == 'success' or event_summary
                # 2. Has impact_score IS NOT NULL
                # 3. Has canonical_url non-empty
                # 4. Earliest ID (first recorded ingestion)
                def rank_signal(r: Dict[str, Any]):
                    score = 0
                    if r.get("gemini_status") == "success" or r.get("event_summary"):
                        score += 100
                    if r.get("impact_score") is not None:
                        score += 50
                    if r.get("canonical_url"):
                        score += 20
                    return (score, -r["id"])

                sorted_rows = sorted(rows, key=rank_signal, reverse=True)
                canonical_row = sorted_rows[0]
                duplicate_rows = sorted_rows[1:]

                canonical_id = canonical_row["id"]
                duplicate_ids = [d["id"] for d in duplicate_rows]

                # Merge affected_instruments across all duplicate rows
                all_instruments = []
                for r in rows:
                    raw_aff = r.get("affected_instruments_json")
                    if raw_aff:
                        try:
                            parsed = json.loads(raw_aff)
                            if isinstance(parsed, list):
                                all_instruments.extend(parsed)
                        except Exception:
                            pass

                merged_instruments = self.merge_affected_instruments(None, all_instruments)

                fp = canonical_row.get("article_fingerprint") or compute_article_fingerprint(
                    canonical_url=canonical_row.get("canonical_url"),
                    headline=canonical_row.get("headline", ""),
                    publisher=canonical_row.get("publisher", ""),
                    published_at=canonical_row.get("timestamp"),
                )

                conn.execute(
                    """
                    UPDATE signals
                    SET article_fingerprint = ?,
                        affected_instruments_json = ?
                    WHERE id = ?
                    """,
                    (fp, json.dumps(merged_instruments), canonical_id),
                )

                if duplicate_ids:
                    placeholders = ",".join("?" for _ in duplicate_ids)
                    conn.execute(
                        f"UPDATE market_alerts SET signal_id = ? WHERE signal_id IN ({placeholders})",
                        (canonical_id, *duplicate_ids),
                    )
                    conn.execute(
                        f"DELETE FROM signals WHERE id IN ({placeholders})",
                        tuple(duplicate_ids),
                    )
                    duplicates_removed += len(duplicate_ids)
                    canonical_records_updated += 1

            conn.commit()
            return {
                "total_scanned": len(all_signals),
                "unique_records": len(grouped),
                "duplicates_removed": duplicates_removed,
                "canonical_updated": canonical_records_updated,
            }

    def record_review_action(
        self,
        signal_id: int,
        action: str,  # 'CONFIRMED', 'RECLASSIFIED', 'DISMISSED'
        corrected_label: Optional[str] = None,
        notes: str = "",
    ):
        """
        Records human oversight. Preserves the original decider_sentiment.
        """
        reviewed_at = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE signals
                SET review_status = ?,
                    reviewer_action = ?,
                    corrected_label = ?,
                    reviewer_notes = ?,
                    reviewed_at = ?
                WHERE id = ?
                """,
                (
                    action,
                    action,
                    corrected_label,
                    notes,
                    reviewed_at,
                    signal_id,
                ),
            )
            conn.commit()

    def get_pending_reviews(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM signals WHERE review_status = 'PENDING' ORDER BY id DESC"
            )
            return [dict(r) for r in cursor.fetchall()]

    def get_recent_signals(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM signals ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            return [dict(r) for r in cursor.fetchall()]

    def get_signal_by_id(self, signal_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM signals WHERE id = ?", (signal_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_kpis(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
            if total == 0:
                return {
                    "total_received": 0,
                    "unique_processed": 0,
                    "bullish_count": 0,
                    "bearish_count": 0,
                    "neutral_count": 0,
                    "noise_count": 0,
                    "escalated_for_review": 0,
                    "sent_to_gemini": 0,
                    "successful_analyses": 0,
                    "failed_analyses": 0,
                    "cloud_calls_avoided_count": 0,
                    "cloud_calls_avoided_pct": 0.0,
                    "total_cloud_spend_usd": 0.0,
                    "avg_decider_latency_ms": 0.0,
                    "avg_cloud_latency_ms": 0.0,
                }

            unique_count = conn.execute(
                "SELECT COUNT(DISTINCT headline) FROM signals"
            ).fetchone()[0]
            bullish = conn.execute(
                "SELECT COUNT(*) FROM signals WHERE decider_sentiment = 'Bullish'"
            ).fetchone()[0]
            bearish = conn.execute(
                "SELECT COUNT(*) FROM signals WHERE decider_sentiment = 'Bearish'"
            ).fetchone()[0]
            neutral = conn.execute(
                "SELECT COUNT(*) FROM signals WHERE decider_sentiment = 'Neutral'"
            ).fetchone()[0]
            noise = conn.execute(
                "SELECT COUNT(*) FROM signals WHERE decider_sentiment = 'Noise'"
            ).fetchone()[0]
            escalated = conn.execute(
                "SELECT COUNT(*) FROM signals WHERE review_status = 'PENDING'"
            ).fetchone()[0]
            sent_to_gemini = conn.execute(
                "SELECT COUNT(*) FROM signals WHERE gemini_status IS NOT NULL AND gemini_status != 'skipped_by_policy' AND gemini_status != 'queued_for_review'"
            ).fetchone()[0]
            success_analyses = conn.execute(
                "SELECT COUNT(*) FROM signals WHERE gemini_status = 'success'"
            ).fetchone()[0]
            failed_analyses = conn.execute(
                "SELECT COUNT(*) FROM signals WHERE gemini_status LIKE 'error_%'"
            ).fetchone()[0]
            filtered_count = conn.execute(
                "SELECT COUNT(*) FROM signals WHERE policy_action IN ('BLOCK_NOISE', 'BLOCK_NEUTRAL')"
            ).fetchone()[0]
            total_spend = conn.execute(
                "SELECT COALESCE(SUM(estimated_cost_usd), 0.0) FROM signals"
            ).fetchone()[0]
            avg_dec = conn.execute(
                "SELECT COALESCE(AVG(decider_latency_ms), 0.0) FROM signals"
            ).fetchone()[0]
            avg_cloud = conn.execute(
                "SELECT COALESCE(AVG(cloud_latency_ms), 0.0) FROM signals WHERE gemini_status = 'success'"
            ).fetchone()[0]

            avoided_count = filtered_count + escalated
            avoided_pct = (avoided_count / total * 100.0) if total > 0 else 0.0

            return {
                "total_received": total,
                "unique_processed": unique_count,
                "bullish_count": bullish,
                "bearish_count": bearish,
                "neutral_count": neutral,
                "noise_count": noise,
                "escalated_for_review": escalated,
                "sent_to_gemini": sent_to_gemini,
                "successful_analyses": success_analyses,
                "failed_analyses": failed_analyses,
                "cloud_calls_avoided_count": avoided_count,
                "cloud_calls_avoided_pct": round(avoided_pct, 1),
                "total_cloud_spend_usd": round(total_spend, 6),
                "avg_decider_latency_ms": round(avg_dec, 1),
                "avg_cloud_latency_ms": round(avg_cloud, 1),
            }

    # -------------------------------------------------------------------------
    # Alert System SQLite Methods
    # -------------------------------------------------------------------------
    def get_alert_rules(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM alert_rules ORDER BY id ASC")
            return [dict(r) for r in cursor.fetchall()]

    def save_alert_rule(
        self,
        name: str,
        condition_type: str,
        target_value: Optional[str] = None,
        min_confidence: float = 0.80,
        enabled: bool = True,
    ) -> int:
        ts = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO alert_rules (name, condition_type, target_value, min_confidence, enabled, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, condition_type, target_value, min_confidence, 1 if enabled else 0, ts),
            )
            conn.commit()
            return cursor.lastrowid

    def toggle_alert_rule(self, rule_id: int, enabled: bool):
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE alert_rules SET enabled = ? WHERE id = ?",
                (1 if enabled else 0, rule_id),
            )
            conn.commit()

    def delete_alert_rule(self, rule_id: int):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM alert_rules WHERE id = ?", (rule_id,))
            conn.commit()

    def insert_alert(
        self,
        signal_id: int,
        rule_id: Optional[int],
        alert_type: str,
        title: str,
        message: str,
        severity: str = "warning",
    ) -> int:
        ts = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO market_alerts (signal_id, rule_id, alert_type, title, message, severity, created_at, is_read)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (signal_id, rule_id, alert_type, title, message, severity, ts),
            )
            conn.commit()
            return cursor.lastrowid

    def get_alerts(self, limit: int = 50, unread_only: bool = False) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            sql = "SELECT * FROM market_alerts"
            if unread_only:
                sql += " WHERE is_read = 0"
            sql += " ORDER BY id DESC LIMIT ?"
            cursor = conn.execute(sql, (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def mark_alert_read(self, alert_id: int):
        with self._get_connection() as conn:
            conn.execute("UPDATE market_alerts SET is_read = 1 WHERE id = ?", (alert_id,))
            conn.commit()

    def has_alert_for_signal(
        self,
        signal_id: int,
        alert_type: str,
        target_value: Optional[str] = None,
    ) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM market_alerts WHERE signal_id = ? AND alert_type = ?",
                (signal_id, alert_type),
            )
            return cursor.fetchone()[0] > 0

    # -------------------------------------------------------------------------
    # Intelligence Analytics Queries
    # -------------------------------------------------------------------------
    def get_intelligence_signals(
        self,
        limit: int = 100,
        symbol: Optional[str] = None,
        impact_level: Optional[str] = None,
        event_category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            query = "SELECT * FROM signals WHERE impact_score IS NOT NULL"
            params = []

            if impact_level:
                query += " AND impact_level = ?"
                params.append(impact_level.upper())

            if event_category:
                query += " AND event_category = ?"
                params.append(event_category)

            if search:
                query += " AND (headline LIKE ? OR publisher LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])

            if symbol:
                query += " AND affected_instruments_json LIKE ?"
                params.append(f"%{symbol}%")

            query += " ORDER BY id DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(query, tuple(params))
            return [dict(r) for r in cursor.fetchall()]

    def get_intelligence_statistics(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            total_analyzed = conn.execute(
                "SELECT COUNT(*) FROM signals WHERE impact_score IS NOT NULL"
            ).fetchone()[0]

            if total_analyzed == 0:
                return {
                    "total_analyzed": 0,
                    "avg_impact_score": 0.0,
                    "critical_count": 0,
                    "high_count": 0,
                    "medium_count": 0,
                    "low_count": 0,
                    "top_pairs": [],
                    "top_events": [],
                    "total_alerts": 0,
                    "unread_alerts": 0,
                }

            avg_score = conn.execute(
                "SELECT COALESCE(AVG(impact_score), 0.0) FROM signals WHERE impact_score IS NOT NULL"
            ).fetchone()[0]

            critical_c = conn.execute("SELECT COUNT(*) FROM signals WHERE impact_level = 'CRITICAL'").fetchone()[0]
            high_c = conn.execute("SELECT COUNT(*) FROM signals WHERE impact_level = 'HIGH'").fetchone()[0]
            medium_c = conn.execute("SELECT COUNT(*) FROM signals WHERE impact_level = 'MEDIUM'").fetchone()[0]
            low_c = conn.execute("SELECT COUNT(*) FROM signals WHERE impact_level = 'LOW'").fetchone()[0]

            total_alerts = conn.execute("SELECT COUNT(*) FROM market_alerts").fetchone()[0]
            unread_alerts = conn.execute("SELECT COUNT(*) FROM market_alerts WHERE is_read = 0").fetchone()[0]

            # Top event categories
            cursor = conn.execute(
                "SELECT event_category, COUNT(*) as cnt FROM signals WHERE event_category IS NOT NULL GROUP BY event_category ORDER BY cnt DESC LIMIT 6"
            )
            top_events = [{"category": row["event_category"], "count": row["cnt"]} for row in cursor.fetchall()]

            return {
                "total_analyzed": total_analyzed,
                "avg_impact_score": round(avg_score, 1),
                "critical_count": critical_c,
                "high_count": high_c,
                "medium_count": medium_c,
                "low_count": low_c,
                "top_events": top_events,
                "total_alerts": total_alerts,
                "unread_alerts": unread_alerts,
            }
