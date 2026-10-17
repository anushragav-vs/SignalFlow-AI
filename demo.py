"""
SignalFlow AI - End-to-End Pipeline Demonstration Script
Demonstrates:
1. Strands Decider 2B local System One classification & calibrated confidence
2. Policy Gatekeeper routing (Noise/Neutral filtering, review queue escalation)
3. Google Gemini structured institutional synthesis via google-genai SDK
4. SQLite persistence, latency tracking, and exact cost calculation
"""

import sys
import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from config import config, FINANCIAL_DISCLAIMER
from src.decider_client import DeciderClient
from src.classification_service import ClassificationService, PolicyAction
from src.gemini_service import GeminiService
from src.database import SignalFlowDatabase
from src.rss_service import NormalizedArticle

# Reconfigure stdout for utf-8 if supported
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console()

DEMO_ARTICLES = [
    NormalizedArticle(
        headline="Tesla reports Q3 net income surges 17% beating Wall Street estimates as automotive margins expand to 19.8%.",
        normalized_headline="tesla reports q3 net income surges 17...",
        canonical_url="https://finance.yahoo.com/news/tsla-q3",
        publisher="Bloomberg Markets",
        description="Strong quarterly earnings beat with margin expansion across automotive operations.",
        published_at="Recent",
        dedup_hash="demo1",
        is_live=False,
    ),
    NormalizedArticle(
        headline="SEC files securities fraud charges against regional bank following whistleblower disclosure of concealed bad loans; stock drops 42%.",
        normalized_headline="sec files securities fraud charges against regional bank...",
        canonical_url="https://reuters.com/news/bank-fraud",
        publisher="Reuters Financial",
        description="Regulatory enforcement action and massive equity plunge following concealed credit impairment.",
        published_at="Recent",
        dedup_hash="demo2",
        is_live=False,
    ),
    NormalizedArticle(
        headline="Federal Reserve leaves benchmark interest rate unchanged at 5.25%-5.50% range, consistent with market expectations.",
        normalized_headline="federal reserve leaves benchmark interest rate unchanged...",
        canonical_url="https://wsj.com/news/fed-rate",
        publisher="Wall Street Journal",
        description="Monetary policy decision fully priced in by market consensus with no unexpected rate change.",
        published_at="Recent",
        dedup_hash="demo3",
        is_live=False,
    ),
    NormalizedArticle(
        headline="Celebrity chef spotted attending luxury watch gala in the Hamptons during holiday weekend.",
        normalized_headline="celebrity chef spotted attending luxury watch gala...",
        canonical_url="https://pagesix.com/hamptons-gala",
        publisher="Page Six Entertainment",
        description="Irrelevant lifestyle and celebrity gossip with zero macro or corporate financial relevance.",
        published_at="Recent",
        dedup_hash="demo4",
        is_live=False,
    ),
    NormalizedArticle(
        headline="Rumors circulate regarding potential mid-market software vendor acquisition by private equity sponsor.",
        normalized_headline="rumors circulate regarding potential midmarket software vendor acquisition...",
        canonical_url="https://dealreporter.com/pe-rumor",
        publisher="DealReporter",
        description="Unverified M&A speculation with ambiguous valuation details requiring human verification.",
        published_at="Recent",
        dedup_hash="demo5",
        is_live=False,
    ),
    NormalizedArticle(
        headline="NVIDIA secures multi-billion enterprise AI datacenter supply contracts across APAC region with deliveries commencing in Q4.",
        normalized_headline="nvidia secures multibillion enterprise ai datacenter supply contracts...",
        canonical_url="https://cnbc.com/nvidia-apac",
        publisher="CNBC Tech",
        description="Large-scale commercial revenue contracts and backlog expansion for sovereign AI infrastructure.",
        published_at="Recent",
        dedup_hash="demo6",
        is_live=False,
    ),
]


def run_pipeline_demo(model_id: str = config.gemini_model_id):
    console.print(Panel.fit(
        f"[bold cyan]SignalFlow AI - Two-Tier Pipeline Demonstration[/bold cyan]\n"
        f"[dim]System One (Local):[/] [yellow]Strands Decider 2B (Calibrated Multi-Class)[/yellow]\n"
        f"[dim]System Two (Cloud):[/] [green]Google Gemini API ({model_id})[/green]\n"
        f"[dim]Persistence:[/] [magenta]SQLite ({config.sqlite_db_path})[/magenta]\n"
        f"[dim]Hackathon Tags:[/] [cyan]{config.hackathon_tags[0]}[/] [cyan]{config.hackathon_tags[1]}[/]",
        border_style="cyan",
        box=box.ASCII,
    ))
    console.print(f"[dim italic]{FINANCIAL_DISCLAIMER}[/dim italic]\n")

    db = SignalFlowDatabase()
    decider = DeciderClient()
    classifier = ClassificationService(decider_client=decider, min_confidence=0.80)
    gemini = GeminiService(model_id=model_id)

    # Health check
    cred = gemini.check_credentials_status()
    console.print(f"[bold]Google AI Studio Status:[/] [{'green' if cred['configured'] else 'yellow'}]{cred['message']}[/{'green' if cred['configured'] else 'yellow'}]\n")

    table = Table(title="SignalFlow AI Live Execution Results", box=box.ASCII, show_lines=True)
    table.add_column("Headline", width=34)
    table.add_column("Decider 2B Sentiment", width=14, justify="center")
    table.add_column("Confidence", width=12, justify="right")
    table.add_column("Policy Action", width=16, justify="center")
    table.add_column("Gemini Status", width=15, justify="center")
    table.add_column("Cloud Latency", width=13, justify="right")
    table.add_column("Est Cost ($)", width=12, justify="right")

    total_cost = 0.0
    cloud_calls = 0
    filtered_calls = 0

    for article in DEMO_ARTICLES:
        h = article.headline

        # Step 1: Local Decider classification
        clf = classifier.classify_headline(h)
        sent = clf.decision
        conf = clf.confidence
        p_act = clf.policy_action

        # Color coding
        s_color = "green" if sent == "Bullish" else "red" if sent == "Bearish" else "magenta" if sent == "Neutral" else "dim"

        # Determine policy display
        if p_act == PolicyAction.APPROVE:
            pol_disp = "[green]APPROVED[/green]"
        elif p_act == PolicyAction.REVIEW_QUEUE:
            pol_disp = "[yellow]REVIEW QUEUE[/yellow]"
        elif p_act == PolicyAction.BLOCK_NOISE:
            pol_disp = "[dim]BLOCK (Noise)[/dim]"
        elif p_act == PolicyAction.BLOCK_NEUTRAL:
            pol_disp = "[dim]BLOCK (Neutral)[/dim]"
        else:
            pol_disp = f"[red]{p_act.value}[/red]"

        # Dispatch or Filter
        gemini_res = None
        if p_act == PolicyAction.APPROVE:
            gemini_res = gemini.analyze_headline(h, sent, conf, model_id=model_id)
            if gemini_res.status == "success":
                cloud_calls += 1
                total_cost += gemini_res.estimated_cost_usd
                gem_status = "[green]Success[/green]"
                cloud_lat = f"{gemini_res.latency_ms:.1f} ms"
                cost_str = f"${gemini_res.estimated_cost_usd:.6f}"
                rev_st = "NONE"
            else:
                gem_status = f"[red]{gemini_res.status}[/red]"
                cloud_lat = f"{gemini_res.latency_ms:.1f} ms"
                cost_str = "$0.000000"
                rev_st = "NONE"
            time.sleep(1.0)  # Rate pacing
        elif p_act == PolicyAction.REVIEW_QUEUE:
            filtered_calls += 1
            gem_status = "[yellow]Queued Review[/yellow]"
            cloud_lat = "0.0 ms"
            cost_str = "$0.000000"
            rev_st = "PENDING"
        else:
            filtered_calls += 1
            gem_status = "[dim]Filtered Locally[/dim]"
            cloud_lat = "0.0 ms"
            cost_str = "$0.000000"
            rev_st = "NONE"

        # Persist to SQLite
        sig_id = db.insert_signal(
            headline=h,
            publisher=article.publisher,
            canonical_url=article.canonical_url,
            is_live=False,
            decider_sentiment=sent,
            decider_confidence=conf,
            probabilities=clf.probabilities,
            decider_latency_ms=clf.decider_latency_ms,
            decider_model_id=clf.model_id,
            policy_action=p_act.value,
            policy_reason=clf.policy_reason,
            review_status=rev_st,
        )

        if gemini_res:
            analysis = gemini_res.analysis
            db.update_gemini_analysis(
                signal_id=sig_id,
                gemini_model_id=gemini_res.model_id,
                gemini_status=gemini_res.status,
                raw_summary=analysis.raw_summary if analysis else "",
                event_summary=analysis.event_summary if analysis else "",
                transmission_mechanism=analysis.transmission_mechanism if analysis else "",
                affected_assets=analysis.affected_assets if analysis else [],
                directional_implications=analysis.directional_implications if analysis else "",
                uncertainties=analysis.uncertainties_and_risks if analysis else [],
                reported_facts=analysis.reported_facts if analysis else [],
                analytical_hypotheses=analysis.analytical_hypotheses if analysis else [],
                cloud_latency_ms=gemini_res.latency_ms,
                input_tokens=gemini_res.input_tokens,
                output_tokens=gemini_res.output_tokens,
                total_tokens=gemini_res.total_tokens,
                estimated_cost_usd=gemini_res.estimated_cost_usd,
            )

        table.add_row(
            h[:31] + "..." if len(h) > 31 else h,
            f"[{s_color}]{sent}[/{s_color}]",
            f"{conf:.3f}",
            pol_disp,
            gem_status,
            cloud_lat,
            cost_str,
        )

    console.print(table)

    avoided_pct = (filtered_calls / len(DEMO_ARTICLES)) * 100.0
    console.print(Panel(
        f"[bold]Pipeline Execution Summary:[/bold]\n"
        f"- Total Articles Ingested: [bold]{len(DEMO_ARTICLES)}[/bold]\n"
        f"- Cloud Invocations Dispatched: [cyan]{cloud_calls}[/cyan]\n"
        f"- Local Policy Filtered / Queued: [green]{filtered_calls}[/green] ([bold green]{avoided_pct:.1f}% Local Savings Rate[/bold green])\n"
        f"- Cumulative Cloud Spend: [yellow]${total_cost:.6f}[/yellow]\n"
        f"- SQLite Audit Trail: [cyan]{config.sqlite_db_path}[/cyan]",
        title="[bold green]SignalFlow AI - Execution Performance[/bold green]",
        border_style="green",
        box=box.ASCII,
    ))


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else config.gemini_model_id
    run_pipeline_demo(model_id=target)
