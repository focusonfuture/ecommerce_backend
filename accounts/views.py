from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer, RegisterSerializer
from .models import CustomUser

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
    


# http://127.0.0.1:8000/api/auth/register/
{
  "email": "alice@example.com",
  "password": "VeryStrongPass123",
  "password2": "VeryStrongPass123",
  "first_name": "Alice",
  "last_name": "Wonderland",
  "username": "alice123",
  "phone": "+19876543210"
}

# http://127.0.0.1:8000/api/auth/login/
{
  "email": "alice@example.com",
  "password": "VeryStrongPass123"
}

# Go to Authorization tab
# Type: Bearer Token
# Paste the access token (not refresh) into the Token field

# Authorization:

# http://127.0.0.1:8000/api/auth/token/refresh/
# {
#   "refresh": ""
# }



#change user to data
#add status
#access token
#refresh token
#token storage
#session storage

