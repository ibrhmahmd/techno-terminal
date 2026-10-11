from typing import Optional
from app.modules.competitions.schemas.team_schemas import (
    CategorySubcategoryDTO,
    TeamsWithMembersBatch,
    TeamMemberWithNameDTO,
    StudentMembershipEnrichedDTO,
    TeamDTO,
    TeamMemberDTO,
)
from app.modules.competitions.schemas.competition_schemas import CompetitionDTO
from sqlmodel import Session, select
from app.shared.datetime_utils import utc_now
from app.modules.competitions.models.competition_models import Competition
from app.modules.crm.models.student_models import Student
from app.modules.competitions.models.team_models import (
    Team,
    TeamMember,
)

ALLOWED_TEAM_UPDATES = {
    "team_name", "category", "subcategory", "project_name",
    "project_description", "group_id", "coach_id", "notes",
    "placement_rank", "placement_label",
}


# ── Teams ─────────────────────────────────────────────────────────────────────


class TeamRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_team(
        self, competition_id: int,
        team_name: str,
        category: str,
        subcategory: Optional[str] = None,
        coach_id: Optional[int] = None,
        group_id: Optional[int] = None,
        notes: Optional[str] = None,
        project_name: Optional[str] = None,
        project_description: Optional[str] = None,
    ) -> Team:
        """Create a team in the new 3-table schema."""
        t = Team(
            competition_id=competition_id,
            team_name=team_name,
            category=category,
            subcategory=subcategory,
            group_id=group_id,
            coach_id=coach_id,
            notes=notes,
            project_name=project_name,
            project_description=project_description,
            created_at=utc_now(),
        )
        self._session.add(t)
        self._session.flush()
        return t


    def list_teams(
        self, competition_id: int,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
    ) -> list[Team]:
        """List teams for a competition with optional category/subcategory filters."""
        stmt = select(Team).where(Team.competition_id == competition_id)
        if category:
            stmt = stmt.where(Team.category == category)
        if subcategory:
            stmt = stmt.where(Team.subcategory == subcategory)
        return list(self._session.exec(stmt).all())


    def get_team(self, team_id: int) -> Team | None:
        """Get a team by ID."""
        return self._session.get(Team, team_id)


    def update_team(self, team_id: int, **kwargs) -> Team | None:
        t = self._session.get(Team, team_id)
        if t:
            for k, v in kwargs.items():
                if k in ALLOWED_TEAM_UPDATES:
                    setattr(t, k, v)
            self._session.add(t)
            self._session.flush()
        return t


    def delete_team(self, team_id: int) -> bool:
        """Hard delete a team."""
        t = self._session.get(Team, team_id)
        if t:
            self._session.delete(t)
            self._session.flush()
            return True
        return False


    def get_distinct_categories(self, competition_id: int) -> list[CategorySubcategoryDTO]:
        """Returns list of (category, subcategory) tuples for autocomplete."""
        stmt = (
            select(Team.category, Team.subcategory)
            .where(Team.competition_id == competition_id)
            .distinct()
            .order_by(Team.category, Team.subcategory)
        )
        rows = list(self._session.exec(stmt).all())
        return [CategorySubcategoryDTO(category=r.category, subcategory=r.subcategory) for r in rows]


    def check_student_in_competition(self, competition_id: int, student_id: int) -> bool:
        """Check if student is already in any team for this competition."""
        stmt = (
            select(TeamMember)
            .join(Team)
            .where(Team.competition_id == competition_id)
            .where(TeamMember.student_id == student_id)
        )
        return self._session.exec(stmt).first() is not None


    def check_category_has_subcategories(self, competition_id: int, category: str) -> bool:
        """Check if any team in this category has a subcategory."""
        stmt = (
            select(Team)
            .where(Team.competition_id == competition_id)
            .where(Team.category == category)
            .where(Team.subcategory.is_not(None))
        )
        return self._session.exec(stmt).first() is not None


    # ── Team Members ──────────────────────────────────────────────────────────────

    def add_team_member(self, team_id: int, student_id: int, amount_due: float = 0.0) -> TeamMember:
        m = TeamMember(team_id=team_id, student_id=student_id, amount_due=amount_due, amount_paid=0.0)
        self._session.add(m)
        self._session.flush()
        return m


    def get_team_member(self, team_id: int, student_id: int) -> TeamMember | None:
        stmt = select(TeamMember).where(
            TeamMember.team_id == team_id, TeamMember.student_id == student_id
        )
        return self._session.exec(stmt).first()


    def get_team_member_by_id(self, member_id: int) -> TeamMember | None:
        """Get a team member by their unique member ID."""
        return self._session.get(TeamMember, member_id)


    def list_team_members(self, team_id: int) -> list[TeamMember]:
        stmt = select(TeamMember).where(TeamMember.team_id == team_id)
        return list(self._session.exec(stmt).all())


    def record_payment(
        self, team_member_id: int, amount: float
    ) -> TeamMember | None:
        """Increment amount_paid for a team member."""
        m = self._session.get(TeamMember, team_member_id)
        if m:
            m.amount_paid = float(m.amount_paid) + amount
            self._session.add(m)
            self._session.flush()
        return m


    def remove_team_member(self, team_id: int, student_id: int) -> bool:
        m = self.get_team_member(team_id, student_id)
        if m:
            self._session.delete(m)
            self._session.flush()
            return True
        return False


    # ── Batch Loading (N+1 Elimination) ──────────────────────────────────────────

    def list_team_members_with_students(
        self, team_ids: list[int]
    ) -> dict[int, list[TeamMemberWithNameDTO]]:
        """
        Batch-load team members with student names for multiple teams in a single query.
        Returns dict mapping team_id -> list of TeamMemberWithNameDTO.
        """
        if not team_ids:
            return {}

        stmt = (
            select(TeamMember, Student.full_name)
            .join(Student, TeamMember.student_id == Student.id, isouter=True)
            .where(TeamMember.team_id.in_(team_ids))
        )
        rows = list(self._session.exec(stmt).all())

        result: dict[int, list[TeamMemberWithNameDTO]] = {}
        for member, student_name in rows:
            result.setdefault(member.team_id, []).append(
                TeamMemberWithNameDTO(
                    member=TeamMemberDTO.model_validate(member),
                    student_name=student_name or f"Student #{member.student_id}"
                )
            )
        return result


    def list_teams_with_members_batch(
        self, competition_id: int
    ) -> TeamsWithMembersBatch:
        """
        Batch-load all teams for a competition with their members and student names.
        Returns the teams plus a mapping team_id -> list of TeamMemberWithNameDTO.
        """
        teams = self.list_teams(competition_id)
        if not teams:
            return TeamsWithMembersBatch(teams=[], members_by_team={})

        team_ids = [t.id for t in teams]
        members_by_team = self.list_team_members_with_students(team_ids)
        return TeamsWithMembersBatch(teams=teams, members_by_team=members_by_team)


    def list_student_memberships_enriched(
        self, student_id: int
    ) -> list[StudentMembershipEnrichedDTO]:
        """
        Batch-load all memberships for a student with team and competition data.
        Returns list of StudentMembershipEnrichedDTO.
        """
        stmt = (
            select(TeamMember, Team, Competition)
            .join(Team, TeamMember.team_id == Team.id)
            .join(Competition, Team.competition_id == Competition.id, isouter=True)
            .where(TeamMember.student_id == student_id)
        )
        rows = list(self._session.exec(stmt).all())
        return [
            StudentMembershipEnrichedDTO(
                membership=TeamMemberDTO.model_validate(m),
                team=TeamDTO.model_validate(t),
                competition=CompetitionDTO.model_validate(c) if c else None,
            )
            for m, t, c in rows
        ]
