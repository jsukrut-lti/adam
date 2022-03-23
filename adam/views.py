import json
import re
from shapely.geometry import Point, Polygon
from django.shortcuts import render,redirect
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import AddressSerializers
from .models import PanelMaster
from geojson import Polygon
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
            items = PanelMaster.objects.filter(status='Active')[:50]
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
                    on panel.panel_no = translate(panel_st.player_no,panel_st.code||'-','') 
                    and panel_st.city = 'N. Charleston' limit 100
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
        # res = Polygon([[(-81.27058013661991, 35.294380959284894), (-81.19077879693572, 35.32694110417019), (-81.13713456303682, 35.30306494604871), (-81.2262460590176, 35.28026749345226)]])
        # print("*************", res)
        cods = request.POST.get('cods')
        min_lng = request.POST.get('min_lng')
        max_lng = request.POST.get('max_lng')
        min_lat = request.POST.get('min_lat')
        max_lat = request.POST.get('max_lat')
        print(min_lng, max_lng)
        result = PanelMaster.objects.filter(longitude__range=(min_lng, max_lng)
                                        # latitude__range=(min_lat, max_lat)
                                        ).values('longitude', 'latitude', 'city', 'state', 'country')
        # print(list(result))
        data = [{'longitude': '-79.955272', 'latitude': '32.837121', 'panel': '10710', 'market': 'charleston',
                 'mediatype': 'Bulletin'},
                {'longitude': '-79.978316', 'latitude': '32.851848', 'panel': '11520', 'market': 'charleston',
                 'mediatype': 'Poster'},
                {'longitude': '-79.986786', 'latitude': '32.847946', 'panel': 'P3716', 'market': 'charleston',
                 'mediatype': 'Poster'},
                {'longitude': '-79.967356', 'latitude': '32.841073', 'panel': '1245', 'market': 'charleston',
                 'mediatype': 'Bulletin'},
                {'longitude': '-79.944102', 'latitude': '32.797972', 'panel': '1012', 'market': 'charleston',
                'mediatype': 'Bulletin'}]

        return HttpResponse(json.dumps({'status': "success", "data": list(data)}), content_type="application/json")
    else:
        return HttpResponse(json.dumps({'status': "bad request"}), content_type="application/json")

