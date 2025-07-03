from .schema import ExpenseFilters
from .models import Expense


def build_expense_filters(filters: ExpenseFilters) -> list:
    expense_filters = [Expense.account_id == filters.account_id]

    field_mapping = {
        "category_id": Expense.category_id == filters.category_id,
        "name": Expense.name == filters.name,
        "start_date": Expense.expense_date >= filters.start_date,
        "end_date": Expense.expense_date <= filters.end_date,
        "min_amount": Expense.amount >= filters.min_amount,
        "max_amount": Expense.amount <= filters.max_amount
    }

    for field, condition in field_mapping.items():
        if getattr(filters, field) is not None:
            expense_filters.append(condition)

    return expense_filters
