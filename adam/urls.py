from django.urls import path
from .views import AddressViewSet, AddressDetailsView

urlpatterns = [
    path('address-add/', AddressViewSet.as_view()),
    path('address-list/', AddressDetailsView.as_view())
]
