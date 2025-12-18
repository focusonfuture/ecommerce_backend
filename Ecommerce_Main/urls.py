from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

def redirect_to_custom_admin_login(request):
    return redirect('accounts:admin_login')

urlpatterns = [
    path('', include('accounts.urls')),  # better: move admin_login here or use view
    path('api/auth/', include('accounts.urls')),  # Clean prefix

    path('', include('products.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)