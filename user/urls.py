from . import views
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .token import MyTokenObtainPairView


urlpatterns = [
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/<int:pk>', views.UserView.as_view({
        'get': 'retrieve',
        'delete': 'destroy',
        'put': 'update',
        'patch': 'perform_update'
    }), name='user_info')
]
