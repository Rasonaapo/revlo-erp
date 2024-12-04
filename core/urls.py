from django.urls import path
from . import views

# url patterns for functions in core.views
urlpatterns = [
    path('', views.index, name='login'),
    path('accounts/login/', views.index, name='login'),

    path('logout/', views.logout_user, name='logout'),
    path('change-password/', views.change_password, name='change-password'),
    path('profile/', views.user_profile, name='profile'),
     path('developers-disclaimer/', views.disclaimer, name='disclaimer'),


    path('dashboard/', views.dashboard, name='dashboard'),
    path('logger/', views.test_logging_view, name='logger'),

]

