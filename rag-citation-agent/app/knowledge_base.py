from app.models import Document


DOCUMENTS = [

    Document(
        id="doc-001",
        title="Remote Work Policy",
        content=(
            "Employees may work remotely up to three days "
            "per week. The remaining working days must be "
            "spent at an approved company office."
        ),
        source="employee_handbook.md",
    ),

    Document(
    id="doc-002",
    title="Vacation Policy",
    content=(
        "The company encourages employees to take regular "
        "time away from work to maintain a healthy work-life "
        "balance. Vacation should normally be planned in "
        "advance with the employee's manager. "

        "Full-time employees receive 25 days of paid vacation "
        "per calendar year. Part-time employees receive vacation "
        "on a proportional basis. "

        "Employees should submit vacation requests through the "
        "HR system. Requests longer than two consecutive weeks "
        "require additional manager approval."
    ),
    source="employee_handbook.md",
    ),

    Document(
        id="doc-003",
        title="Travel Policy",
        content=(
            "International business-class travel is permitted "
            "for flights with a scheduled duration greater "
            "than eight hours."
        ),
        source="travel_policy.md",
    ),

    Document(
        id="doc-004",
        title="Expense Policy",
        content=(
            "Employees may claim up to $80 per day for meals "
            "while travelling on approved business trips."
        ),
        source="expense_policy.md",
    ),

]