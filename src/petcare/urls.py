from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/accounts/", include("src.apps.accounts.urls")),
    path("api/v1/pets/", include("src.apps.pets.urls")),
    path("api/v1/health/", include("src.apps.health.urls")),
    path("api/v1/schedule/", include("src.apps.schedule.urls")),
    path("api/v1/store/", include("src.apps.store.urls")),
]
