from fastapi import APIRouter, HTTPException
from app.schemas.schemas import SettlementResponse, Transaction
from app.models.database import get_connection
from app.services.settlement import compute_net_balances, minimise_transactions

router = APIRouter()


@router.get("/{group_id}/settle", response_model=SettlementResponse)
def get_settlement_plan(group_id: int):
    """
    Returns the minimum number of transactions needed to settle
    all debts within the group.

    Algorithm: Greedy max-heap pairing of largest creditor
    with largest debtor at each step — O(n log n).
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Verify group exists
        cursor.execute("SELECT id FROM groups_tbl WHERE id = %s", (group_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Group not found")

        # Fetch all expenses with their splits
        cursor.execute(
            "SELECT id, paid_by, amount FROM expenses WHERE group_id = %s",
            (group_id,)
        )
        expenses = cursor.fetchall()

        if not expenses:
            return SettlementResponse(
                group_id=group_id,
                transactions=[],
                total_transactions=0
            )

        for expense in expenses:
            cursor.execute(
                "SELECT member_id, share FROM expense_splits WHERE expense_id = %s",
                (expense["id"],)
            )
            expense["splits"] = cursor.fetchall()

        # Compute net balances and minimise transactions
        balances     = compute_net_balances(expenses)
        raw_txns     = minimise_transactions(balances)

        # Fetch member names for readable output
        cursor.execute(
            "SELECT id, name FROM members WHERE group_id = %s", (group_id,)
        )
        name_map = {row["id"]: row["name"] for row in cursor.fetchall()}

        transactions = [
            Transaction(
                from_member=name_map.get(debtor_id, f"Member {debtor_id}"),
                to_member=name_map.get(creditor_id, f"Member {creditor_id}"),
                amount=amount
            )
            for debtor_id, creditor_id, amount in raw_txns
        ]

        return SettlementResponse(
            group_id=group_id,
            transactions=transactions,
            total_transactions=len(transactions)
        )

    finally:
        cursor.close()
        conn.close()


@router.get("/{group_id}/balances")
def get_balances(group_id: int):
    """
    Returns each member's net balance.
    Positive = others owe them. Negative = they owe others.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM groups_tbl WHERE id = %s", (group_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Group not found")

        cursor.execute(
            "SELECT id, paid_by, amount FROM expenses WHERE group_id = %s",
            (group_id,)
        )
        expenses = cursor.fetchall()

        for expense in expenses:
            cursor.execute(
                "SELECT member_id, share FROM expense_splits WHERE expense_id = %s",
                (expense["id"],)
            )
            expense["splits"] = cursor.fetchall()

        balances = compute_net_balances(expenses)

        cursor.execute(
            "SELECT id, name FROM members WHERE group_id = %s", (group_id,)
        )
        name_map = {row["id"]: row["name"] for row in cursor.fetchall()}

        return {
            "group_id": group_id,
            "balances": [
                {
                    "member_id": mid,
                    "name": name_map.get(mid, f"Member {mid}"),
                    "net_balance": round(bal, 2),
                    "status": "to_receive" if bal > 0 else "to_pay" if bal < 0 else "settled"
                }
                for mid, bal in balances.items()
            ]
        }
    finally:
        cursor.close()
        conn.close()
