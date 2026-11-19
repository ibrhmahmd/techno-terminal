"""Hard delete clears children before parents (#219).

payments.team_member_id references team_members with no ON DELETE rule, so
team_members must be deleted after the payments that point at them.
"""
from sqlalchemy import text

from app.testing.db_helpers import (
    create_test_competition,
    create_test_payment,
    create_test_receipt,
    create_test_student,
    create_test_team,
    create_test_team_member,
)


def test_hard_delete_student_with_competition_fee_payment(
    client_with_uow, uow, override_auth, mock_admin_headers
):
    s = uow.session
    student = create_test_student(s, full_name="Hard Del Comp")
    comp = create_test_competition(s, fee_per_student=100)
    team = create_test_team(s, comp.id)
    member = create_test_team_member(s, team.id, student.id, amount_due=100, amount_paid=100)
    receipt = create_test_receipt(s)
    create_test_payment(
        s, receipt.id, student.id, 100, team_member_id=member.id, payment_type="competition"
    )
    # a refund pointing at the original payment must not block the delete either
    original = s.execute(
        text("SELECT id FROM payments WHERE student_id = :s"), {"s": student.id}
    ).scalar_one()
    create_test_payment(
        s, receipt.id, student.id, 10, team_member_id=member.id,
        transaction_type="refund", payment_type="competition",
    )
    s.execute(
        text("UPDATE payments SET original_payment_id = :o WHERE student_id = :s AND transaction_type = 'refund'"),
        {"o": original, "s": student.id},
    )
    s.commit()

    r = client_with_uow.delete(f"/api/v1/crm/students/{student.id}/hard", headers=mock_admin_headers)

    assert r.status_code == 200, r.text
    for table in ("students", "team_members", "payments"):
        col = "id" if table == "students" else "student_id"
        assert s.execute(
            text(f"SELECT count(*) FROM {table} WHERE {col} = :s"), {"s": student.id}
        ).scalar_one() == 0, table
