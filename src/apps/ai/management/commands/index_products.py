"""Management command to index all products in vector store."""

import structlog
from django.core.management.base import BaseCommand

from src.apps.ai.services import ProductIntelligenceService
from src.apps.store.models import Product

logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    help = "Index all products in vector store for RAG"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force reindex all products even if already indexed",
        )

    def handle(self, *args, **options):
        service = ProductIntelligenceService()
        products = Product.objects.all()

        self.stdout.write(f"Indexing {products.count()} products...")

        success_count = 0
        error_count = 0

        for i, product in enumerate(products, 1):
            try:
                service.index_product(product)
                success_count += 1

                if i % 10 == 0:
                    self.stdout.write(f"Indexed {i}/{products.count()}")

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"Error indexing product {product.id} ({product.name}): {str(e)}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Successfully indexed {success_count}/{products.count()} products"
            )
        )

        if error_count > 0:
            self.stdout.write(self.style.WARNING(f"❌ {error_count} errors occurred"))
