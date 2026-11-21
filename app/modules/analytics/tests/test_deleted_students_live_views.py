"""#175: live views hide a soft-deleted student; the delete use case drops their active enrollments."""
from datetime import date

from app.modules.academics.repositories.group_details_repository import GroupDetailsRepository
from app.modules.analytics.repositories.academic_repository import AcademicRepository
from app.modules.analytics.repositories.dashboard_repository import DashboardRepository
from app.modules.analytics.repositories.financial_repository import FinancialRepository
from app.modules.enrollments.models import Enrollment
from app.modules.enrollments.services.student_deletion_service import StudentDeletionService
from app.modules.finance.repositories.payment_repository import PaymentRepository
from app.modules.finance.tests.characterization.test_finance_api import _seed_enrollment
from app.modules.notifications.repositories.reports_repository import ReportsRepository
from app.modules.notifications.schemas.report_dto import PeriodReportAggregateDTO
from app.shared.datetime_utils import utc_now


def _seed(uow):
    _, group, student, enrollment = _seed_enrollment(uow.session)
    return group, student, enrollment


def _hide(uow, student):
    student.deleted_at = utc_now()
    uow.session.add(student)
    uow.commit()


def test_live_queries_hide_deleted_student(uow):
    group, student, enrollment = _seed(uow)  # active, unpaid: balance < 0
    s = uow.session
    details, academic = GroupDetailsRepository(s), AcademicRepository(s)
    dash, fin = DashboardRepository(s), FinancialRepository(s)

    def visible():
        sid = student.id
        proj = academic.get_student_progress(group_id=group.id)
        period = PeriodReportAggregateDTO()
        ReportsRepository(s).populate_detailed_arrays(period, date(2026, 1, 1), date(2026, 12, 31))
        return {
            "level_roster": any(r.student_id == sid for r in details.get_roster_for_group_level(group.id, 1)),
            "group_enrollments": any(r.student_id == sid for r in details.get_enrollments_by_group_with_students(group.id)),
            "dash_roster": any(r.student_id == sid for r in dash.get_roster_for_group_level(group.id, 1)),
            "progress": any(r.student_id == sid for r in proj),
            "top_debtors": any(r.student_id == sid for r in fin.get_top_debtors(1000)),
            "unpaid": any(i.student_id == sid for i in PaymentRepository(s).get_unpaid_enrollments(group_id=group.id).items),
            "report_debtors": any(d.student_name == student.full_name for d in period.cumulative_unpaid_debtors),
            "outstanding": any(o.group_id == group.id for o in fin.get_outstanding_by_group()),
        }

    assert all(visible().values())
    _hide(uow, student)
    assert not any(visible().values()), visible()


def test_delete_use_case_drops_active_enrollments_only(uow):
    _, student, enrollment = _seed(uow)
    done = Enrollment(student_id=student.id, group_id=enrollment.group_id, level_number=2,
                      amount_due=0, discount_applied=0, status="completed")
    uow.session.add(done)
    uow.commit()

    assert StudentDeletionService(uow).delete_student(student.id, deleted_by=None) is True
    uow.rollback()  # only committed state survives

    uow.session.refresh(enrollment)
    uow.session.refresh(done)
    uow.session.refresh(student)
    assert student.deleted_at is not None
    assert enrollment.status == "dropped"
    assert done.status == "completed"
    assert StudentDeletionService(uow).delete_student(student.id, deleted_by=None) is False
