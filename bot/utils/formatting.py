from bot.models.provider import Provider
from bot.models.resource import Resource


class Formatter:

    @staticmethod
    def provider_card(p: Provider) -> str:
        ptype = "Storage" if p.provider_type == "storage" else "Compute"
        unit = "GB/mo" if p.provider_type == "storage" else "vCPU-hr"
        avail = p.available_capacity
        total = p.total_capacity
        pct_used = (p.used_capacity / total * 100) if total else 0
        stars = int(round(p.rating))
        star_str = ("*" * stars) + ("-" * (5 - stars))

        return (
            f"{'=' * 34}\n"
            f"  {p.name}\n"
            f"{'=' * 34}\n"
            f"  Type      : {ptype}\n"
            f"  Region    : {p.region}\n"
            f"  Price     : {p.price_per_unit} 0G/{unit}\n"
            f"  Capacity  : {avail:,.0f} / {total:,.0f} ({100 - pct_used:.1f}% free)\n"
            f"  Uptime    : {p.uptime_pct}%\n"
            f"  Rating    : [{star_str}] {p.rating}/5.0\n"
            f"  ID        : #{p.id}\n"
        )

    @staticmethod
    def provider_comparison_table(providers: list[Provider]) -> str:
        if not providers:
            return "No providers to compare."
        ptype = providers[0].provider_type
        unit = "GB/mo" if ptype == "storage" else "vCPU-hr"
        header = f"{'Name':<22} {'Price':>8} {'Avail':>8} {'Uptime':>7} {'Rating':>6}\n"
        sep = "-" * 55 + "\n"
        rows = ""
        for p in sorted(providers, key=lambda x: x.price_per_unit):
            avail = p.available_capacity
            name = p.name[:20]
            rows += (
                f"{name:<22} {p.price_per_unit:>7.3f}  "
                f"{avail:>7.0f}  {p.uptime_pct:>6.2f}% {p.rating:>5.1f}\n"
            )
        title = f"  Provider Comparison ({unit})\n"
        return f"<pre>{title}{sep}{header}{sep}{rows}{sep}</pre>"

    @staticmethod
    def resource_card(r: Resource, provider_name: str = "") -> str:
        rtype = "Storage" if r.resource_type == "storage" else "Compute"
        unit = "GB" if r.resource_type == "storage" else "vCPU-hrs"
        status_icon = {
            "active": "[ACTIVE]",
            "expired": "[EXPIRED]",
            "cancelled": "[CANCELLED]",
        }.get(r.status, f"[{r.status.upper()}]")

        lines = [
            f"--- Resource #{r.id} {status_icon} ---",
            f"  Type     : {rtype}",
            f"  Amount   : {r.amount} {unit}",
            f"  Paid     : {r.price_paid} 0G",
        ]
        if provider_name:
            lines.append(f"  Provider : {provider_name}")
        if r.expires_at:
            lines.append(f"  Expires  : {r.expires_at}")
        if r.tx_hash:
            lines.append(f"  Tx       : {r.tx_hash[:16]}...")
        return "\n".join(lines)

    @staticmethod
    def file_card(f: dict) -> str:
        size_kb = f.get("file_size", 0) / 1024
        status = f.get("status", "unknown").upper()
        return (
            f"--- File #{f.get('id')} [{status}] ---\n"
            f"  Name    : {f.get('filename', 'unknown')}\n"
            f"  Size    : {size_kb:,.1f} KB\n"
            f"  Root    : {(f.get('merkle_root') or 'N/A')[:20]}...\n"
            f"  Uploaded: {f.get('created_at', 'N/A')}\n"
        )

    @staticmethod
    def earnings_summary(summary: dict, recent: list[dict]) -> str:
        lines = [
            "=== Earnings Summary ===",
            f"  Total earned   : {summary.get('total', 0):.4f} 0G",
            f"  Last 30 days   : {summary.get('last_30d', 0):.4f} 0G",
            f"  Transactions   : {summary.get('count', 0)}",
            "",
        ]
        if recent:
            lines.append("--- Recent Earnings ---")
            for e in recent[:10]:
                lines.append(
                    f"  +{e['amount']:.4f} 0G  |  {e['source']}  |  {e['created_at']}"
                )
        return "\n".join(lines)

    @staticmethod
    def job_card(j: dict) -> str:
        status_map = {
            "pending": "[PENDING]",
            "running": "[RUNNING]",
            "completed": "[DONE]",
            "failed": "[FAILED]",
        }
        st = status_map.get(j.get("status", ""), f"[{j.get('status', '?').upper()}]")
        lines = [
            f"--- Job #{j.get('id')} {st} ---",
            f"  Type     : {j.get('job_type', 'N/A')}",
            f"  Provider : {j.get('provider_name', 'N/A')}",
            f"  Created  : {j.get('created_at', 'N/A')}",
        ]
        if j.get("completed_at"):
            lines.append(f"  Finished : {j['completed_at']}")
        if j.get("result"):
            lines.append(f"  Result   : {j['result'][:100]}")
        return "\n".join(lines)
