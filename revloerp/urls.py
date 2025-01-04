"""revloerp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
]

urlpatterns += [
    path('hr/', include('hr.urls')),
    path('', include('core.urls')),
    path('hr/payroll/', include('hr.urls.payroll_urls')),
    path('administration/', include('administration.urls')),
    path('sales/', include('sales.urls')),
    path('report/', include('report.urls')),

]

# urls for operations module
urlpatterns += [
    path('operations/warehouse/', include('operations.urls.warehouse_urls')),
    path('operations/customers/', include('operations.urls.customer_urls')),
    path('operations/suppliers/', include('operations.urls.supplier_urls')),
    path('operations/inventories/', include('operations.urls.inventory_urls')),
]

# urls for finance module
urlpatterns += [
    path('finance/expense/', include('finance.urls.expense_urls')),
    path('finance/revenue/', include('finance.urls.revenue_urls')),
    path('finance/account/', include('finance.urls.account_urls')),
    path('finance/other-transactions/', include('finance.urls.other_trans_urls')),
]

# urls for report module
urlpatterns += [
    path('report/hr/', include('report.urls.hr_report_urls')),
    path('report/payroll/', include('report.urls.payroll_report_urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
