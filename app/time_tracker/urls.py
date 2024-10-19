from django.contrib import admin
from django.urls import path, include
from rest_framework.authentication import TokenAuthentication
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

schema_view = get_schema_view(
    openapi.Info(
        title="Work Logging API Documentation",  
        default_version="v1",
        description="This is documentation for the backend API",
    ),
    public=True,  
    permission_classes=(AllowAny,),
     
)

urlpatterns = [
    path('admin/', admin.site.urls),  
    path('', include('api.urls')),  
    # path('', include('worklog.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # path('api-docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api-docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='schema-swagger-ui'),
] 