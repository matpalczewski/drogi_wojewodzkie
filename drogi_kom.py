#Skrypt przetestowany w oprogramowaniu QGIS 3.28

from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (QgsProcessingAlgorithm,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFeatureSink,
                       QgsFields,
                       QgsField,
                       QgsWkbTypes,
                       QgsCoordinateReferenceSystem,
                       QgsVectorLayer,
                       QgsFeatureRequest,
                       QgsPoint,
                       QgsLineString,
                       QgsFeature)
import fiona, os, overpy, tempfile
import pandas as pd
from fiona.crs import from_epsg
from pyproj import Transformer

class Drogi(QgsProcessingAlgorithm):
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
    def createInstance(self):
        return Drogi()
    def name(self):
        return 'drogi_kom'
    def displayName(self):
        return self.tr('Drogi')
    def group(self):
        return self.tr('Drogi (z komentarzem)')
    def groupId(self):
        return 'drogi_kom'
    def shortHelpString(self):
        return self.tr('Narzędzie tworzące schematyczną warstwę dróg wojewódzkich')
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFile(
                'INPUT',
                self.tr('Plik CSV z wykazem dróg')
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'OUTPUT',
                self.tr('Nowa warstwa z drogami')
            )
        )
    
    def processAlgorithm(self, parameters, context, feedback):
        
        pola = QgsFields()
        pola.append(QgsField('nr', QVariant.Int, len=4)) #pole (kolumna) dla numerów dróg w tworzonej warstwie z drogami
        pola.append(QgsField('przebieg', QVariant.String, len=150)) #pole dla opisów przebiegu dróg (opisem są nazwy miast na drodze wymienione po przecinku w odpowiedniej kolejności)
        
        plik_csv = self.parameterAsFile(
            parameters,
            'INPUT',
            context
        )
        (drogi, drogi_id) = self.parameterAsSink(
            parameters,
            'OUTPUT',
            context,
            pola,
            QgsWkbTypes.LineString,
            QgsCoordinateReferenceSystem('EPSG:2180')
        )
        
        tempd = tempfile.mkdtemp()
        tempf = os.path.join(tempd, 'miasta.shp')
        schema = {'geometry': 'Point', 'properties': {'name': 'str:25'}}
        q = overpy.Overpass().query("""area["name"="Polska"];node["place"~"town|^city$"](area);out body;""")
        t = Transformer.from_crs(4326, 2180, always_xy=True)
        
        with fiona.open(tempf, 'w', crs=from_epsg(2180), driver='ESRI Shapefile', schema=schema, encoding='Windows-1250') as f:
            for n in q.nodes: #pozyskanie punktów (lokalizacji miast) z OpenStreetMap, n oznacza jeden punkt (tyle iteracji ile polskich miast)
                lon, lat = t.transform(n.lon, n.lat)
                punkt = {'type': 'Point', 'coordinates': (lon, lat)}
                prop = {'name': n.tags.get("name")}
                f.write({'geometry': punkt, 'properties': prop})
        
        drogi_csv = pd.read_csv(plik_csv, encoding='windows-1250') #utworzenie tabeli w której wiersz reprezentuje jedną drogę, pierwsza komórka w wierszu zawiera numer drogi, a pozostałe komórki zawierają nazwy miast na drodze (jedno miasto w jednej komórce), liczba kolumn jest równa liczbie komórek w wierszu reprezentującym drogę z największą liczbą miast
        drogi_csv = drogi_csv.fillna('brak') #zastąpienie wartości NaN w pustych komórkach wartością do której łatwiej się odnieść w dalszej części kodu (drogi nie mają jednakowej liczby miast w swoim przebiegu stąd puste komórki
        miasta = QgsVectorLayer(tempf)
        
        for a in range(0, len(drogi_csv)): #a oznacza jedną drogę (tyle iteracji ile dróg)
            nr = int(drogi_csv._get_value(a, 0, takeable=True))
            przebieg = '' #zmienna do tworzenia opisów przebiegu dróg
            vertices = [] #tablica przechowująca punkty tworzące linię (drogę)
            for b in range(1, len(drogi_csv.columns)): #b oznacza jedno miasto na drodze (tyle iteracji ile miast na drodze)
                miasto = drogi_csv._get_value(a, b, takeable=True)
                if miasto != 'brak':
                    przebieg += '{}, '.format(miasto)
                    city = miasta.getFeatures(QgsFeatureRequest().setFilterExpression('"name"=\'{}\''.format(miasto))) #pozyskanie obiektów warstwy z miastami, których nazwa jest taka sama jak nazwa miasta w bieżącej iteracji
                    i = 0 #zmienna do zliczania miast
                    for c in city: #c oznacza jedno miasto, city może oznaczać jedno miasto (następuje wtedy tylko jedna iteracja, najczęstszy przypadek) albo miasta mające taką samą nazwę (obecnie co najwyżej dwa polskie miasta mogą nosić taką samą nazwę)
                        i += 1
                        vertices.append(c.geometry().asPoint()) #lokalizacja miasta staje się punktem tworzącym linię
                        if i > 1:
                            nr *= 10 #tymczasowe pomnożenie numeru drogi, wyróżnienie dróg łączących miasta o tej samej nazwie (obecnie nie ma drogi wojewódzkiej w Polsce łączącej miasta o tej samej nazwie)
            if nr > 1000: #część kodu wykonywana dla dróg o zbyt dużej liczbie miast (dla dróg o pomnożonym numerze)
                nr /= 10
                for d in range(0, len(vertices)-1): #iteracje po segmentach linii (odcinkach drogi między dwoma kolejnymi miastami), d oznacza indeks punktu (miasta) będącego punktem początkowym segmentu
                    p = QgsPoint(vertices[d])
                    p1 = QgsPoint(vertices[d+1])
                    odl = p.distance(p1)
                    if odl > 100000: #jeśli długość segmentu linii jest większa niż 100000 m (100 km), segment jest tworzony przez nieprawidłowy punkt, ponieważ odległości między dwoma kolejnymi miastami na drodze są niewielkie i z pewnością nie przekraczają 100 km
                        #poniższe warunki wykrywają który punkt segmentu jest nieprawidłowy - początkowy (d) czy końcowy (d+1) - na podstawie odległości od prawidłowego punktu należącego do następnego segmentu (punkt o indeksie d+2); również wykorzystywana jest wartość 100000 m - jeśli odległość jest większa to znaczy, że jest mierzona od punktu prawidłowego do punktu nieprawidłowego
                        if d+2 < len(vertices): #w tym przypadku analizowana jest odległość od punktu o indeksie d+2
                            p2 = QgsPoint(vertices[d+2])
                            o = p2.distance(p)
                            if o > 100000: #jeśli bieżący segment jest pierwszym segmentem linii
                                vertices.pop(d) #usunięcie punktu będącego początkiem segmentu
                                break #przerwanie pętli - bieżąca linia nie będzie miała już nieprawidłowych punktów
                            else: #jeśli bieżący segment nie jest ostatnim segmentem linii
                                vertices.pop(d+1) #usunięcie punktu będącego końcem segmentu
                                break
                        else: #jeśli bieżący segment jest ostatnim segmentem linii (nie ma wtedy punktu o indeksie d+2)
                            vertices.pop(d+1)
                            break
            przebieg = przebieg[:-2] #usunięcie przecinka i spacji znajdujących się na końcu opisu przebiegu
            obiekt = QgsFeature()
            obiekt.setGeometry(QgsLineString(vertices)) #ostateczne utworzenie linii
            obiekt.setAttributes([nr, przebieg])
            drogi.addFeature(obiekt)
        
        return {'OUTPUT': drogi_id}