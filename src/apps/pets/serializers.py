from rest_framework import serializers

from .models import Breed, Pet


class BreedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Breed
        fields = "__all__"


class PetSerializer(serializers.ModelSerializer):
    breed = BreedSerializer(read_only=True)
    breed_id = serializers.PrimaryKeyRelatedField(
        queryset=Breed.objects.all(), source="breed", write_only=True
    )

    class Meta:
        model = Pet
        fields = ["id", "name", "breed", "breed_id", "birth_date", "owner"]
        read_only_fields = ["owner"]
