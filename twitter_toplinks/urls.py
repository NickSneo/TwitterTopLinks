
from django.contrib import admin
from django.urls import path, include
from toplinks.views import home, loginUser, logoutUser

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name="home"),
    path('loginUser/', loginUser, name="loginUser"),
    path('logoutUser/', logoutUser, name="logoutUser"),
    path('oauth/', include('social_django.urls', namespace='social')),
]
