from fastapi import APIRouter, HTTPException
from app.schemas.schemas import ExpenseCreate, ExpenseResponse, SplitEntry
from app.models.database import get_connection

router = APIRouter()


@router.post("/{group_id}/expenses", response_model=ExpenseResponse, status_code=201)
def add_expense(group_id: int, body: ExpenseCreate):
    # Validate splits sum matches total amount
    split_total = round(sum(s.share for s in body.splits), 2)
    if abs(split_total - round(body.amount, 2)) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Split shares ({split_total}) must sum to expense amount ({body.amount})"
        )

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Verify group exists
        cursor.execute("SELECT id FROM groups_tbl WHERE id = %s", (group_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Group not found")

        # Verify payer is in this group
        cursor.execute(
            "SELECT id FROM members WHERE id = %s AND group_id = %s",
            (body.paid_by, group_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Payer is not a member of this group")

        # Verify all split members are in this group
        member_ids = [s.member_id for s in body.splits]
        fmt = ",".join(["%s"] * len(member_ids))
        cursor.execute(
            f"SELECT id FROM members WHERE id IN ({fmt}) AND group_id = %s",
            (*member_ids, group_id)
        )
        valid_ids = {row["id"] for row in cursor.fetchall()}
        invalid = set(member_ids) - valid_ids
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Member IDs {invalid} do not belong to this group"
            )

        # Insert expense
        cursor.execute(
            "INSERT INTO expenses (group_id, paid_by, description, amount) VALUES (%s, %s, %s, %s)",
            (group_id, body.paid_by, body.description, body.amount)
        )
        expense_id = cursor.lastrowid

        # Insert splits
        split_data = [(expense_id, s.member_id, s.share) for s in body.splits]
        cursor.executemany(
            "INSERT INTO expense_splits (expense_id, member_id, share) VALUES (%s, %s, %s)",
            split_data
        )
        conn.commit()

        # Return full expense
        cursor.execute("SELECT * FROM expenses WHERE id = %s", (expense_id,))
        expense = cursor.fetchone()
        expense["splits"] = [{"member_id": s.member_id, "share": s.share} for s in body.splits]
        return expense

    finally:
        cursor.close()
        conn.close()


@router.get("/{group_id}/expenses", response_model=list[ExpenseResponse])
def list_expenses(group_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM expenses WHERE group_id = %s ORDER BY created_at DESC",
            (group_id,)
        )
        expenses = cursor.fetchall()

        for expense in expenses:
            cursor.execute(
                "SELECT member_id, share FROM expense_splits WHERE expense_id = %s",
                (expense["id"],)
            )
            expense["splits"] = cursor.fetchall()

        return expenses
    finally:
        cursor.close()
        conn.close()


@router.delete("/{group_id}/expenses/{expense_id}", status_code=204)
def delete_expense(group_id: int, expense_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM expenses WHERE id = %s AND group_id = %s",
            (expense_id, group_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Expense not found")
    finally:
        cursor.close()
        conn.close()
