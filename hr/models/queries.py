from django.db.models import Sum, Q

# Get the payroll instance
payroll = Payroll.objects.get(id=25)

# Fetch distinct banks for this payroll
payroll_banks = Bank.objects.filter(employees__payroll_items__payroll=payroll).distinct()

bank_totals = []  # Store results for each bank

for bank in payroll_banks:
    # Filter payroll items related to the current bank
    payroll_items = PayrollItem.objects.filter(
        payroll=payroll,
        employee__bank=bank  # Filter employees in this bank
    )

    # Get salary items total (grouping by salary_item foreign key)
    salary_items = (
        payroll_items.filter(item_type='salary_item')
        .values('salary_item')  # Group by salary_item ForeignKey
        .annotate(total=Sum('amount'))
    )

    # Get credit unions total (grouping by credit_union foreign key)
    credit_unions = (
        payroll_items.filter(item_type='credit_union')
        .values('credit_union')  # Group by credit_union ForeignKey
        .annotate(total=Sum('amount'))
    )

    # Get loans total (grouping by loan type)
    loans = (
        payroll_items.filter(item_type='loan')
        .values('loan__loan_type')  # Group by loan type
        .annotate(total=Sum('amount'))
    )

    # Totals for deductions like SSNIT, Tax
    employee_ssnit_total = payroll_items.filter(item_type='employee_ssnit').aggregate(total=Sum('amount'))['total'] or 0
    employer_ssnit_total = payroll_items.filter(item_type='employer_ssnit').aggregate(total=Sum('amount'))['total'] or 0
    tax_total = payroll_items.filter(item_type='tax').aggregate(total=Sum('amount'))['total'] or 0

    # Append all results to the bank's record
    bank_totals.append({
        'bank_name': bank.bank_name,
        'salary_items': list(salary_items),  # List of distinct salary item totals
        'credit_unions': list(credit_unions),  # List of distinct credit union totals
        'loans': list(loans),  # List of distinct loan type totals
        'employee_ssnit_total': employee_ssnit_total,
        'employer_ssnit_total': employer_ssnit_total,
        'tax_total': tax_total,
    })

# Print or return the totals for all banks
for bank_total in bank_totals:
    print(bank_total)


# Example Optimization

