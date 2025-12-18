from django.urls import path
from . import views
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('admin-login/', admin_login_view, name='admin_login'),
    path('admin/logout/', views.admin_logout_view, name='admin_logout'),
    path('admin/', admin_home_view, name='admin_home'),       
    path('admin/dashboard/', admin_home_view, name='admin_dashboard'),  
]