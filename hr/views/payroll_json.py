from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from hr.models.payroll import SalaryGrade, Tax, SalaryItem, Loan, CreditUnion
from django_datatables_view.base_datatable_view import BaseDatatableView
from django.utils.html import escape
from datetime import date
from django.db.models import Q, Count
import json
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .utils import item_expiry_status

class SalaryGradeListApiView(LoginRequiredMixin, BaseDatatableView):
    model = SalaryGrade
    columns = ['id', 'grade', 'step', 'amount', 'employee_count', 'created_at']

    def render_column(self, row, column):
        if column == 'created_at':
            return row.created_at.strftime('%d %b, %Y')  # Format the created_at field
        
        # <td>{{ sg.get_currency_symbol }}{{ sg.amount|default:'-' }}</td>
        if column == 'amount':
            if row.amount:
                return f"{row.get_currency_symbol()}{row.amount}"
            else:
                return "N/A"
        
        if column == 'employee_count':
            return row.employee_count
        
        if column == 'step':
            return row.grade_step.step

        if column == 'id':
            return row.id
        
        return super().render_column(row, column)

    def get_initial_queryset(self):
        return SalaryGrade.objects.annotate(employee_count=Count('employees'))
    
    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(grade__icontains=search) |
                Q(grade_step__step__icontains=search) |
                Q(amount__icontains=search)  |
                Q(employees__first_name__icontains=search) |
                Q(employees__last_name__icontains=search)

            )
        return qs
    
class SalaryItemListApiView(LoginRequiredMixin, BaseDatatableView):
    model = SalaryItem
    columns = ['id', 'item_name', 'alias_name', 'entry', 'rate_type', 'rate_amount', 'rate_dependency', 'affected_employees', 'created_at']

    def render_column(self, row, column):
        if column == 'created_at':
            return row.created_at.strftime('%d %b, %Y')  # Format the created_at field
        
        # <td>{{ sg.get_currency_symbol }}{{ sg.amount|default:'-' }}</t
        if column == 'alias_name':
            return row.get_condition_display()
        
        if column == 'entry':
                return row.get_effect_display()

        if column == 'rate_type':
            return row.get_rate_type_display()
        
        if column == 'affected_employees':
            return row.eligible_employee_count
        
        if column == 'rate_dependency':
            # if value is not basic, then it's an ID for another salary item..
            dependency = row.rate_dependency
            if row.rate_type == "factor":
                if dependency != 'Basic':
                    try:
                        dependency = SalaryItem.objects.get(id=dependency).item_name
                    except SalaryItem.DoesNotExist:
                        dependency = 'Unknown Item'
            elif row.rate_type == 'fix':
                dependency = '-'
            return dependency

        if column == 'id':
            return row.id
        
        return super().render_column(row, column)

    def get_initial_queryset(self):
        return SalaryItem.objects.all()
    
    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(item_name__icontains=search) |
                Q(condition__icontains=search) |
                Q(rate_amount__icontains=search) |
                Q(rate_type__icontains=search) |
                Q(rate_dependency__icontains=search) |
                Q(alias_name__icontains=search) |
                Q(salary_grade__grade__icontains=search) |
                Q(applicable_to__first_name__icontains=search) |
                Q(applicable_to__last_name__icontains=search)

            )
        return qs

def load_tax(request):
        today = timezone.now()
        # Let's query for the current year's tax setup from GRA setup
        current_year_setup = Tax.objects.filter(year=today.year).order_by('rate')
        container = []
        if current_year_setup.exists():
            container = [{'id':item.id, 'block':item.block, 'rate':item.rate } for item in current_year_setup] 
            return JsonResponse(container, safe=False)
        else:
            return JsonResponse(container, safe=False)

def test_tax(request, **kwargs):
    amount = float(kwargs['amount'])
    year = timezone.now().year
    tax = Tax.calculate_tax(year, amount)
    return JsonResponse(tax, safe=False)

def load_salary_items(request):
    data = [{'id':'Basic', 'name':'BASIC'}]
    # load all the salary items and sort out those with expires on to ensure they're not expired already
    salary_items = SalaryItem.objects.all()
    for item in salary_items:
        expires_on = item.expires_on

        # if this item has expires_on value and is expired, exclude it from the list
        if expires_on  and  item_expiry_status(expires_on):
            continue

        data.append({'id':item.id, 'name':item.item_name})
    return JsonResponse(data, safe=False)      

class LoanListApiView(LoginRequiredMixin, BaseDatatableView):
    model = Loan
    columns = ['employee', 'loan_type', 'principal_amount', 'interest_rate', 'duration_in_months', 'monthly_installment', 'outstanding_balance', 'status', 'applied_on',  'deduction_end_date', 'created_at']
       
    def render_column(self, row, column):
        if column == 'created_at':
            return row.created_at.strftime('%d %b, %Y')  # Format the created_at field
        
        if column == 'applied_on':
            return row.applied_on.strftime('%d %b, %Y')  # Format the created_at field
        
        if column == 'deduction_end_date':
            return row.deduction_end_date.strftime('%d %b, %Y') if row.deduction_end_date else '-'  # Format the created_at field

        if column == 'status':
            return {'theme':row.get_status_theme(), 'status':row.get_status_display()} 
              
        return super().render_column(row, column)

    def get_initial_queryset(self):
        return Loan.objects.all().order_by('applied_on', 'approved_on')
    
    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(loan_type__icontains=search) |
                # Q(condition__icontains=search) |
                # Q(rate_amount__icontains=search) |
                # Q(rate_type__icontains=search) |
                # Q(rate_dependency__icontains=search) |
                # Q(alias_name__icontains=search) |
                # Q(salary_grade__grade__icontains=search) |
                Q(employee__first_name__icontains=search) |
                Q(employee__last_name__icontains=search)

            )
        # process drop down filters from template
        status = self.request.GET.get('filterStatus')
        loan_type = self.request.GET.get('filterLoanType')

        if status:
            qs = qs.filter(status=status)
        if loan_type:
            qs = qs.filter(loan_type=loan_type)
            
        return qs
    
# Credit Unions 

class CreditUnionListApiView(LoginRequiredMixin, BaseDatatableView):
    model = CreditUnion
    columns = ['credit_union', 'amount', 'deduction_start_date', 'employee_count', 'deduction_end_date', 'created_at']

    def render_column(self, row, column):
        if column == 'created_at':
            return row.created_at.strftime('%d %b, %Y')  # Format the created_at field
        
        if column == 'credit_union':
            return row.union_name
        
        if column == 'deduction_start_date':
            return row.deduction_start_date.strftime('%d %b, %Y') if row.deduction_start_date else '-'  
        
        if column == 'deduction_end_date':
            return row.deduction_end_date.strftime('%d %b, %Y') if row.deduction_end_date else '-'

        if column == 'employee_count':
            return row.get_eligible_employees().count()
          
        return super().render_column(row, column)
    
    def get_initial_queryset(self):
        return CreditUnion.objects.all()
    
    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(union_name__icontains=search)
            )
        return qs