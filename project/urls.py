# project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse   # <-- imported
from rest_framework.authtoken.views import obtain_auth_token

def root_view(request):
    return HttpResponse(
        "<h1>Chemical Equipment Parameter Visualizer API</h1>"
        "<p>Visit <a href='/api/'>/api/</a> for API root or <a href='/admin/'>/admin/</a>.</p>"
    )

urlpatterns = [
    path('', root_view, name='root'),
    path('admin/', admin.site.urls),

    # auth endpoint to obtain token (POST username & password -> returns token)
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),

    # api app endpoints
    path('api/', include('api.urls')),
]

# serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
