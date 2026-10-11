"""Analytics repositories (classes built from a session)."""
from .academic_repository import AcademicRepository
from .bi_repository import BiRepository
from .competition_repository import CompetitionRepository
from .dashboard_repository import DashboardRepository
from .financial_repository import FinancialRepository

__all__ = [
    "AcademicRepository",
    "BiRepository",
    "CompetitionRepository",
    "DashboardRepository",
    "FinancialRepository",
]
