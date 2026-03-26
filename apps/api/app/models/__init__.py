"""ייבוא כל המודלים כדי ש-Alembic יוכל לגלות אותם אוטומטית."""

from .taxonomy import Skill, Topic, Role, Industry, Country, Region, Language, SkillAlias, TopicAlias
from .pipeline import SourceRun, RawSourceRecord, NormalizedRecord, PipelineRun
from .learning import InternalLearningAsset
from .signals import SignalSnapshot
from .opportunities import OpportunityBrief, OpportunityEvidenceItem, ReviewDecision

__all__ = [
    # טקסונומיה
    "Skill",
    "SkillAlias",
    "Topic",
    "TopicAlias",
    "Role",
    "Industry",
    "Country",
    "Region",
    "Language",
    # פייפליין
    "SourceRun",
    "RawSourceRecord",
    "NormalizedRecord",
    "PipelineRun",
    # נכסי למידה
    "InternalLearningAsset",
    # אותות
    "SignalSnapshot",
    # הזדמנויות
    "OpportunityBrief",
    "OpportunityEvidenceItem",
    "ReviewDecision",
]
