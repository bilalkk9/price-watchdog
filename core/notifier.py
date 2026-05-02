"""Alert notifications — console (always) and email via Gmail SMTP (FR6)."""
import logging
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD

logger = logging.getLogger(__name__)

_BORDER = "═" * 54


def _pct_arrow(drop_pct: float) -> str:
    return f"▼ {abs(drop_pct):.2f}%" if drop_pct > 0 else f"▲ {abs(drop_pct):.2f}%"


def _fmt_price(price: Optional[float], currency: str = "PKR") -> str:
    if price is None:
        return "N/A"
    return f"{currency} {price:,.0f}"


# ── Console ────────────────────────────────────────────────────────────────────

def send_console_alert(
    product_name: str,
    product_url: str,
    old_price: Optional[float],
    new_price: float,
    drop_percentage: float,
    target_price: float,
    availability: str,
    reasoning: str,
    currency: str = "PKR",
) -> None:
    """Print a formatted alert box to stdout."""
    target_line = _fmt_price(target_price, currency)
    reached = new_price <= target_price
    target_status = f"{target_line} {'✅ TARGET REACHED!' if reached else '(not yet reached)'}"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        f"╔{_BORDER}╗",
        f"║{'🐕 PRICE WATCHDOG ALERT':^54}║",
        f"╠{_BORDER}╣",
        f"║ {'Product:':<14}{product_name[:37]:<38}║",
        f"║ {'URL:':<14}{product_url[:37]:<38}║",
        f"║ {'Prev Price:':<14}{_fmt_price(old_price, currency):<38}║",
        f"║ {'Now:':<14}{_fmt_price(new_price, currency):<38}║",
        f"║ {'Drop:':<14}{_pct_arrow(drop_percentage):<38}║",
        f"║ {'Target:':<14}{target_status:<38}║",
        f"║ {'Status:':<14}{availability:<38}║",
        f"║ {'Time:':<14}{timestamp:<38}║",
        f"╠{_BORDER}╣",
        f"║ Agent Reasoning:{'':37}║",
    ]

    # Word-wrap the reasoning into 50-char lines
    words, line_buf = reasoning.split(), ""
    for word in words:
        if len(line_buf) + len(word) + 1 > 50:
            lines.append(f"║  {line_buf:<52}║")
            line_buf = word
        else:
            line_buf = f"{line_buf} {word}".strip()
    if line_buf:
        lines.append(f"║  {line_buf:<52}║")

    lines.append(f"╚{_BORDER}╝")
    print("\n".join(lines))


# ── Email ──────────────────────────────────────────────────────────────────────

_EMAIL_HTML = """\
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
<h2 style="color:#e63946">🐕 Price Watchdog Alert</h2>
<table style="border-collapse:collapse;width:100%">
  <tr><td style="padding:6px;font-weight:bold">Product</td><td style="padding:6px">{product_name}</td></tr>
  <tr style="background:#f1faee"><td style="padding:6px;font-weight:bold">URL</td>
      <td style="padding:6px"><a href="{product_url}">{product_url}</a></td></tr>
  <tr><td style="padding:6px;font-weight:bold">Previous Price</td><td style="padding:6px">{old_price}</td></tr>
  <tr style="background:#f1faee"><td style="padding:6px;font-weight:bold">Current Price</td>
      <td style="padding:6px;color:#e63946;font-weight:bold">{new_price}</td></tr>
  <tr><td style="padding:6px;font-weight:bold">Drop</td><td style="padding:6px">{drop_pct}</td></tr>
  <tr style="background:#f1faee"><td style="padding:6px;font-weight:bold">Target Price</td>
      <td style="padding:6px">{target_price} {target_status}</td></tr>
  <tr><td style="padding:6px;font-weight:bold">Availability</td><td style="padding:6px">{availability}</td></tr>
  <tr style="background:#f1faee"><td style="padding:6px;font-weight:bold">Timestamp</td>
      <td style="padding:6px">{timestamp}</td></tr>
</table>
<h3 style="margin-top:20px">Agent Reasoning</h3>
<p style="background:#f8f9fa;padding:12px;border-radius:4px">{reasoning}</p>
<hr/><p style="color:#999;font-size:12px">Price Watchdog — autonomous e-commerce price tracker</p>
</body></html>
"""


def send_email_alert(
    product_name: str,
    product_url: str,
    old_price: Optional[float],
    new_price: float,
    drop_percentage: float,
    target_price: float,
    availability: str,
    reasoning: str,
    recipient_email: str,
    currency: str = "PKR",
) -> bool:
    """Send an HTML email alert via Gmail SMTP. Returns True on success.

    Requires GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env.
    Falls back gracefully — logs error but does not raise.
    """
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        logger.warning("Email credentials not configured — skipping email alert")
        return False

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    reached = new_price <= target_price

    html_body = _EMAIL_HTML.format(
        product_name=product_name,
        product_url=product_url,
        old_price=_fmt_price(old_price, currency),
        new_price=_fmt_price(new_price, currency),
        drop_pct=_pct_arrow(drop_percentage),
        target_price=_fmt_price(target_price, currency),
        target_status="✅ TARGET REACHED!" if reached else "",
        availability=availability,
        timestamp=timestamp,
        reasoning=reasoning,
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🐕 Price Drop: {product_name} — {_pct_arrow(drop_percentage)}"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = recipient_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, recipient_email, msg.as_string())
        logger.info("email alert sent to %s", recipient_email)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error(
            "Gmail authentication failed — check GMAIL_APP_PASSWORD in .env "
            "(must be an App Password, not your account password)"
        )
    except smtplib.SMTPException as exc:
        logger.error("SMTP error sending alert: %s", exc)
    except OSError as exc:
        logger.error("Network error sending email: %s", exc)
    return False


# ── Unified entry point ────────────────────────────────────────────────────────

def notify(
    product_name: str,
    product_url: str,
    old_price: Optional[float],
    new_price: float,
    drop_percentage: float,
    target_price: float,
    availability: str,
    reasoning: str,
    recipient_email: Optional[str] = None,
    currency: str = "PKR",
) -> str:
    """Send console alert always; email alert if recipient_email is provided.

    Returns: 'console', 'email', or 'both'
    """
    send_console_alert(
        product_name, product_url, old_price, new_price,
        drop_percentage, target_price, availability, reasoning, currency,
    )
    channels = "console"

    if recipient_email:
        sent = send_email_alert(
            product_name, product_url, old_price, new_price,
            drop_percentage, target_price, availability, reasoning,
            recipient_email, currency,
        )
        if sent:
            channels = "both"

    return channels
