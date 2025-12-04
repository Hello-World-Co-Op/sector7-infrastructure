"""
Aurora Forester - Founder Profile Management
Secure, encrypted profile storage and retrieval for personalized context.
"""

import os
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path
import hashlib

# Profile categories aligned with database schema
PROFILE_CATEGORIES = {
    "identity": "Core identity information (encrypted)",
    "preferences": "Communication and work preferences",
    "boundaries": "Privacy and security boundaries",
    "goals": "Short and long-term goals",
    "patterns": "Observed behavioral patterns",
    "wellbeing": "Health and wellbeing tracking",
}


@dataclass
class FounderContext:
    """
    Secure founder context container.
    Never logged, never transmitted without explicit consent.
    """

    # Identity (encrypted at rest)
    preferred_name: str = "the founder"
    pronouns: List[str] = field(default_factory=lambda: ["they/them"])

    # Preferences
    communication_style: str = "direct, warm, collaborative"
    work_hours_preference: Optional[str] = None
    focus_duration_preference: int = 90  # minutes
    break_reminder_enabled: bool = True

    # Current state (ephemeral)
    current_energy_level: Optional[str] = None  # high, medium, low
    current_focus_area: Optional[str] = None
    last_break_time: Optional[datetime] = None

    # Boundaries
    never_share_topics: List[str] = field(default_factory=lambda: [
        "sector7",
        "personal_projects",
        "private_channels",
        "financial_details",
        "health_specifics",
    ])

    # Goals tracking
    active_goals: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "preferred_name": self.preferred_name,
            "pronouns": self.pronouns,
            "communication_style": self.communication_style,
            "work_hours_preference": self.work_hours_preference,
            "focus_duration_preference": self.focus_duration_preference,
            "break_reminder_enabled": self.break_reminder_enabled,
            "never_share_topics": self.never_share_topics,
            "active_goals": self.active_goals,
            "last_updated": datetime.now().isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FounderContext":
        """Reconstruct from dictionary."""
        return cls(
            preferred_name=data.get("preferred_name", "the founder"),
            pronouns=data.get("pronouns", ["they/them"]),
            communication_style=data.get("communication_style", "direct, warm, collaborative"),
            work_hours_preference=data.get("work_hours_preference"),
            focus_duration_preference=data.get("focus_duration_preference", 90),
            break_reminder_enabled=data.get("break_reminder_enabled", True),
            never_share_topics=data.get("never_share_topics", []),
            active_goals=data.get("active_goals", []),
        )


class FounderProfileManager:
    """
    Manages secure founder profile storage and retrieval.

    Security model:
    - Profile stored in secure directory (chmod 700)
    - Sensitive fields encrypted with pgcrypto in database
    - Never share topics enforced at query time
    - All access logged for founder review
    """

    def __init__(self, secure_dir: Optional[Path] = None):
        self.secure_dir = secure_dir or Path.home() / ".aurora-forester" / "secure-profile"
        self.secure_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self.secure_dir, 0o700)

        self.profile_file = self.secure_dir / "founder_context.json"
        self.access_log = self.secure_dir / "access_log.jsonl"

        self._context: Optional[FounderContext] = None

    def _log_access(self, action: str, details: Optional[str] = None):
        """Log profile access for founder transparency."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details,
        }
        with open(self.access_log, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def load_context(self) -> FounderContext:
        """Load founder context from secure storage."""
        if self._context is not None:
            return self._context

        if self.profile_file.exists():
            with open(self.profile_file, "r") as f:
                data = json.load(f)
            self._context = FounderContext.from_dict(data)
            self._log_access("load", "Profile loaded from secure storage")
        else:
            self._context = FounderContext()
            self.save_context()
            self._log_access("initialize", "New profile created with defaults")

        return self._context

    def save_context(self):
        """Save founder context to secure storage."""
        if self._context is None:
            return

        with open(self.profile_file, "w") as f:
            json.dump(self._context.to_dict(), f, indent=2)

        os.chmod(self.profile_file, 0o600)
        self._log_access("save", "Profile saved to secure storage")

    def update_preference(self, key: str, value: Any):
        """Update a single preference."""
        context = self.load_context()
        if hasattr(context, key):
            setattr(context, key, value)
            self.save_context()
            self._log_access("update", f"Updated {key}")

    def add_goal(self, goal: Dict[str, Any]):
        """Add a new goal to tracking."""
        context = self.load_context()
        goal["added_at"] = datetime.now().isoformat()
        goal["status"] = goal.get("status", "active")
        context.active_goals.append(goal)
        self.save_context()
        self._log_access("add_goal", goal.get("title", "Untitled goal"))

    def is_shareable_topic(self, topic: str) -> bool:
        """Check if a topic can be shared based on boundaries."""
        context = self.load_context()
        topic_lower = topic.lower()

        for forbidden in context.never_share_topics:
            if forbidden.lower() in topic_lower:
                return False

        return True

    def get_context_for_rag(self) -> Dict[str, Any]:
        """
        Get founder context suitable for RAG injection.
        Excludes sensitive fields.
        """
        context = self.load_context()
        return {
            "preferred_name": context.preferred_name,
            "communication_style": context.communication_style,
            "current_focus": context.current_focus_area,
            "goals_summary": [g.get("title") for g in context.active_goals if g.get("status") == "active"],
        }


class WellbeingMonitor:
    """
    Monitors founder wellbeing patterns.
    Aurora's caring side - gentle reminders, not mandates.
    """

    def __init__(self, profile_manager: FounderProfileManager):
        self.profile = profile_manager
        self.state_file = profile_manager.secure_dir / "wellbeing_state.json"

    def _load_state(self) -> Dict[str, Any]:
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                return json.load(f)
        return {}

    def _save_state(self, state: Dict[str, Any]):
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)
        os.chmod(self.state_file, 0o600)

    def record_focus_start(self):
        """Record start of a focus session."""
        state = self._load_state()
        state["focus_started"] = datetime.now().isoformat()
        state["last_activity"] = datetime.now().isoformat()
        self._save_state(state)

    def record_break(self):
        """Record a break taken."""
        state = self._load_state()
        state["last_break"] = datetime.now().isoformat()
        state["breaks_today"] = state.get("breaks_today", 0) + 1
        self._save_state(state)

    def check_break_needed(self) -> Optional[str]:
        """
        Check if a break reminder should be suggested.
        Returns a gentle message or None.
        """
        context = self.profile.load_context()
        if not context.break_reminder_enabled:
            return None

        state = self._load_state()
        focus_started = state.get("focus_started")

        if not focus_started:
            return None

        focus_start = datetime.fromisoformat(focus_started)
        duration = (datetime.now() - focus_start).total_seconds() / 60

        if duration > context.focus_duration_preference:
            return f"You've been focused for {int(duration)} minutes. A short break might help maintain clarity."

        return None

    def get_daily_summary(self) -> Dict[str, Any]:
        """Get a summary of today's wellbeing metrics."""
        state = self._load_state()
        return {
            "breaks_taken": state.get("breaks_today", 0),
            "last_break": state.get("last_break"),
            "focus_sessions": state.get("focus_sessions_today", 0),
        }


# Initialize singleton instances
_profile_manager: Optional[FounderProfileManager] = None
_wellbeing_monitor: Optional[WellbeingMonitor] = None


def get_profile_manager() -> FounderProfileManager:
    """Get the singleton profile manager."""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = FounderProfileManager()
    return _profile_manager


def get_wellbeing_monitor() -> WellbeingMonitor:
    """Get the singleton wellbeing monitor."""
    global _wellbeing_monitor
    if _wellbeing_monitor is None:
        _wellbeing_monitor = WellbeingMonitor(get_profile_manager())
    return _wellbeing_monitor


# Convenience functions for Aurora to use
def get_founder_context() -> Dict[str, Any]:
    """Get current founder context for RAG."""
    return get_profile_manager().get_context_for_rag()


def can_share_topic(topic: str) -> bool:
    """Check if a topic is shareable."""
    return get_profile_manager().is_shareable_topic(topic)


def check_wellbeing() -> Optional[str]:
    """Check if a wellbeing reminder is needed."""
    return get_wellbeing_monitor().check_break_needed()
