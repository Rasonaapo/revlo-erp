from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from hr.models.payroll import SalaryGrade
from django_datatables_view.base_datatable_view import BaseDatatableView
from django.utils.html import escape
from datetime import date
from django.db.models import Q
import json

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