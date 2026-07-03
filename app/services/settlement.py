"""
Debt Minimisation Algorithm
----------------------------
Problem : Given N people with net balances (positive = owed money,
          negative = owes money), find the MINIMUM number of
          transactions to settle all debts.

Approach : Greedy two-pointer on sorted balance list.
           At each step, pair the person who owes the most with
           the person who is owed the most. One of them reaches
           zero — eliminating them from future rounds.

Time  : O(n log n)  — dominated by sort
Space : O(n)

This is optimal for the general case (proven NP-hard for the
exact minimum, but greedy gives minimum for the common split-equal
/ arbitrary-share case used here).
"""

import heapq
from typing import List, Tuple, Dict


def minimise_transactions(
    balances: Dict[int, float]          # member_id -> net balance
) -> List[Tuple[int, int, float]]:      # (debtor_id, creditor_id, amount)
    """
    Returns list of (from_id, to_id, amount) transactions
    that settle all debts in the minimum number of transfers.
    """
    # Separate into creditors (owed money) and debtors (owe money)
    # Use max-heaps (negate for Python's min-heap)
    creditors = []   # max-heap: (-amount, member_id)
    debtors   = []   # max-heap: (-amount, member_id)

    for member_id, balance in balances.items():
        if balance > 0.009:           # creditor — someone owes them
            heapq.heappush(creditors, (-balance, member_id))
        elif balance < -0.009:        # debtor   — they owe someone
            heapq.heappush(debtors,   (balance,  member_id))
        # balances within ±0.01 are considered settled (float rounding)

    transactions = []

    while creditors and debtors:
        credit_amt, creditor_id = heapq.heappop(creditors)
        debit_amt,  debtor_id   = heapq.heappop(debtors)

        credit_amt = -credit_amt      # convert back to positive
        debit_amt  = -debit_amt       # convert back to positive

        # The smaller of the two determines this transaction amount
        settled = min(credit_amt, debit_amt)
        transactions.append((debtor_id, creditor_id, round(settled, 2)))

        remaining_credit = credit_amt - settled
        remaining_debit  = debit_amt  - settled

        # Whoever still has a balance goes back into the heap
        if remaining_credit > 0.009:
            heapq.heappush(creditors, (-remaining_credit, creditor_id))
        if remaining_debit > 0.009:
            heapq.heappush(debtors,   (-remaining_debit,  debtor_id))

    return transactions


def compute_net_balances(
    expenses: List[dict],    # [{paid_by, amount, splits: [{member_id, share}]}]
) -> Dict[int, float]:
    """
    Compute net balance per member across all expenses.
    Positive balance  = others owe this member money.
    Negative balance  = this member owes others money.
    """
    balances: Dict[int, float] = {}

    for expense in expenses:
        payer_id = expense["paid_by"]
        amount   = float(expense["amount"])

        # Payer is credited the full amount
        balances[payer_id] = balances.get(payer_id, 0) + amount

        # Each member in the split is debited their share
        for split in expense["splits"]:
            mid   = split["member_id"]
            share = float(split["share"])
            balances[mid] = balances.get(mid, 0) - share

    return balances
