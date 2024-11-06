from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from hr.models.payroll import SalaryGrade, Tax
from django_datatables_view.base_datatable_view import BaseDatatableView
from django.utils.html import escape
from datetime import date
from django.db.models import Q
import json
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse

class SalaryGradeListApiView(LoginRequiredMixin, BaseDatatableView):
    model = SalaryGrade
    columns = ['id', 'grade', 'step', 'amount', 'created_at']

    def render_column(self, row, column):
        if column == 'created_at':
            return row.created_at.strftime('%d %b, %Y')  # Format the created_at field
        
        # <td>{{ sg.get_currency_symbol }}{{ sg.amount|default:'-' }}</td>
        if column == 'amount':
            if row.amount:
                return f"{row.get_currency_symbol()}{row.amount}"
            else:
                return "N/A"

        if column == 'id':
            return row.id
        
        return super().render_column(row, column)

    def get_initial_queryset(self):
        return SalaryGrade.objects.all()
    
    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(grade__icontains=search) |
                Q(step__icontains=search) |
                Q(amount__icontains=search) 

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


       
    