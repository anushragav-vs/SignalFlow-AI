"""
SignalFlow AI - SQLite History & Audit Persistence Layer
Preserves both original Strands Decider model classifications and human review actions without overwriting.
"""

import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from config import config

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
            ]
            for col_name, col_type in columns_to_ensure:
                if col_name not in existing_cols:
                    conn.execute(f"ALTER TABLE signals ADD COLUMN {col_name} {col_type}")
            conn.commit()

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
    ) -> int:
        ts = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO signals (
                    timestamp, headline, canonical_url, publisher, is_live,
                    decider_sentiment, decider_confidence, probabilities_json,
                    decider_latency_ms, decider_model_id, policy_action, policy_reason,
                    review_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ts,
                    headline,
                    canonical_url,
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
