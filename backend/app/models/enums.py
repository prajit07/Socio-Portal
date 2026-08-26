import enum


class RoleEnum(str, enum.Enum):
    """Roles from plan.txt §2 — Actors, Roles & Permissions."""

    CITIZEN = "citizen"
    UNIVERSITY_ADMIN = "university_admin"
    STUDENT = "student"
    FACULTY = "faculty"
    INDUSTRY = "industry"
    GOVERNMENT = "government"
    ADMIN = "admin"


class ProblemStatusEnum(str, enum.Enum):
    """Problem lifecycle status."""

    SUBMITTED = "submitted"
    VALIDATED = "validated"
    CATEGORIZED = "categorized"
    MATCHED = "matched"
    IN_PROGRESS = "in_progress"
    SOLUTION_PROPOSED = "solution_proposed"
    PROTOTYPE = "prototype"
    PILOT_TEST = "pilot_test"
    IMPLEMENTED = "implemented"
    CLOSED = "closed"
    REJECTED = "rejected"


class ProblemPriorityEnum(str, enum.Enum):
    """Problem priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SolutionStatusEnum(str, enum.Enum):
    """Solution lifecycle status."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PROTOTYPE = "prototype"
    PILOT = "pilot"
    IMPLEMENTED = "implemented"