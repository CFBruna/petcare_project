import random
from datetime import time, timedelta
from decimal import Decimal

import structlog
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone
from faker import Faker

from src.apps.accounts.models import Customer
from src.apps.accounts.tests.factories import CustomerFactory
from src.apps.pets.models import Pet
from src.apps.pets.tests.factories import PetFactory
from src.apps.schedule.models import Appointment, Service, TimeSlot
from src.apps.schedule.services import AppointmentService
from src.apps.schedule.tests.factories import AppointmentFactory, ServiceFactory
from src.apps.store.models import (
    Brand,
    Category,
    Product,
    ProductLot,
    Promotion,
    PromotionRule,
    Sale,
    SaleItem,
)
from src.apps.store.tests.factories import (
    BrandFactory,
    CategoryFactory,
)

logger = structlog.get_logger(__name__)
fake = Faker("pt_BR")


REALISTIC_PRODUCT_NAMES = [
    "Ração Premium para Cães Adultos 15kg",
    "Ração Filhotes Raças Pequenas 3kg",
    "Ração Gatos Castrados Salmão 10kg",
    "Ração Especial para Filhotes 7.5kg",
    "Ração Super Premium Frango e Arroz 20kg",
    "Ração Hipoalergênica para Cães Sensíveis 12kg",
    "Ração Gatos Adultos Mix de Peixes 8kg",
    "Petisco Natural de Frango Desidratado 200g",
    "Osso de Couro Bovino para Cães",
    "Bifinho de Carne Bovina 500g",
    "Snack Dental para Cães Adultos",
    "Petisco Freeze Dried de Salmão para Gatos 50g",
    "Shampoo Antipulgas e Carrapatos 500ml",
    "Condicionador Hidratante para Pelos Longos 500ml",
    "Tapete Higiênico Super Absorvente 30un",
    "Lenços Umedecidos Pet Fresh 100un",
    "Escova de Dentes Pet com Cerdas Macias",
    "Perfume Colônia Pet Lavanda 120ml",
    "Lixa para Unhas de Gatos",
    "Bolinha de Borracha Resistente Grande",
    "Corda de Algodão Trançada para Cães",
    "Arranhador de Sisal com Bolinha Suspensa",
    "Pelúcia Mordedor com Som",
    "Bola Dispenser de Petiscos",
    "Varinha com Penas para Gatos",
    "Frisbee Flutuante para Cães",
    "Coleira Ajustável Nylon Refletiva P/M/G",
    "Guia Retrátil Automática 5 metros",
    "Cama Ortopédica Cinza com Memory Foam",
    "Comedouro Duplo Inox Antiaderente",
    "Bebedouro Fonte Automática 3 Litros",
    "Caixa de Transporte Tamanho M Resistente",
    "Peitoral Anti-Puxão Ajustável",
    "Antipulgas Spot On para Cães 10-25kg",
    "Vermífugo Comprimido Sabor Carne 4 doses",
    "Suplemento Vitamínico para Articulações",
    "Pomada Cicatrizante Veterinária 30g",
    "Colírio Oftálmico Lubrificante 10ml",
    "Sabonete Antisséptico para Pets 90g",
    "Anti-inflamatório Natural para Cães",
    "Areia Higiênica Perfumada para Gatos 4kg",
    "Granulado Sanitário Biodegradável 6kg",
    "Bandeja Sanitária Fechada com Filtro",
]


@shared_task
@transaction.atomic
def simulate_daily_activity(
    num_customers: int = 5,
    num_products: int = 3,
    num_lots_per_product: int = 2,
    num_sales: int = 5,
    num_appointments: int = 7,
    num_manual_promotions: int = 2,
    num_health_records: int = 4,
) -> str:
    """
    Simulates daily activity in the PetCare system by creating random data.
    This includes new customers, products, lots, sales, appointments, promotions, and health records.
    """
    results = []
    today = timezone.now().date()

    for day in range(5):
        TimeSlot.objects.get_or_create(
            day_of_week=day,
            start_time=time(8, 0),
            defaults={"end_time": time(20, 0)},
        )
    results.append("Horários de funcionamento (Seg-Sex, 08h-20h) garantidos.")

    yesterday = timezone.now() - timedelta(days=1)

    new_customers = CustomerFactory.create_batch(num_customers)
    results.append(f"Created {len(new_customers)} new customers.")

    new_products = []
    if not Category.objects.exists():
        CategoryFactory.create_batch(3)
    if not Brand.objects.exists():
        BrandFactory.create_batch(3)

    used_product_names = set(Product.objects.values_list("name", flat=True))
    created_count = 0

    existing_categories = list(Category.objects.all())
    existing_brands = list(Brand.objects.all())

    for _ in range(num_products):
        for _ in range(10):
            product_name = random.choice(REALISTIC_PRODUCT_NAMES)

            if product_name not in used_product_names:
                product = Product.objects.create(
                    name=product_name,
                    sku=fake.ean8(),
                    barcode=fake.ean13(),
                    brand=random.choice(existing_brands),
                    category=random.choice(existing_categories),
                    description=fake.paragraph(),
                    price=Decimal(random.uniform(10.00, 300.00)).quantize(
                        Decimal("0.01")
                    ),
                )

                used_product_names.add(product_name)
                new_products.append(product)
                created_count += 1

                for _ in range(num_lots_per_product):
                    expiration_delta = random.randint(1, 180)
                    lot = ProductLot.objects.create(
                        product=product,
                        lot_number=fake.bothify(text="???-####").upper(),
                        quantity=random.randint(10, 50),
                        expiration_date=today + timedelta(days=expiration_delta),
                    )

                    if random.random() < 0.3:
                        lot.expiration_date = today + timedelta(
                            days=random.randint(1, 30)
                        )
                        lot.save()

                results.append(
                    f"Created product '{product.name}' with {num_lots_per_product} lots."
                )
                break

    existing_customers = list(Customer.objects.all())
    existing_lots = list(ProductLot.objects.filter(quantity__gt=0))

    if not existing_customers:
        existing_customers = CustomerFactory.create_batch(5)
    if not existing_lots:
        product = Product.objects.create(
            name=random.choice(REALISTIC_PRODUCT_NAMES),
            sku=fake.ean8(),
            barcode=fake.ean13(),
            brand=random.choice(existing_brands),
            category=random.choice(existing_categories),
            description=fake.paragraph(),
            price=Decimal(random.uniform(10.00, 300.00)).quantize(Decimal("0.01")),
        )
        existing_lots = [
            ProductLot.objects.create(
                product=product,
                lot_number=fake.bothify(text="???-####").upper(),
                quantity=random.randint(10, 50),
                expiration_date=today + timedelta(days=random.randint(30, 180)),
            )
            for _ in range(5)
        ]

    created_sales_count = 0
    for _ in range(num_sales):
        if not existing_customers or not existing_lots:
            break

        customer = random.choice(existing_customers)
        sale = Sale.objects.create(customer=customer, created_at=yesterday)
        total_sale_value = Decimal("0.00")

        num_items = random.randint(1, 3)
        for _ in range(num_items):
            lot = random.choice(existing_lots)
            if lot.quantity > 0:
                quantity_to_sell = random.randint(1, min(lot.quantity, 3))
                unit_price = lot.final_price
                SaleItem.objects.create(
                    sale=sale,
                    lot=lot,
                    quantity=quantity_to_sell,
                    unit_price=unit_price,
                )

                lot.quantity = F("quantity") - quantity_to_sell
                lot.save(update_fields=["quantity"])
                lot.refresh_from_db(fields=["quantity"])

                total_sale_value += unit_price * quantity_to_sell

        sale.total_value = total_sale_value
        sale.save()
        created_sales_count += 1

    results.append(f"Created {created_sales_count} sales for yesterday.")

    existing_pets = list(Pet.objects.all())
    existing_services = list(Service.objects.all())

    if not existing_pets:
        if not Customer.objects.exists():
            CustomerFactory.create_batch(5)
        existing_pets = PetFactory.create_batch(5)

    if not existing_services:
        existing_services.extend(ServiceFactory.create_batch(3))

    all_available_slots = []
    if existing_services:
        # Obter slots disponíveis para todos os serviços
        for day_offset in range(8):
            appointment_date = today + timedelta(days=day_offset)
            for service in existing_services:
                slots_for_day = AppointmentService.get_available_slots(
                    appointment_date, service
                )
                for slot_datetime in slots_for_day:
                    # Verificar se o horário + tempo de serviço não ultrapassa o horário de funcionamento
                    end_time = slot_datetime + timedelta(
                        minutes=service.duration_minutes
                    )
                    close_time = timezone.make_aware(
                        timezone.datetime.combine(appointment_date, time(20, 0))
                    )
                    if end_time <= close_time:
                        # Armazenar junto com o serviço correspondente
                        all_available_slots.append((slot_datetime, service))

    occupied_times = set(
        Appointment.objects.filter(
            schedule_time__in=[slot[0] for slot in all_available_slots]
        ).values_list("schedule_time", flat=True)
    )

    # Remover slots já ocupados
    available_slots_with_service = [
        (slot, service)
        for slot, service in all_available_slots
        if slot not in occupied_times
    ]

    # Separar appointments para hoje para garantir pelo menos 2 confirmados
    today_appointments = [
        (slot, service)
        for slot, service in available_slots_with_service
        if slot.date() == today
    ]
    other_appointments = [
        (slot, service)
        for slot, service in available_slots_with_service
        if slot.date() != today
    ]

    created_appointments_count = 0
    # Forçar a criação de 2 agendamentos confirmados para hoje para garantir a consistência do teste
    if existing_pets and existing_services:
        # Garante que o horário de funcionamento de hoje existe
        TimeSlot.objects.get_or_create(
            day_of_week=today.weekday(),
            start_time=time(8, 0),
            defaults={"end_time": time(20, 0)},
        )

        for i in range(2):
            pet = random.choice(existing_pets)
            service = random.choice(existing_services)
            # Usar horários fixos para evitar colisões e garantir a criação
            schedule_time = timezone.make_aware(
                timezone.datetime.combine(today, time(9 + i, 0))
            )

            # Criar apenas se o slot não estiver ocupado
            if not Appointment.objects.filter(schedule_time=schedule_time).exists():
                AppointmentFactory(
                    pet=pet,
                    service=service,
                    status=Appointment.Status.CONFIRMED,
                    schedule_time=schedule_time,
                )
                created_appointments_count += 1

    # Combinar agendamentos restantes
    remaining_slots_with_service = today_appointments + other_appointments
    random.shuffle(remaining_slots_with_service)

    for _ in range(num_appointments - created_appointments_count):
        if (
            not remaining_slots_with_service
            or not existing_pets
            or not existing_services
        ):
            break

        schedule_time, service = remaining_slots_with_service.pop()
        pet = random.choice(existing_pets)

        status = random.choices(
            [
                Appointment.Status.PENDING,
                Appointment.Status.CONFIRMED,
                Appointment.Status.COMPLETED,
                Appointment.Status.CANCELED,
            ],
            weights=[0.3, 0.4, 0.2, 0.1],
            k=1,
        )[0]

        appointment = AppointmentFactory(
            pet=pet, service=service, status=status, schedule_time=schedule_time
        )

        if status == Appointment.Status.COMPLETED:
            # Verificar se o horário de conclusão não ultrapassa o horário de funcionamento
            close_time = timezone.make_aware(
                timezone.datetime.combine(schedule_time.date(), time(20, 0))
            )
            calculated_completion = schedule_time + timedelta(
                minutes=service.duration_minutes
            )
            # Definir o horário de conclusão como o menor entre o cálculo e o horário de fechamento
            actual_completion = min(calculated_completion, close_time)
            appointment.completed_at = actual_completion
            appointment.save()

        created_appointments_count += 1

    results.append(f"Created {created_appointments_count} appointments.")

    from src.apps.health.tests.factories import HealthRecordFactory

    created_health_records = 0
    if existing_pets:
        for _ in range(num_health_records):
            pet = random.choice(existing_pets)
            HealthRecordFactory(pet=pet)
            created_health_records += 1

    results.append(f"Created {created_health_records} health records.")

    existing_lots_for_promo = list(ProductLot.objects.filter(quantity__gt=0))
    created_promotions_count = 0

    for _ in range(num_manual_promotions):
        if not existing_lots_for_promo:
            break

        promotion = Promotion.objects.create(
            name=f"Promoção {fake.catch_phrase()}",
            start_date=timezone.now() - timedelta(days=random.randint(0, 3)),
            end_date=timezone.now() + timedelta(days=random.randint(7, 20)),
        )

        num_rules = random.randint(1, 2)
        for _ in range(num_rules):
            lot_for_rule = random.choice(existing_lots_for_promo)
            if lot_for_rule.quantity > 0:
                PromotionRule.objects.create(
                    promotion=promotion,
                    lot=lot_for_rule,
                    discount_percentage=Decimal(random.choice([15, 25, 35])),
                    promotional_stock=random.randint(1, min(lot_for_rule.quantity, 10)),
                )

        created_promotions_count += 1

    results.append(f"Created {created_promotions_count} manual promotions.")

    apply_expiration_discounts.delay()
    results.append("Triggered automatic expiration discounts task.")

    return "\n".join(results)


@shared_task
@transaction.atomic
def apply_expiration_discounts() -> str:
    """
    Applies automatic discounts to product lots nearing expiration.
    Fixed discount rules:
    - Less than 7 days: 30% discount
    - 7-15 days: 20% discount
    - 15-30 days: 10% discount
    - More than 30 days: No discount
    """
    today = timezone.now().date()
    updated_count = 0

    discount_rules = [
        (7, Decimal("30.00")),
        (15, Decimal("20.00")),
        (30, Decimal("10.00")),
    ]

    lots = ProductLot.objects.filter(
        expiration_date__isnull=False,
        expiration_date__gte=today,
        quantity__gt=0,
    )

    for lot in lots:
        days_until_expiration = (lot.expiration_date - today).days
        new_discount = Decimal("0.00")

        for days_threshold, discount_percentage in discount_rules:
            if days_until_expiration <= days_threshold:
                new_discount = discount_percentage
                break

        if lot.auto_discount_percentage != new_discount:
            lot.auto_discount_percentage = new_discount
            lot.save(update_fields=["auto_discount_percentage"])
            updated_count += 1

    return f"{updated_count} lotes tiveram seu desconto por validade atualizado."


@shared_task
def generate_daily_sales_report() -> str:
    """
    Generates a daily sales report for the previous day.
    """
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)

    sales = Sale.objects.filter(created_at__date=yesterday)
    total_revenue = sales.aggregate(total=Sum("total_value"))["total"] or 0

    if not sales.exists():
        subject = f"Relatório Diário de Vendas - {yesterday.strftime('%d/%m/%Y')}"
        message = "Nenhuma venda foi realizada nesta data."
    else:
        subject = f"Relatório Diário de Vendas - {yesterday.strftime('%d/%m/%Y')} ({sales.count()} vendas)"
        report_lines = [
            f"Relatório de vendas realizadas em {yesterday.strftime('%d/%m/%Y')}",
            "-" * 40,
        ]

        for sale in sales:
            customer_name = sale.customer.full_name or sale.customer.user.username
            sale_time = timezone.localtime(sale.created_at).strftime("%H:%M")
            report_lines.append(
                f"- {sale_time}h | Cliente: {customer_name} | Total: R$ {sale.total_value:.2f}"
            )

        report_lines.append("-" * 40)
        report_lines.append(f"Faturamento Total do Dia: R$ {total_revenue:.2f}")
        message = "\n".join(report_lines)

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        settings.ADMIN_EMAIL,
        fail_silently=False,
    )

    return f"Relatório de vendas para {yesterday.strftime('%d/%m/%Y')} enviado com sucesso."


@shared_task
def generate_daily_promotions_report() -> str:
    """
    Generates a daily report on active promotions.
    """
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)

    active_promotions = Promotion.objects.filter(
        start_date__lte=yesterday,
        end_date__gte=yesterday,
    ).prefetch_related("rules__lot__product")

    if not active_promotions.exists():
        subject = f"Relatório Diário de Promoções - {yesterday.strftime('%d/%m/%Y')}"
        message = "Nenhuma promoção ativa nesta data."
    else:
        subject = f"Relatório Diário de Promoções - {yesterday.strftime('%d/%m/%Y')} ({active_promotions.count()} promoções)"
        report_lines = [
            f"Relatório de promoções ativas em {yesterday.strftime('%d/%m/%Y')}",
            "-" * 40,
        ]

        for promo in active_promotions:
            report_lines.append(f"Promoção: {promo.name}")
            report_lines.append(f"  Vigência: {promo.start_date} até {promo.end_date}")

            for rule in promo.rules.all():
                product_name = rule.lot.product.name
                discount = rule.discount_percentage
                stock = rule.promotional_stock
                report_lines.append(
                    f"  - {product_name}: {discount}% desconto | Estoque promocional: {stock} unidades"
                )

            report_lines.append("-" * 40)

        message = "\n".join(report_lines)

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        settings.ADMIN_EMAIL,
        fail_silently=False,
    )

    return f"Relatório de promoções para {yesterday.strftime('%d/%m/%Y')} enviado com sucesso."
