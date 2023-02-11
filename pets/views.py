
from rest_framework.views import APIView, Request, Response, status
from django.shortcuts import render
from .models import Pet
from groups.models import Group
from traits.models import Trait
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404
from pets.serializers import PetSerializer
from rest_framework.pagination import PageNumberPagination


class PetView(APIView, PageNumberPagination):
    def get(self, request: Request) -> Response:
        pets = Pet.objects.all()
        result_page = self.paginate_queryset(pets, request, view=self)

        serializer = PetSerializer(result_page, many=True)

        return self.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:

        serializer = PetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        group_list = serializer.validated_data.pop("group")
        traits_list = serializer.validated_data.pop("traits")

        group_obj = Group.objects.filter(
            scientific_name__iexact=group_list["scientific_name"]
        ).first()

        if not group_obj:
            group_obj = Group.objects.create(**group_list)

        pet: Pet = Pet.objects.create(
            **serializer.validated_data, group=group_obj)

        for trait_dict in traits_list:
            trait_obj = Trait.objects.filter(
                name__iexact=trait_dict["name"]
            ).first()

            if not trait_obj:
                trait_obj = Trait.objects.create(**trait_dict)

            pet.traits.add(trait_obj)

        serializer = PetSerializer(pet)

        return Response(serializer.data, 201)


class PetDetailView(APIView):
    def get(self, request: Request):

        trait = request.query_params.get("traits", None)

        pets = Pet.objects.filter(
            trait_name=trait
        )

        serializer = PetSerializer(pets, many=True)

        return Response(serializer.data)

    def get(self, request: Request, pet_id):

        pet = Pet.objects.get(pk=pet_id)

        serializer = PetSerializer(pet)

        return Response(serializer.data, status.HTTP_200_OK)

    def patch(self, request: Request, pet_id: int) -> Response:

        pet = get_object_or_404(Pet, id=pet_id)
        serializer = PetSerializer(data=request.data, partial=True)

        serializer.is_valid(raise_exception=True)

        for key, value in serializer.validated_data.items():
            setattr(pet, key, value)

        pet.save()

        serializer = PetSerializer(pet)

        return Response(serializer.data)

    def delete(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)

        pet.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
