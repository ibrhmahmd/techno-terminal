from datetime import date, datetime
from typing import Optional
from app.db.connection import get_session
from app.modules.competitions.models import (
    Competition,
    CompetitionCategory,
    Team,
    TeamMember,
)
from app.modules.competitions import repository as repo


# ── Competitions ──────────────────────────────────────────────────────────────


def create_competition(
    name: str,
    edition: Optional[str] = None,
    competition_date: Optional[date] = None,
    location: Optional[str] = None,
    notes: Optional[str] = None,
) -> Competition:
    """Validates inputs and creates a new competition."""
    if not name.strip():
        raise ValueError("Competition name is required.")
    with get_session() as db:
        return repo.create_competition(
            db, name, edition, competition_date, location, notes
        )


def list_competitions() -> list[Competition]:
    with get_session() as db:
        return repo.list_competitions(db)


def add_category(
    competition_id: int,
    category_name: str,
    notes: Optional[str] = None,
) -> CompetitionCategory:
    if not category_name.strip():
        raise ValueError("Category name is required.")
    with get_session() as db:
        comp = repo.get_competition(db, competition_id)
        if not comp:
            raise ValueError(f"Competition {competition_id} not found.")
        return repo.add_category(db, competition_id, category_name, notes)


def list_categories(competition_id: int) -> list[CompetitionCategory]:
    with get_session() as db:
        return repo.list_categories(db, competition_id)


# ── Teams ─────────────────────────────────────────────────────────────────────


def register_team(
    category_id: int,
    team_name: str,
    student_ids: list[int],
    coach_id: Optional[int] = None,
    group_id: Optional[int] = None,
    fee_per_student: Optional[float] = None,
) -> dict:
    """
    Creates a team and adds all listed students as members.
    Validates that all students are active before inserting anything.
    Returns {'team': Team, 'members_added': int}.
    """
    from app.modules.crm.models import Student

    if not team_name.strip():
        raise ValueError("Team name is required.")
    if not student_ids:
        raise ValueError("At least one student is required.")

    with get_session() as db:
        # Validate category exists
        cat = repo.get_category(db, category_id)
        if not cat:
            raise ValueError(f"Category {category_id} not found.")

        # Validate all students are active
        for sid in student_ids:
            s = db.get(Student, sid)
            if not s:
                raise ValueError(f"Student {sid} not found.")
            if not s.is_active:
                raise ValueError(f"Student '{s.full_name}' is not active.")

        # Create team
        team = repo.create_team(
            db, category_id, team_name, coach_id, group_id, fee_per_student
        )

        # Add members
        members_added = 0
        for sid in student_ids:
            # Skip duplicates gracefully
            existing = repo.get_team_member(db, team.id, sid)
            if not existing:
                repo.add_team_member(db, team.id, sid)
                members_added += 1

        return {"team": team, "members_added": members_added}


def list_teams(category_id: int) -> list[Team]:
    with get_session() as db:
        return repo.list_teams(db, category_id)


def list_team_members(team_id: int) -> list[dict]:
    """Returns team members enriched with student name and fee status."""
    from app.modules.crm.models import Student

    with get_session() as db:
        members = repo.list_team_members(db, team_id)
        result = []
        for m in members:
            s = db.get(Student, m.student_id)
            result.append(
                {
                    "team_member_id": m.id,
                    "student_id": m.student_id,
                    "student_name": s.full_name if s else f"Student #{m.student_id}",
                    "fee_paid": m.fee_paid,
                    "payment_id": m.payment_id,
                }
            )
        return result


def pay_competition_fee(
    team_id: int,
    student_id: int,
    guardian_id: Optional[int],
    received_by_user_id: Optional[int],
) -> dict:
    """
    Pays the competition fee for one student in a team.
    Creates a Finance receipt with payment_type='competition',
    then marks team_members.fee_paid = True.
    Returns {'receipt_number': str, 'payment_id': int}.
    """
    from app.modules.finance import service as fin_srv

    with get_session() as db:
        team = repo.get_team(db, team_id)
        if not team:
            raise ValueError(f"Team {team_id} not found.")

        member = repo.get_team_member(db, team_id, student_id)
        if not member:
            raise ValueError(f"Student {student_id} is not a member of team {team_id}.")
        if member.fee_paid:
            raise ValueError("Fee is already paid for this student.")

        fee = team.enrollment_fee_per_student or 0.0
        if fee <= 0:
            raise ValueError(
                "Team has no fee set. Set 'enrollment_fee_per_student' on the team first."
            )

    # Create receipt and payment line via Finance service
    receipt = fin_srv.open_receipt(
        guardian_id=guardian_id,
        method="cash",
        received_by_user_id=received_by_user_id,
        notes=f"Competition fee — Team #{team_id}",
    )

    payment = fin_srv.add_charge_line(
        receipt_id=receipt.id,
        student_id=student_id,
        enrollment_id=None,  # Not tied to a course enrollment
        amount=fee,
        payment_type="competition",
    )

    # Mark the fee as paid
    with get_session() as db:
        repo.mark_fee_paid(db, team_id, student_id, payment.id)

    return {
        "receipt_number": receipt.receipt_number,
        "payment_id": payment.id,
        "amount": fee,
    }


def get_competition_summary(competition_id: int) -> dict:
    """Returns competition + all categories + teams + member fee status."""
    with get_session() as db:
        comp = repo.get_competition(db, competition_id)
        if not comp:
            return {}
        categories = repo.list_categories(db, competition_id)
        result = {
            "competition": comp,
            "categories": [],
        }
        for cat in categories:
            teams = repo.list_teams(db, cat.id)
            cat_entry = {
                "category": cat,
                "teams": [],
            }
            for team in teams:
                members = repo.list_team_members(db, team.id)
                cat_entry["teams"].append({"team": team, "members": members})
            result["categories"].append(cat_entry)
        return result
