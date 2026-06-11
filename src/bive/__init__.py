"""Behavioral Integrity Verification Engine."""

from .models import EvidenceEvent, Hypothesis, VerificationReport
from .report import build_report_from_transcript

__all__ = ["EvidenceEvent", "Hypothesis", "VerificationReport", "build_report_from_transcript"]
__version__ = "0.4.0"
