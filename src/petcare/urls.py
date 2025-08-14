from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("src.apps.accounts.urls")),
    path("api/v1/", include("src.apps.pets.urls")),
    path("api/v1/", include("src.apps.health.urls")),
    path("api/v1/", include("src.apps.schedule.urls")),
    path("api/v1/", include("src.apps.store.urls")),
]
