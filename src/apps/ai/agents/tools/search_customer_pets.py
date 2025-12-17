from datetime import date

import structlog
from pydantic import BaseModel, Field

from src.apps.pets.models import Breed, Pet

logger = structlog.get_logger(__name__)


class SearchCustomerPetsTool(BaseModel):
    """Search for pets by species, breed, or age.

    This tool helps find the right pet when a customer mentions characteristics
    like breed, species, or age.
    """

    species: str | None = Field(
        default=None,
        description="Pet species: 'dog', 'cat', 'bird', or 'other' (Portuguese: cachorro, gato, pássaro)",
    )
    breed: str | None = Field(
        default=None,
        description="Breed name in Portuguese (e.g., 'golden retriever', 'poodle', 'siamês')",
    )
    age_min: int | None = Field(
        default=None,
        description="Minimum age in years",
    )
    age_max: int | None = Field(
        default=None,
        description="Maximum age in years",
    )
    customer_id: int | None = Field(
        default=None,
        description="Filter by specific customer ID if known",
    )


def search_customer_pets(
    species: str | None = None,
    breed: str | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
    customer_id: int | None = None,
) -> list[dict]:
    """Search for pets matching the criteria.

    Args:
        species: Pet species (dog, cat, bird, other)
        breed: Breed name (case-insensitive, partial match)
        age_min: Minimum age in years
        age_max: Maximum age in years
        customer_id: Filter by customer ID

    Returns:
        List of pets with their details
    """
    logger.info(
        "search_customer_pets_started",
        species=species,
        breed=breed,
        age_min=age_min,
        age_max=age_max,
        customer_id=customer_id,
    )

    queryset = Pet.objects.select_related("breed", "owner").all()

    if customer_id:
        queryset = queryset.filter(owner_id=customer_id)

    if species:
        species_map = {
            "cachorro": Breed.Species.DOG,
            "dog": Breed.Species.DOG,
            "gato": Breed.Species.CAT,
            "cat": Breed.Species.CAT,
            "pássaro": Breed.Species.BIRD,
            "passaro": Breed.Species.BIRD,
            "bird": Breed.Species.BIRD,
        }
        species_enum = species_map.get(species.lower())
        if species_enum:
            queryset = queryset.filter(breed__species=species_enum)

    if breed:
        queryset = queryset.filter(breed__name__icontains=breed)

    if age_min is not None or age_max is not None:
        today = date.today()
        for pet in queryset:
            if pet.birth_date:
                age = (
                    today.year
                    - pet.birth_date.year
                    - (
                        (today.month, today.day)
                        < (pet.birth_date.month, pet.birth_date.day)
                    )
                )
                if age_min is not None and age < age_min:
                    queryset = queryset.exclude(pk=pet.pk)
                if age_max is not None and age > age_max:
                    queryset = queryset.exclude(pk=pet.pk)

    pets = queryset[:5]

    results = []
    for pet in pets:
        pet_age = None
        if pet.birth_date:
            today = date.today()
            pet_age = (
                today.year
                - pet.birth_date.year
                - (
                    (today.month, today.day)
                    < (pet.birth_date.month, pet.birth_date.day)
                )
            )

        results.append(
            {
                "id": pet.id,
                "name": pet.name,
                "breed": pet.breed.name,
                "species": pet.breed.get_species_display(),
                "age": pet_age,
                "owner_name": pet.owner.full_name or pet.owner.user.username,
                "owner_id": pet.owner.id,
            }
        )

    logger.info("search_customer_pets_completed", results_count=len(results))
    return results
