from django.urls import include, path

from src.apps.accounts.admin import petcare_admin_site

urlpatterns = [
    path("admin/", petcare_admin_site.urls),
    path("api/v1/auth/", include("dj_rest_auth.urls")),
    path("api/v1/auth/registration/", include("dj_rest_auth.registration.urls")),
    path("api/v1/accounts/", include("src.apps.accounts.urls")),
    path("api/v1/pets/", include("src.apps.pets.urls")),
    path("api/v1/health/", include("src.apps.health.urls")),
    path("api/v1/schedule/", include("src.apps.schedule.urls")),
    path("api/v1/store/", include("src.apps.store.urls")),
]
