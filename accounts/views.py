from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer, RegisterSerializer
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .models import CustomUser
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user": {
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
            },
            "message": "User created successfully",
        }, status=status.HTTP_201_CREATED)
    


# accounts/views.py

@sensitive_post_parameters()
@csrf_protect
@never_cache
def admin_login_view(request):
    """
    Custom admin login view  now redirects to your beautiful dashboard
    """
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('accounts:admin_home')  # ← Your new dashboard

    if request.method == "POST":
        email = request.POST.get('email', '').strip().lower()  # ← Now matches name="email"
        password = request.POST.get('password')

        # Honeypot check (anti-bot)
        if request.POST.get('website'):
            messages.error(request, "Login failed. Please try again.")
            return render(request, 'admin/admin_login.html')

        if not email or not password:
            messages.error(request, "Please provide both email and password.")
        else:
            user = authenticate(request, username=email, password=password)
            if user is not None:
                if user.is_staff or user.is_superuser:
                    login(request, user)
                    messages.success(request, f"Welcome back, {user.get_full_name() or user.email}!")

                    # Respect ?next= parameter, otherwise go to custom dashboard
                    next_url = request.GET.get('next')
                    if next_url and next_url.startswith('/admin/'):
                        return redirect(next_url)
                    return redirect('accounts:admin_home')  # ← YOUR DASHBOARD

                else:
                    messages.error(request, "You don't have admin access.")
            else:
                messages.error(request, "Invalid email or password.")

    return render(request, 'admin/admin_login.html')



@staff_member_required(login_url='accounts:admin_login')
def admin_home_view(request):
    """
    ElectroMart Admin Dashboard – Home Page
    Simple, beautiful welcome screen for staff after login.
    """
    context = {
        'title': 'Dashboard • ElectroMart Admin',
        'user': request.user,
        'current_year': timezone.now().year,
        'total_staff': request.user.__class__.objects.filter(is_staff=True).count(),
    }
    return render(request, 'admin/admin_home.html', context)


@csrf_protect
@never_cache
def admin_logout_view(request):
    """
    Secure Admin Logout View
    Logs out admin/staff users and redirects to admin login page.
    """
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "You have been logged out successfully.")

    return redirect('accounts:admin_login')