from django.urls import path
from .views import ChatAPIView

urlpatterns = [
    path('studio/', ChatAPIView.as_view(), name='studio'),
    # path('trim/', TrimAPIView.as_view(), name='trim_api'),
]
