#Define de no existir un listado con las referencias de las capas vectoriales para no perder sus referencias
if not "vlayers" in locals():
    vlayers=[]

#Define las constantes de conexión a base de datos
if not "db" in locals():
    db={"servidor":"leoviquez.com","puerto":"5432","baseDatos":"curso_gis","usuario":"gis","clave":"gis"}

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
    print (cLayer.crs().authid())
    selectList = []
    if cLayer:
        count = cLayer.selectedFeatureCount()
        print (count)
        selectedList = cLayer.selectedFeatures()
        print (selectedList)
        for f in selectedList:
            print (f.geometry().asJson())
            #print (f.geometry().area())
    for i in canvas.layers():
        if i.type() == i.VectorLayer:
            i.removeSelection()

def mostrarRutaLabTocomedor():
    uri = QgsDataSourceUri()
    uri.setConnection("leoviquez.com", "5432", "curso_gis", "gis", "gis")
    sql = """SELECT * FROM pgr_dijkstra(
      'SELECT id,source, target, distancia as cost FROM routing.aceras_completo',
      328, 359, directed => false) as r inner join routing.aceras_completo as a on (r.edge=a.id)"""
    uri.setDataSource("", "("+sql+")", "geom",  "", "id")
    vRuteo= QgsVectorLayer(uri.uri(False), "testlayer", "postgres")
    QgsProject.instance().addMapLayer(vRuteo)


    
#Ruta del proyecto actual
direccionProyecto=QgsProject.instance().readPath("./");

acciones["capaRutas"] = QAction(QIcon(direccionProyecto+"/autobus.png"),'Cargar rutas de buses')
acciones["capaRutas"].triggered.connect(lambda: cargarCapaPostgres(db["servidor"],db["puerto"],db["baseDatos"],db["usuario"],db["clave"],"routing","rutas_buses","geom"))

acciones["aceras"] = QAction(QIcon(direccionProyecto+"/acera.png"),'Cargar aceras del TEC')
acciones["aceras"].triggered.connect(lambda: cargarCapaPostgres(db["servidor"],db["puerto"],db["baseDatos"],db["usuario"],db["clave"],"routing","aceras_completo","geom"))

acciones["nodos"] = QAction(QIcon(direccionProyecto+"/nodos.png"),'Cargar nodos de enrutamiento de las aceras TEC')
acciones["nodos"].triggered.connect(lambda: cargarCapaPostgres(db["servidor"],db["puerto"],db["baseDatos"],db["usuario"],db["clave"],"routing","aceras_completo_vertices_pgr","the_geom"))

acciones["normalizar"] = QAction(QIcon(direccionProyecto+"/punto.png"),'Cargar aceras del TEC')
acciones["normalizar"].triggered.connect(normalizarRutas)

acciones["Listar elementos seleccionados"] = QAction(QIcon(direccionProyecto+"/json.png"),'Listar elementos seleccionados')
acciones["Listar elementos seleccionados"].triggered.connect(listar_geometrias_seleccionadas)

acciones["rutaComedor"] = QAction('Ruta al comedor')
acciones["rutaComedor"].triggered.connect(mostrarRutaLabTocomedor)

#Agregar elementos a la barra de herramientas 
iface.addToolBarIcon(acciones["capaRutas"])
iface.addToolBarIcon(acciones["aceras"])
iface.addToolBarIcon(acciones["nodos"])
iface.addToolBarIcon(acciones["normalizar"])
iface.addToolBarIcon(acciones["Listar elementos seleccionados"])
iface.addToolBarIcon(acciones["rutaComedor"])







