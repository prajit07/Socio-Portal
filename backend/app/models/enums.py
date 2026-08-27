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
    """Problem lifecycle status — plan.txt §7 (ER DIAGRAM)."""

    PENDING_VALIDATION = "pending_validation"
    VALIDATED = "validated"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    OPEN = "open"
    IN_REVIEW = "in_review"
    PROPOSAL_SUBMITTED = "proposal_submitted"
    IN_COLLABORATION = "in_collaboration"
    PROTOTYPE = "prototype"
    PILOT = "pilot"
    IMPLEMENTED = "implemented"
    CLOSED = "closed"


class ProblemPriorityEnum(str, enum.Enum):
    """AI-generated priority level (1-10 mapped to buckets)."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceTypeEnum(str, enum.Enum):
    """Evidence media type — plan.txt §7 EVIDENCE.type."""

    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    TEXT = "text"


class SolutionStatusEnum(str, enum.Enum):
    """Proposal status — plan.txt §7 PROPOSALS.status."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class RoutingTypeEnum(str, enum.Enum):
    """Routing target type — plan.txt §7 ROUTING_LOG.routed_to_type."""

    UNIVERSITY = "university"
    INDUSTRY = "industry"


class NotificationTypeEnum(str, enum.Enum):
    PROBLEM_ROUTED = "problem_routed"
    PROPOSAL_RECEIVED = "proposal_received"
    STATUS_UPDATED = "status_updated"
    DUPLICATE_FLAGGED = "duplicate_flagged"
    GENERIC = "generic"
