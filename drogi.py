# © 2023 Mateusz Palczewski <matpalczewski@gmail.com>

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
        return 'drogi'
    def displayName(self):
        return self.tr('Drogi')
    def group(self):
        return self.tr('Drogi')
    def groupId(self):
        return 'drogi'
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
        pola.append(QgsField('nr', QVariant.Int, len=4))
        pola.append(QgsField('przebieg', QVariant.String, len=150))
        
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
            for n in q.nodes:
                lon, lat = t.transform(n.lon, n.lat)
                punkt = {'type': 'Point', 'coordinates': (lon, lat)}
                prop = {'name': n.tags.get("name")}
                f.write({'geometry': punkt, 'properties': prop})
        
        drogi_csv = pd.read_csv(plik_csv)
        drogi_csv = drogi_csv.fillna('brak')
        miasta = QgsVectorLayer(tempf)
        
        for a in range(len(drogi_csv)):
            nr = int(drogi_csv._get_value(a, 0, takeable=True))
            przebieg = ''
            vertices = []
            for b in range(1, len(drogi_csv.columns)):
                miasto = drogi_csv._get_value(a, b, takeable=True)
                if miasto != 'brak':
                    przebieg += '{}, '.format(miasto)
                    city = miasta.getFeatures(QgsFeatureRequest().setFilterExpression('"name"=\'{}\''.format(miasto)))
                    i = 0
                    for c in city:
                        i += 1
                        vertices.append(c.geometry().asPoint())
                        if i > 1:
                            nr *= 10
            if nr > 1000:
                nr /= 10
                for d in range(len(vertices)-1):
                    p = QgsPoint(vertices[d])
                    p1 = QgsPoint(vertices[d+1])
                    odl = p.distance(p1)
                    if odl > 100000:
                        if d+2 < len(vertices):
                            p2 = QgsPoint(vertices[d+2])
                            o = p2.distance(p)
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
            obiekt = QgsFeature()
            obiekt.setGeometry(QgsLineString(vertices))
            obiekt.setAttributes([nr, przebieg])
            drogi.addFeature(obiekt)
        
        return {'OUTPUT': drogi_id}
