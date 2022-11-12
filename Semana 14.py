import psycopg2
#Define de no existir un listado con las referencias de las capas vectoriales para no perder sus referencias

if not "vlayers" in locals():
    vlayers=[]

#Define las constantes de conexión a base de datos
if not "db" in locals():
    db={"servidor":"localhost","puerto":"5432","baseDatos":"qgis_proyecto","usuario":"postgres","clave":"7201"}

#Define el listado de acciones por agregar a la barra de herramientas
if not "acciones" in locals():
    acciones={}

#Carga un acapa desde postgres    
def cargarCapaPostgres(servidor,puerto,baseDatos,usuario,clave,esquema,tabla,columnaGeografica):
    global vlayers
    uri = QgsDataSourceUri()
    #host name, port, database name, username and password
    uri.setConnection(servidor,puerto, baseDatos,usuario,clave)
    #database schema, table name, geometry column
    uri.setDataSource(esquema, tabla, columnaGeografica)
    #Crea la capa vectorial y almacena su referencia en la lista de capas vectoriales
    vlayers.append({"nombre":tabla,"capa":QgsVectorLayer(uri.uri(), tabla,"postgres")})
    layerTree = iface.layerTreeCanvasBridge().rootGroup()
    layerTree.insertChildNode(0,QgsLayerTreeLayer(vlayers[-1]["capa"]))

#Carga capa nueva en memoria para normalizar rutas
def normalizarRutas():
    global vlayers
    # creación de una nueva nuevas capas
    vl = QgsVectorLayer("Point", "Puntos de normalización", "memory")
    vlayers.append(vl)
    #Definición del sistema de referecias de coordenadas    
    crs=QgsCoordinateReferenceSystem()
    crs.createFromId(5367)
    vl.setCrs(crs)
    #Instanciación del proveedor de datos de la nueva capa
    pr=vl.dataProvider()
    #Adición de campos descriptivos para los objetos geográficos
    pr.addAttributes( [ QgsField("Nombre" ), QgsField("id",  QVariant.Int), QgsField("radio", QVariant.Double) ] )
    #Instanciación del grupo raíz del arbol de capas
    layerTree = iface.layerTreeCanvasBridge().rootGroup()
    #Inserción de la nueva capa en la pocisión 0 del panel de capas
    layerTree.insertChildNode(0, QgsLayerTreeLayer(vl))
    #Inico de edición de la capa
    vl.startEditing()
    #Agente renderizador de la capa
    r=vl.renderer()
    #Instancia Symbol que maneja en general el estilo de la capa
    s=r.symbol()
    #Asignar propiedades al simbolo de la capa actual
    s.setColor(QColor.fromRgb(55,128,100,100))
    #Asignación de la propiedad size en función de un dato calculado
    s.symbolLayer(0).setDataDefinedProperty(QgsSymbolLayer.PropertySize ,QgsProperty.fromField("radio"))
    #Definición de las unidades utilizadas para desplegar el tamaño del marcador
    s.setSizeUnit(QgsUnitTypes.RenderMetersInMapUnits)
    #Carga de archivo de estilos
    #vl.loadNamedStyle(QgsProject.instance().readPath("./")+"/estilo_puntos_normalizar.qml")
    #Creación de nuevos simbolos
    symbol = QgsGeometryGeneratorSymbolLayer.create({})
    symbol.setSymbolType(QgsSymbol.Marker)
    symbol.setGeometryExpression("centroid($geometry)")
    symbol.setColor(QColor('Blue'))
    s.insertSymbolLayer(1, symbol)
    #Refrescar la capa
    vl.triggerRepaint()

#Lista los elementos seleccionados en una capa en formato json
def listar_geometrias_seleccionadas():
    canvas = qgis.utils.iface.mapCanvas()
    canvas.currentLayer().selectAll()
    cLayer = canvas.currentLayer()
    
    # abrir capa de rutas_buses
    global vlayers
    vRutas = vlayers[0]["capa"]
    #vRutas.startEditing()
    

    connection = psycopg2.connect(user="postgres",
                                password="7201",
                                host="localhost",
                                port="5432",
                                database="qgis_proyecto")
    cursor = connection.cursor()

    selectList = []
    if cLayer:
        count = cLayer.selectedFeatureCount()
        selectedList = cLayer.selectedFeatures()
        for f in selectedList:
            geometria = f.geometry().asWkt()
            radio = f.attributes()[1] /2

            # idRuta, geomPunto, pathPunto
            sql = """select id, st_astext(geom), path from (select (ST_DumpPoints(geom)).geom, (ST_DumpPoints(geom)).path, id  FROM rutas_buses) as rb, 
                        (select st_buffer( ST_GeomFromText(%s, 5367) , %s)) as points 
                            where st_contains (points.st_buffer, rb.geom)"""
            
            data = (geometria, radio, )
            cursor.execute(sql, data)
            result = cursor.fetchall()
            #info de los vertices contenidos
            print(result)
            
            xPoint =  f.geometry().asPoint().x() 
            yPoint = f.geometry().asPoint().y()

            # hacer pero con los vertices de vRutas
            for i in result: 
                geom =  QgsGeometry.fromWkt(i[1])
                vIndex = i[2][1]
                geom.moveVertex(xPoint, yPoint, vIndex)

    for i in canvas.layers():
        if i.type() == i.VectorLayer:
            i.removeSelection()
    

    

# def mostrarRutaLabTocomedor():
#     uri = QgsDataSourceUri()
#     uri.setConnection("leoviquez.com", "5432", "curso_gis", "gis", "gis")
#     sql = """SELECT * FROM pgr_dijkstra(
#       'SELECT id,source, target, distancia as cost FROM routing.aceras_completo',
#       328, 359, directed => false) as r inner join routing.aceras_completo as a on (r.edge=a.id)"""
#     uri.setDataSource("", "("+sql+")", "geom",  "", "id")
#     vRuteo= QgsVectorLayer(uri.uri(False), "testlayer", "postgres")
#     QgsProject.instance().addMapLayer(vRuteo)


#Ruta del proyecto actual
direccionProyecto=QgsProject.instance().readPath("./");

acciones["capaRutas"] = QAction(QIcon(direccionProyecto+"/autobus.png"),'Cargar rutas de buses')
acciones["capaRutas"].triggered.connect(lambda: cargarCapaPostgres(db["servidor"],db["puerto"],db["baseDatos"],db["usuario"],db["clave"],"public","rutas_buses","geom"))

acciones["normalizar"] = QAction(QIcon(direccionProyecto+"/punto.png"),'Normalizar')
acciones["normalizar"].triggered.connect(normalizarRutas)

acciones["Listar elementos seleccionados"] = QAction(QIcon(direccionProyecto+"/json.png"),'Listar elementos seleccionados')
acciones["Listar elementos seleccionados"].triggered.connect(listar_geometrias_seleccionadas)


#Agregar elementos a la barra de herramientas 
iface.addToolBarIcon(acciones["capaRutas"])
iface.addToolBarIcon(acciones["normalizar"])
iface.addToolBarIcon(acciones["Listar elementos seleccionados"])


