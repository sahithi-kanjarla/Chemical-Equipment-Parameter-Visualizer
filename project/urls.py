# project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

# JWT Authentication Views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Optional: DRF Token obtain endpoint (legacy)
from rest_framework.authtoken.views import obtain_auth_token


def root_view(request):
    return HttpResponse(
        "<h1>Chemical Equipment Parameter Visualizer API</h1>"
        "<p>Visit <a href='/api/'>/api/</a> for API root or "
        "<a href='/admin/'>/admin/</a>.</p>"
    )


urlpatterns = [
    path('', root_view, name='root'),

    # Django Admin Panel
    path('admin/', admin.site.urls),

    # ---- JWT Authentication Endpoints ----
    # POST username + password → returns access + refresh tokens
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),

    # POST refresh token → returns new access token
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ---- Legacy DRF Token endpoint (optional) ----
    # POST username + password -> returns {"token": "<token>"} (uncomment in settings REST_FRAMEWORK to accept TokenAuthentication)
    path('api/api-token-auth/', obtain_auth_token, name='api_token_auth'),

    # ---- Your application API ----
    path('api/', include('api.urls')),
]

# Serve media files in development (uploaded CSVs)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
