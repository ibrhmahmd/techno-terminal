"""HR Unit of Work

Transaction management for HR operations.
"""
from sqlmodel import Session

from .employee_repository import EmployeeRepository
from .staff_account_repository import StaffAccountRepository


class HRUnitOfWork:
    """Unit of Work for HR module transactions.
    
    Coordinates multiple repositories in a single transaction.
    
    Example:
        with get_session() as session:
            uow = HRUnitOfWork(session)
            service = EmployeeCrudService(uow)
            result = service.create(dto)
            uow.commit()
    """

    def __init__(self, session: Session):
        self._session = session
        self.employees = EmployeeRepository(session)
        self.staff_accounts = StaffAccountRepository(session)

    def commit(self) -> None:
        """Commit the transaction."""
        self._session.commit()

    def flush(self) -> None:
        """Flush pending changes to database."""
        self._session.flush()

    def rollback(self) -> None:
        """Rollback the transaction."""
        self._session.rollback()
