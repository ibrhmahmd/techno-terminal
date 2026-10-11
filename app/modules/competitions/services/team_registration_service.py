from typing import Optional
from sqlmodel import select
from app.db.uow import UnitOfWork
from app.shared.exceptions import NotFoundError, BusinessRuleError, ConflictError
from app.modules.competitions.schemas.team_schemas import (
    RegisterTeamInput,
    TeamDTO,
    TeamRegistrationResultDTO,
    TeamRegistrationResultWithWarningDTO,
)
from app.modules.crm import StudentActivityService, LogCompetitionRegistrationDTO
from app.modules.academics.models.group_models import Group
from app.modules.crm.models.student_models import Student
from app.modules.enrollments.models import Enrollment
from app.modules.competitions.services.team_base import TeamServiceBase

import logging
logger = logging.getLogger(__name__)


class TeamRegistrationService(TeamServiceBase):
    """Team registration use case."""

    def register_team(
        self, cmd: RegisterTeamInput, current_user_id: Optional[int] = None,
    ) -> TeamRegistrationResultWithWarningDTO:
        """
        Creates a team and adds all listed students as members.
        3-table schema: uses competition_id, category, subcategory directly.
        Business rules:
        - At least one student source required: group_id OR student_ids
        - If group_id provided, pre-fills students from group's current level roster
        - One student can only be in one team per competition
        - If category has subcategories, must specify subcategory
        """
        db = self._uow.session
        # Validate competition exists
        comp = self._comps.get_competition(cmd.competition_id)
        if not comp:
            raise NotFoundError(f"Competition {cmd.competition_id} not found.")

        # Resolve student IDs: group pre-fill + manual list
        student_ids = self._resolve_student_ids(db, cmd)

        # Business rule: If category has subcategories, must specify subcategory
        if cmd.subcategory is None:
            has_subs = self._teams.check_category_has_subcategories(cmd.competition_id, cmd.category
            )
            if has_subs:
                raise BusinessRuleError(
                    f"Category '{cmd.category}' has subcategories. "
                    "Must specify a subcategory."
                )

        # Validate team name uniqueness in this competition
        existing_teams = self._teams.list_teams(cmd.competition_id, cmd.category, cmd.subcategory)
        if any(t.team_name.lower() == cmd.team_name.lower() for t in existing_teams):
            raise ConflictError(
                f"A team named '{cmd.team_name}' already exists in this category."
            )

        # Validate all students are active and collect duplicate warnings
        duplicate_warnings = []
        for sid in student_ids:
            s = db.get(Student, sid)
            if not s:
                raise NotFoundError(f"Student {sid} not found.")
            if s.status != "active":
                raise BusinessRuleError(f"Student '{s.full_name}' is not active.")

            # Business rule: Warn if student already in another team for this competition
            already_enrolled = self._teams.check_student_in_competition(cmd.competition_id, sid
            )
            if already_enrolled:
                duplicate_warnings.append(
                    f"Student '{s.full_name}' is already enrolled in another team "
                    f"for this competition."
                )

        # Create team (no team-level fee — fees are per-student on TeamMember)
        team = self._teams.create_team(competition_id=cmd.competition_id,
            team_name=cmd.team_name,
            category=cmd.category,
            subcategory=cmd.subcategory,
            coach_id=cmd.coach_id,
            group_id=cmd.group_id,
            notes=cmd.notes,
            project_name=cmd.project_name,
            project_description=cmd.project_description,
        )

        # Add members with per-student fee from input (default to competition fee if not specified)
        members_added = 0
        for sid in student_ids:
            amount_due = None
            if cmd.student_fees and sid in cmd.student_fees:
                amount_due = cmd.student_fees[sid]
                
            if amount_due is None:
                amount_due = float(comp.fee_per_student or 0.0)

            # Skip duplicates gracefully
            existing = self._teams.get_team_member(team.id, sid)
            if not existing:
                self._teams.add_team_member(team.id, sid, amount_due=amount_due)
                members_added += 1

        # Log activity and notify for each student
        self._log_team_registration_activity(
            db=db,
            team=team,
            student_ids=student_ids,
            competition_name=comp.name,
            current_user_id=current_user_id,
        )

        # Notify: team registration per student
        # Commit first so data is visible to the background task's fresh session
        self._uow.commit()
        db.refresh(team)
        for sid in student_ids:
            self._notify(
                "team_registration",
                student_id=sid,
                team_id=team.id,
                team_name=team.team_name,
                competition_name=comp.name,
                category=cmd.category,
                subcategory=cmd.subcategory,
            )


        warning = "; ".join(duplicate_warnings) if duplicate_warnings else None
        return TeamRegistrationResultWithWarningDTO(
            result=TeamRegistrationResultDTO(
                team=TeamDTO.model_validate(team),
                members_added=members_added
            ),
            warning=warning,
        )

    def _resolve_student_ids(self, db, cmd: RegisterTeamInput) -> list[int]:
        """Resolve final student IDs from group pre-fill and/or manual list."""
        group_ids: list[int] = []
        if cmd.group_id:
            group = db.get(Group, cmd.group_id)
            if not group:
                raise NotFoundError(f"Group {cmd.group_id} not found.")
            if group.status != "active":
                raise BusinessRuleError(f"Group '{group.name}' is not active.")

            # Fetch active enrollments at the group's current level
            enrollments = db.exec(
                select(Enrollment).where(
                    Enrollment.group_id == cmd.group_id,
                    Enrollment.level_number == group.level_number,
                    Enrollment.status == "active",
                )
            ).all()
            group_ids = [e.student_id for e in enrollments]
            if not group_ids:
                raise BusinessRuleError(
                    f"Group '{group.name}' has no active students at level {group.level_number}."
                )

        manual_ids = cmd.student_ids or []
        # Merge: group roster + manual list (union, preserve order)
        seen = set()
        combined = []
        for sid in group_ids + manual_ids:
            if sid not in seen:
                seen.add(sid)
                combined.append(sid)

        if not combined:
            raise BusinessRuleError(
                "At least one student is required. Provide student_ids or select a group with active students."
            )

        return combined

    def _log_team_registration_activity(
        self,
        db,
        team,
        student_ids: list[int],
        competition_name: str,
        current_user_id: Optional[int],
    ) -> None:
        """Log competition registration activity for each team member."""
        # Create UoW and activity service
        # Note: This is a simplified integration - in production you'd want to
        # share the same transaction/session
        try:
            uow = UnitOfWork(db)
            activity_svc = StudentActivityService(uow)

            for sid in student_ids:
                activity_svc.log_competition_registration(
                    LogCompetitionRegistrationDTO(
                        student_id=sid,
                        competition_id=team.competition_id,
                        competition_name=competition_name,
                        performed_by=current_user_id,
                    )
                )
            uow.commit()
        except Exception:
            logger.exception("Failed to log competition registration activity for team %s", team.id)
