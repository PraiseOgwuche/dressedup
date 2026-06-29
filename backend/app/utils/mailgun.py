import hashlib
import hmac
import logging
import re
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

_INGEST_ADDRESS_RE = re.compile(r"u-([a-f0-9]{16})@", re.IGNORECASE)


@dataclass
class MailgunAttachment:
    filename: str
    content_type: str
    data: bytes


@dataclass
class InboundEmail:
    recipient: str
    sender: str
    subject: str
    attachments: list[MailgunAttachment]


def extract_ingest_token(recipient_field: str) -> Optional[str]:
    """Pull the user's ingest token from a Mailgun `recipient` field."""
    for address in recipient_field.replace(" ", "").split(","):
        match = _INGEST_ADDRESS_RE.search(address.lower())
        if match:
            return match.group(1).lower()
    return None


def verify_mailgun_signature(
    signing_key: str,
    timestamp: str,
    token: str,
    signature: str,
) -> bool:
    if not signing_key:
        return False
    digest = hmac.new(
        key=signing_key.encode("utf-8"),
        msg=f"{timestamp}{token}".encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(digest, signature)


def parse_mailgun_form(form) -> InboundEmail:
    """Parse Mailgun inbound `multipart/form-data` into a structured email."""
    recipient = str(form.get("recipient") or "")
    sender = str(form.get("sender") or form.get("from") or "")
    subject = str(form.get("subject") or "")
    attachments: list[MailgunAttachment] = []

    try:
        count = int(form.get("attachment-count") or 0)
    except (TypeError, ValueError):
        count = 0

    for index in range(1, count + 1):
        upload = form.get(f"attachment-{index}")
        if upload is None:
            continue
        filename = getattr(upload, "filename", None) or f"attachment-{index}"
        content_type = getattr(upload, "content_type", None) or "application/octet-stream"
        data = upload.file.read() if hasattr(upload, "file") else b""
        attachments.append(MailgunAttachment(filename=filename, content_type=content_type, data=data))

    # Some Mailgun routes also expose numbered files without attachment-count.
    if not attachments:
        index = 1
        while True:
            upload = form.get(f"attachment-{index}")
            if upload is None:
                break
            filename = getattr(upload, "filename", None) or f"attachment-{index}"
            content_type = getattr(upload, "content_type", None) or "application/octet-stream"
            data = upload.file.read() if hasattr(upload, "file") else b""
            attachments.append(MailgunAttachment(filename=filename, content_type=content_type, data=data))
            index += 1

    return InboundEmail(recipient=recipient, sender=sender, subject=subject, attachments=attachments)
