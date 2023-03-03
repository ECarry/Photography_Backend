from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from .seriazlizers import UserSerializer
from .models import User


class UserView(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    permission_classes = [IsAuthenticated]
