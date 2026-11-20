"""Staging-only E2E data purge (#218), ADR-0006.

Deletes every row reachable from the seed set (names starting ``e2e-``) in ONE
transaction over the caller's UnitOfWork, children before parents. It lives in finance,
the highest module that writes the affected tables; each module's rows go through its
own purge service (ADR-0004). The caller guards the environment before calling this.
"""
from app.db.uow import UnitOfWork
from app.modules.academics import AcademicsE2EPurgeService
from app.modules.attendance import AttendanceE2EPurgeService
from app.modules.competitions import CompetitionsE2EPurgeService
from app.modules.crm import CrmE2EPurgeService
from app.modules.enrollments import EnrollmentsE2EPurgeService
from app.modules.finance.repositories.e2e_purge_repository import FinanceE2EPurgeRepository
from app.modules.finance.schemas.e2e_purge import E2EPurgeResultDTO

E2E_PREFIX = "e2e-"


class E2EPurgeService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._repo = FinanceE2EPurgeRepository(uow.session)
        self._crm = CrmE2EPurgeService(uow)
        self._academics = AcademicsE2EPurgeService(uow)
        self._enrollments = EnrollmentsE2EPurgeService(uow)
        self._attendance = AttendanceE2EPurgeService(uow)
        self._competitions = CompetitionsE2EPurgeService(uow)

    def purge(self, run_id: str | None = None) -> E2EPurgeResultDTO:
        # names are e2e-<run_id>-<worker>...: the trailing dash keeps run "ab" from matching run "abcd"
        prefix = f"{E2E_PREFIX}{run_id}-" if run_id else E2E_PREFIX
        crm = self._crm.find_seed(prefix)
        acad = self._academics.find_seed(prefix)
        enrollment_ids = self._enrollments.find_enrollment_ids(crm.student_ids, acad.group_ids)
        comp = self._competitions.find_seed(prefix, crm.student_ids)
        payment_ids = self._repo.find_payment_ids(crm.student_ids, enrollment_ids, comp.team_member_ids)
        receipt_ids = self._repo.find_receipt_ids(payment_ids, prefix)

        counts: dict[str, int] = {}
        counts.update(self._attendance.purge(crm.student_ids, acad.session_ids, enrollment_ids).counts)
        counts["payments"] = self._repo.delete_payments(payment_ids)
        counts["receipts"] = self._repo.delete_receipts_without_payments(receipt_ids)
        counts.update(self._enrollments.purge(enrollment_ids, crm.student_ids, acad.level_ids).counts)
        counts.update(self._competitions.purge(comp).counts)
        counts.update(self._academics.purge(acad).counts)
        counts.update(self._crm.purge(crm).counts)
        self._uow.commit()
        return E2EPurgeResultDTO(prefix=prefix, counts=counts)
