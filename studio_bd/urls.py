from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

# Simple home view to serve the root URL
def home(request):
    return HttpResponse("🚀 Studio Fliplora is live!")

urlpatterns = [
    path('', home, name='home'),  # Root URL now responds with 200 OK
    path('admin/', admin.site.urls),
    path('ex/', include('studio.urls')),  # Adjust if you meant something else
    path('api/', include('api_studio.urls')),
]
