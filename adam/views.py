import json
from django.shortcuts import render,redirect
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import AddressSerializers
from .models import PanelMaster
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
cursor = connection.cursor()
# Create your views here.


class AddressViewSet(APIView):

    def post(self, request):
        print(request.data)
        serilalizer = AddressSerializers(data=request.data, many=True)
        if serilalizer.is_valid():
            serilalizer.save()
            return Response({"result": "success", "data": serilalizer.data,
                             "status": status.HTTP_200_OK})
        else:
            return Response({"result": "error", "data": serilalizer.errors,
                             "status": status.HTTP_400_BAD_REQUEST})


class AddressDetailsView(APIView):

    def get(self, request):
        item = PanelMaster.objects.filter(postal_code=request.GET['post_code'])
        serializer = AddressSerializers(item, many=True)
        if item:
            return Response({"result": "success",
                             "data": list(serializer.data),
                             "status": status.HTTP_200_OK})
        elif not item:
            items = PanelMaster.objects.filter(enable=True)
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
    if request.user.is_authenticated:
        address_data = []
        query = '''select panel.panel_no,panel_st.player_no,panel.latitude,panel.longitude,panel.market_name,
                    panel_st.submarket,panel_st.media_type,panel_st.unit_type,
                    panel.status,panel_st.description,panel_st.code,
                    panel_st.city,panel_st.site,panel_st.wk4_imp,
                    translate(panel_st.player_no,panel_st.code||'-','') as panel_st_panel_code
                    from adam_panelstaticdetails panel_st
                    join adam_panelmaster panel
                    on panel.panel_no = translate(panel_st.player_no,panel_st.code||'-','') limit 100
                '''
        cursor.execute(query)
        if (cursor.rowcount > 0):
            for row in cursor.fetchall():
                record = {}
                record['panel_no'] = row[0]
                record['player_no'] = row[1]
                record['market_name'] = row[4]
                record['longitude'] = row[3]
                record['latitude'] = row[2]
                record['description'] = row[9]
                record['city'] = row[11]

                address_data.append(record)

        print(address_data)
        context = {
                    'user_id': request.user.id,
                    'address_data': address_data
                }

        return render(request, 'adam/view_address.html', context)
    return redirect('login')



def find_address(request):
    return render(request, 'adam/find_address.html')


@csrf_exempt
def create_address(request):
    if request.method == 'POST' and request.is_ajax():
        obj = PanelMaster()
        obj.address_title = request.POST.get('address_title')
        obj.address_type = request.POST.get('address_type')
        obj.address_line1 = request.POST.get('address_line1')
        obj.address_line2 = request.POST.get('address_line2')
        obj.city = request.POST.get('city')
        obj.state = request.POST.get('state')
        obj.country = request.POST.get('country')
        obj.latitude = request.POST.get('latitude')
        obj.longitude = request.POST.get('longitude')
        obj.save()
        # serilalizer = AddressSerializers(data=request.POST)
        # if serilalizer.is_valid():
        #      serilalizer.save()
        #      print("saved")
        # else:
        #      print("not valid")
        return HttpResponse(json.dumps({'status': "success"}), content_type="application/json")
    else:
        return HttpResponse(json.dumps({'status': "bad request"}), content_type="application/json")

@csrf_exempt
def check_area(request):
    if request.method == 'POST' and request.is_ajax():
        min_lng = request.POST.get('min_lng')
        max_lng = request.POST.get('max_lng')
        min_lat = request.POST.get('min_lat')
        max_lat = request.POST.get('max_lat')
        result = PanelMaster.objects.filter(longitude__range=(min_lng, max_lng)
                                        # latitude__range=(min_lat, max_lat)
                                        ).values('longitude', 'latitude', 'city', 'state', 'country')
        print(list(result))
        data = [{'longitude': '77.29972607572665', 'latitude': '13.200179182144382'}, {'longitude': '76.88224560697597', 'latitude': '13.028982684247879'}]
        return HttpResponse(json.dumps({'status': "success", "data": list(result)}), content_type="application/json")
    else:
        return HttpResponse(json.dumps({'status': "bad request"}), content_type="application/json")

