from datetime import timedelta

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User
from django.db.models import Sum
from django.db.models.functions import TruncDay
from django.utils import timezone
from django_celery_beat.models import (
    ClockedSchedule,
    CrontabSchedule,
    IntervalSchedule,
    PeriodicTask,
    SolarSchedule,
)
from rest_framework.authtoken.models import TokenProxy

from src.apps.health.admin import HealthRecordAdmin
from src.apps.health.models import HealthRecord
from src.apps.pets.admin import BreedAdmin, PetAdmin
from src.apps.pets.models import Breed, Pet
from src.apps.schedule.admin import AppointmentAdmin, ServiceAdmin, TimeSlotAdmin
from src.apps.schedule.models import Appointment, Service, TimeSlot
from src.apps.store.admin import (
    AutoPromotionAdmin,
    BrandAdmin,
    CategoryAdmin,
    ProductAdmin,
    ProductLotAdmin,
    PromotionAdmin,
    SaleAdmin,
)
from src.apps.store.models import (
    AutoPromotion,
    Brand,
    Category,
    Product,
    ProductLot,
    Promotion,
    Sale,
    SaleItem,
)

from .models import Customer


class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    list_display = ("username", "email", "first_name", "last_name", "is_staff")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")


class CustomGroupAdmin(GroupAdmin):
    pass


class CustomerAdmin(admin.ModelAdmin):
    list_display = ["user", "cpf", "phone", "address"]
    search_fields = ["user__username", "cpf"]


class PetCareAdminSite(admin.AdminSite):
    site_header = "Administração PetCare"
    site_title = "Painel PetCare"
    index_title = "Bem-vindo ao Painel de Controle PetCare"
    index_template = "admin/dashboard.html"

    def index(self, request, extra_context=None):
        now = timezone.now()
        today = now.date()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        start_of_week = today - timedelta(days=6)

        sales_today = Sale.objects.filter(created_at__range=(start_of_day, end_of_day))
        revenue_today = sales_today.aggregate(total=Sum("total_value"))["total"] or 0

        appointments_today = Appointment.objects.filter(
            schedule_time__date=today, status=Appointment.Status.CONFIRMED
        ).count()

        revenue_by_day = (
            Sale.objects.filter(created_at__date__gte=start_of_week)
            .annotate(day=TruncDay("created_at"))
            .values("day")
            .annotate(total=Sum("total_value"))
            .order_by("day")
        )

        chart_data = {
            (start_of_week + timedelta(days=i)).strftime("%d/%m"): 0 for i in range(7)
        }
        for entry in revenue_by_day:
            chart_data[entry["day"].strftime("%d/%m")] = float(entry["total"])

        top_products_today = (
            SaleItem.objects.filter(sale__in=sales_today)
            .values("lot__product__name")
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold")[:5]
        )

        context = {
            **self.each_context(request),
            "title": self.index_title,
            "revenue_today": revenue_today,
            "appointments_today": appointments_today,
            "chart_labels": list(chart_data.keys()),
            "chart_values": list(chart_data.values()),
            "top_products": top_products_today,
        }

        return super().index(request, extra_context=context)

    def get_app_list(self, request, app_label=None):
        app_dict = self._build_app_dict(request)

        ordering = {
            "Vendas e Estoque": 1,
            "Agendamentos": 2,
            "Cadastros Gerais": 3,
            "Marketing e Promoções": 4,
            "Administração do Sistema": 5,
        }

        cadastros_gerais_models = []
        marketing_models = []

        if "accounts" in app_dict:
            cadastros_gerais_models.extend(app_dict.pop("accounts")["models"])
        if "pets" in app_dict:
            cadastros_gerais_models.extend(app_dict.pop("pets")["models"])
        if "health" in app_dict:
            cadastros_gerais_models.extend(app_dict.pop("health")["models"])

        store_app = app_dict.get("store")
        if store_app:
            marketing_models.extend(
                [
                    m
                    for m in store_app["models"]
                    if m["object_name"] in ["Promotion", "AutoPromotion"]
                ]
            )
            store_app["models"] = [
                m
                for m in store_app["models"]
                if m["object_name"] not in ["Promotion", "AutoPromotion"]
            ]
            store_app["name"] = "Vendas e Estoque"

        if "schedule" in app_dict:
            app_dict["schedule"]["name"] = "Agendamentos"

        if "auth" in app_dict:
            app_dict["auth"]["name"] = "Administração do Sistema"
            app_dict["auth"]["models"] = [
                m
                for m in app_dict["auth"]["models"]
                if m["object_name"] in ["User", "Group"]
            ]

        app_list = list(app_dict.values())
        if cadastros_gerais_models:
            app_list.append(
                {
                    "name": "Cadastros Gerais",
                    "app_label": "cadastros_gerais",
                    "models": sorted(cadastros_gerais_models, key=lambda x: x["name"]),
                }
            )
        if marketing_models:
            app_list.append(
                {
                    "name": "Marketing e Promoções",
                    "app_label": "marketing",
                    "models": sorted(marketing_models, key=lambda x: x["name"]),
                }
            )

        app_list.sort(key=lambda x: (ordering.get(x["name"], 99), x["name"]))

        return app_list


petcare_admin_site = PetCareAdminSite(name="petcare_admin")


admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
admin.site.unregister(EmailAddress)
admin.site.unregister(SocialApp)
admin.site.unregister(SocialAccount)
admin.site.unregister(SocialToken)
admin.site.unregister(PeriodicTask)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(SolarSchedule)
admin.site.unregister(ClockedSchedule)

petcare_admin_site.register(User, CustomUserAdmin)
petcare_admin_site.register(Group, CustomGroupAdmin)
petcare_admin_site.register(Customer, CustomerAdmin)
petcare_admin_site.register(HealthRecord, HealthRecordAdmin)
petcare_admin_site.register(Pet, PetAdmin)
petcare_admin_site.register(Breed, BreedAdmin)
petcare_admin_site.register(Appointment, AppointmentAdmin)
petcare_admin_site.register(Service, ServiceAdmin)
petcare_admin_site.register(TimeSlot, TimeSlotAdmin)
petcare_admin_site.register(Sale, SaleAdmin)
petcare_admin_site.register(Product, ProductAdmin)
petcare_admin_site.register(ProductLot, ProductLotAdmin)
petcare_admin_site.register(Category, CategoryAdmin)
petcare_admin_site.register(Brand, BrandAdmin)
petcare_admin_site.register(Promotion, PromotionAdmin)
petcare_admin_site.register(AutoPromotion, AutoPromotionAdmin)
