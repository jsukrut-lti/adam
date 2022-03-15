from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import AddressSerializers
from .models import Address

# Create your views here.


class AddressViewSet(APIView):

    def post(self, request):
        serilalizer = AddressSerializers(data=request.data)
        if serilalizer.is_valid():
            serilalizer.save()
            return Response({"result": "success", "data": serilalizer.data,
                             "status": status.HTTP_200_OK})
        else:
            return Response({"result": "error", "data": serilalizer.errors,
                             "status": status.HTTP_400_BAD_REQUEST})


class AddressDetailsView(APIView):

    def get(self, request):
        item = Address.objects.filter(postal_code=request.GET['post_code'])
        serializer = AddressSerializers(item, many=True)
        if item:
            return Response({"result": "success",
                             "data": list(serializer.data),
                             "status": status.HTTP_200_OK})
        elif not item:
            items = Address.objects.filter(enable=True)
            serializer = AddressSerializers(items, many=True)
            if items:
                return Response({"result": "success",
                                 "data": list(serializer.data),
                                 "status": status.HTTP_200_OK})
            else:
                return Response({"result": "Data Not founded"})
        else:
            return Response({"result": "Data Not founded"})


def create_address_view(request):
    return render(request, 'adam/create_address.html')


def view_address(request):
    return render(request, 'adam/view_address.html')


def find_address(request):
    return render(request, 'adam/find_address.html')
