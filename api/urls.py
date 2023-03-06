from rest_framework import routers
from . import views
from django.urls import path, include

router = routers.DefaultRouter()
router.register(r'photos', views.PhotoViewSet)
router.register(r'category', views.CategoryViewSet)
router.register(r'videos', views.VideoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

# urlpatterns = [
#     path('photos/', views.PhotoViewSet.as_view({
#         'get': 'list',
#         'post': 'create'
#     })),
#     path('photos/<int:pk>', views.PhotoViewSet.as_view({
#         'get': 'retrieve',
#         'delete': 'destroy',
#         'put': 'update',
#         'patch': 'perform_update'
#     }))
# ]
