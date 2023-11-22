# © 2023 Mateusz Palczewski <matpalczewski@gmail.com>

import arcpy, fiona, os, overpy, pyproj, tempfile
import pandas as pd
from fiona.crs import from_epsg

class Toolbox(object):
    def __init__(self):
        self.label = 'Drogi'
        self.alias = 'Drogi'
        self.tools = [Drogi]

class Drogi(object):
    
    def __init__(self):
        self.label = 'Drogi'
        self.description = 'Narzędzie tworzące schematyczną warstwę dróg wojewódzkich'.decode('utf8').encode('cp1250')
        self.canRunInBackground = False
    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName='Plik CSV z wykazem dróg'.decode('utf8').encode('cp1250'),
            name='csv',
            datatype='DETextfile',
            parameterType='Required',
            direction='Input')
        param1 = arcpy.Parameter(
            displayName='Nowa warstwa z drogami',
            name='drogi',
            datatype='GPFeatureLayer',
            parameterType='Required',
            direction='Output')
        params = [param0, param1]
        return params
    def isLicensed(self):
        return True
    def updateParameters(self, parameters):
        return
    def updateMessages(self, parameters):
        return
    
    def execute(self, parameters, messages):
        
        plik_csv = parameters[0].valueAsText
        drogi = parameters[1].valueAsText
        
        sr = arcpy.SpatialReference(2180)
        arcpy.CreateFeatureclass_management(os.path.dirname(drogi), os.path.basename(drogi), 'POLYLINE', spatial_reference = sr)
        arcpy.AddField_management(drogi, 'nr', 'SHORT', 4)
        arcpy.AddField_management(drogi, 'przebieg', 'TEXT', field_length = 150)
        
        tempd = tempfile.mkdtemp()
        tempf = os.path.join(tempd, 'miasta.shp')
        schema = {'geometry': 'Point', 'properties': {'name': 'str:25'}}
        q = overpy.Overpass().query("""area["name"="Polska"];node["place"~"town|^city$"](area);out body;""")
        
        with fiona.open(tempf, 'w', crs=from_epsg(2180), driver='ESRI Shapefile', schema=schema, encoding='Windows-1250') as f:
            for n in q.nodes: #pozyskanie punktów (lokalizacji miast) z OpenStreetMap, n oznacza jeden punkt (tyle iteracji ile polskich miast)
                lon, lat = pyproj.transform(pyproj.Proj(init='epsg:4326'), pyproj.Proj(init='epsg:2180'), n.lon, n.lat)
                punkt = {'type': 'Point', 'coordinates': (lon, lat)}
                prop = {'name': n.tags.get("name")}
                f.write({'geometry': punkt, 'properties': prop})
        
        drogi_csv = pd.read_csv(plik_csv)
        drogi_csv = drogi_csv.fillna('brak')
        
        for a in range(0, len(drogi_csv)):
            nr = int(drogi_csv.get_value(a, 0, takeable=True))
            przebieg = ''
            vertices = []
            for b in range(1, len(drogi_csv.columns)):
                miasto = drogi_csv.get_value(a, b, takeable=True)
                if miasto != 'brak':
                    przebieg += '{}, '.format(miasto)
                    city = arcpy.da.SearchCursor(tempf, ['SHAPE@X', 'SHAPE@Y'], '"name" = \'{}\''.format(miasto), sr)
                    i = 0
                    for c in city:
                        i += 1
                        vertices.append(arcpy.Point(c[0],c[1]))
                        if i > 1:
                            nr *= 10
            if nr > 1000:
                nr /= 10
                for d in range(0, len(vertices)-1):
                    p = arcpy.PointGeometry(vertices[d], sr)
                    p1 = arcpy.PointGeometry(vertices[d+1], sr)
                    k, odl = p.angleAndDistanceTo(p1)
                    if odl > 100000:
                        if d+2 < len(vertices):
                            p2 = arcpy.PointGeometry(vertices[d+2], sr)
                            k, o = p2.angleAndDistanceTo(p)
                            if o > 100000:
                                vertices.pop(d)
                                break
                            else:
                                vertices.pop(d+1)
                                break
                        else:
                            vertices.pop(d+1)
                            break
            przebieg = przebieg[:-2]
            geometria = arcpy.Polyline(arcpy.Array(vertices))
            obiekt = arcpy.da.InsertCursor(drogi, ['nr', 'przebieg', 'SHAPE@'])
            obiekt.insertRow([nr, przebieg, geometria])
        
        del city, obiekt
        arcpy.DeleteField_management(drogi, 'Id')
        
        return
