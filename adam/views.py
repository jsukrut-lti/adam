import json
import re
# from shapely.geometry import Point, Polygon
from django.shortcuts import render,redirect
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import AddressSerializers
from .models import PanelMaster, SpatialPolygon
# from geojson import Polygon
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
cursor = connection.cursor()
from django.contrib.gis.geos.polygon import Polygon
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
        cods = request.POST.get('cods')
        cods = json.loads(cods)
        # geo_polygon = Polygon(( (0.0, 0.0), (0.0, 50.0), (50.0, 50.0), (50.0, 0.0), (0.0, 0.0) ))

        geo_polygon = Polygon((
            (cods[0][0], cods[0][1]),
            (cods[1][0], cods[1][1]),
            (cods[2][0], cods[2][1]),
            (cods[3][0], cods[3][1]),
            (cods[4][0], cods[4][1]),
            (cods[0][0], cods[0][1])
        ), srid=4326)
        poly = SpatialPolygon.objects.create(poly=geo_polygon)
        poly.save()
        # filter = geo_polygon.within(SpatialPanel.objects.all())
        # query = SpatialPanel.objects.filter(points__contains=geo_polygon)
        # query = SpatialPanel.objects.all()
        query = '''SELECT ST_X(point.points) AS x,
                    ST_Y(point.points) AS y,
                    ST_AsText(point.points) AS xy 
                    FROM public."adam_spatialpoint" point, public."adam_spatialpolygon" polygon
                    WHERE ST_Contains(polygon.poly, point.points) and polygon.id = {}
                '''.format(poly.id)
        cursor.execute(query)

        res = list()
        for q in cursor.fetchall():
            co = dict()
            co['longitude'] = q[0]
            co['latitude'] = q[1]
            res.append(co)
        return HttpResponse(json.dumps({'status': "success", "data": res}), content_type="application/json")
    else:
        return HttpResponse(json.dumps({'status': "bad request"}), content_type="application/json")

