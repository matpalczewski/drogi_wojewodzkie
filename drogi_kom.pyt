# © 2023 Mateusz Palczewski <matpalczewski@gmail.com>

#Narzędzie przetestowane w oprogramowaniu ArcMap 10.8

import arcpy, fiona, os, overpy, pyproj, tempfile
import pandas as pd
from fiona.crs import from_epsg

class Toolbox(object):
    def __init__(self):
        self.label = 'Drogi (z komentarzem)'
        self.alias = 'Drogi (z komentarzem)'
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
        arcpy.AddField_management(drogi, 'nr', 'SHORT', 4) #pole (kolumna) dla numerów dróg w tworzonej warstwie z drogami
        arcpy.AddField_management(drogi, 'przebieg', 'TEXT', field_length = 150) #pole dla opisów przebiegu dróg (opisem są nazwy miast na drodze wymienione po przecinku w odpowiedniej kolejności)
        
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
        
        drogi_csv = pd.read_csv(plik_csv) #utworzenie tabeli w której wiersz reprezentuje jedną drogę, pierwsza komórka w wierszu zawiera numer drogi, a pozostałe komórki zawierają nazwy miast na drodze (jedno miasto w jednej komórce), liczba kolumn jest równa liczbie komórek w wierszu reprezentującym drogę z największą liczbą miast
        drogi_csv = drogi_csv.fillna('brak') #zastąpienie wartości NaN w pustych komórkach wartością do której łatwiej się odnieść w dalszej części kodu (drogi nie mają jednakowej liczby miast w swoim przebiegu stąd puste komórki
        
        for a in range(0, len(drogi_csv)): #a oznacza jedną drogę (tyle iteracji ile dróg)
            nr = int(drogi_csv.get_value(a, 0, takeable=True))
            przebieg = '' #zmienna do tworzenia opisów przebiegu dróg
            vertices = [] #tablica przechowująca punkty tworzące linię (drogę)
            for b in range(1, len(drogi_csv.columns)): #b oznacza jedno miasto na drodze (tyle iteracji ile miast na drodze)
                miasto = drogi_csv.get_value(a, b, takeable=True)
                if miasto != 'brak':
                    przebieg += '{}, '.format(miasto)
                    city = arcpy.da.SearchCursor(tempf, ['SHAPE@X', 'SHAPE@Y'], '"name" = \'{}\''.format(miasto), sr) #pozyskanie obiektów warstwy z miastami, których nazwa jest taka sama jak nazwa miasta w bieżącej iteracji
                    i = 0 #zmienna do zliczania miast
                    for c in city: #c oznacza jedno miasto, city może oznaczać jedno miasto (następuje wtedy tylko jedna iteracja, najczęstszy przypadek) albo miasta mające taką samą nazwę (obecnie co najwyżej dwa polskie miasta mogą nosić taką samą nazwę)
                        i += 1
                        vertices.append(arcpy.Point(c[0],c[1])) #lokalizacja miasta staje się punktem tworzącym linię
                        if i > 1:
                            nr *= 10 #tymczasowe pomnożenie numeru drogi, wyróżnienie dróg łączących miasta o tej samej nazwie (obecnie nie ma drogi wojewódzkiej w Polsce łączącej miasta o tej samej nazwie)
            if nr > 1000: #część kodu wykonywana dla dróg o zbyt dużej liczbie miast (dla dróg o pomnożonym numerze)
                nr /= 10
                for d in range(0, len(vertices)-1): #iteracje po segmentach linii (odcinkach drogi między dwoma kolejnymi miastami), d oznacza indeks punktu (miasta) będącego punktem początkowym segmentu
                    p = arcpy.PointGeometry(vertices[d], sr)
                    p1 = arcpy.PointGeometry(vertices[d+1], sr)
                    k, odl = p.angleAndDistanceTo(p1)
                    if odl > 100000: #jeśli długość segmentu linii jest większa niż 100000 m (100 km), segment jest tworzony przez nieprawidłowy punkt, ponieważ odległości między dwoma kolejnymi miastami na drodze są niewielkie i z pewnością nie przekraczają 100 km
                        #poniższe warunki wykrywają który punkt segmentu jest nieprawidłowy - początkowy (d) czy końcowy (d+1) - na podstawie odległości od prawidłowego punktu należącego do następnego segmentu (punkt o indeksie d+2); również wykorzystywana jest wartość 100000 m - jeśli odległość jest większa to znaczy, że jest mierzona od punktu prawidłowego do punktu nieprawidłowego
                        if d+2 < len(vertices): #w tym przypadku analizowana jest odległość od punktu o indeksie d+2
                            p2 = arcpy.PointGeometry(vertices[d+2], sr)
                            k, o = p2.angleAndDistanceTo(p)
                            if o > 100000: #jeśli bieżący segment jest pierwszym segmentem linii
                                vertices.pop(d) #usunięcie punktu będącego początkiem segmentu
                                break #przerwanie pętli - bieżąca linia nie będzie miała już nieprawidłowych punktów (w przypadku polskich miast)
                            else: #jeśli bieżący segment nie jest ostatnim segmentem linii
                                vertices.pop(d+1) #usunięcie punktu będącego końcem segmentu
                                break
                        else: #jeśli bieżący segment jest ostatnim segmentem linii (nie ma wtedy punktu o indeksie d+2)
                            vertices.pop(d+1)
                            break
            przebieg = przebieg[:-2] #usunięcie przecinka i spacji znajdujących się na końcu opisu przebiegu
            geometria = arcpy.Polyline(arcpy.Array(vertices)) #ostateczne utworzenie linii
            obiekt = arcpy.da.InsertCursor(drogi, ['nr', 'przebieg', 'SHAPE@'])
            obiekt.insertRow([nr, przebieg, geometria])
        
        del city, obiekt
        arcpy.DeleteField_management(drogi, 'Id')
        
        return
