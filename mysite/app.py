from flask import Flask, render_template, redirect , request, url_for, flash, session
from flask_toastr import Toastr
from flask_sqlalchemy import SQLAlchemy
from entidades import app, db
from scrap import buscarRUC, buscarRUCAPI
from fahp import generate_dataset, generate_results
from datetime import datetime
import numpy as np

from key_generator.key_generator import generate
import entidades as mdl
'''
#CONFIG
#app = Flask(__name__)
#app.config["DEBUG"] = True

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="root",
    password="#Rfrr19072002",
    hostname="localhost",
    databasename="upcisitp$tp",
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


#db = SQLAlchemy(app)
#db.init_app(app)
'''


app.config['WTF_CSRF_ENABLED'] = False
toast = Toastr(app)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.app_context().push()

#VIEWS
@app.route('/generate-key', methods=["GET"])
def generate_key():
    key = generate(4,'-',7,7).get_key()
    #print(key)
    user = mdl.user(
        userKey=key, 
        descUser = ""
    )
    db.session.add(user)
    db.session.commit()
    
    return redirect(url_for('mantenimiento'))

@app.route('/', methods=["GET"])
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=["GET"])
def login():
    if session.get("const_user") is None:
        session['const_nombre'] = ""
        session['const_estado'] = ""
        session['const_habido'] = ""
        session['const_direccion'] = ""
        session['const_ruc_search'] = ""

        '''
        session['const_sector'] = ""
        session['const_proveedor_seleccionado'] = ""
        session['const_resultados_general_proveedores'] = ""
        session['const_resultados_general_puntajes'] = ""
        session['const_user'] = ""
        session['const_sesion'] = ""
        session['const_sesion_sector'] = ""
        '''
        return render_template("login.html")
    else:
        return redirect(url_for('mantenimiento'))

@app.route('/logout', methods=["GET"])
def logout():
    session.pop("const_user", default=None)
    session.pop("const_sesion", default=None)
    session.pop("const_sesion_sector", default=None)
    session['const_nombre'] = ""
    session['const_estado'] = ""
    session['const_habido'] = ""
    session['const_direccion'] = ""
    session['const_ruc_search'] = ""
    #COMENTflash({'title': "Sesion cerrada exitosamente"}, 'success')
    return render_template("login.html")

@app.route('/mantenimiento', methods=["GET"])
def mantenimiento():
    if session.get("const_user") is None: 
        flash({'title': "Error: Acceso denegado", 'message': "Inicia sesión antes de continuar"}, 'error')
        return redirect(url_for('login'))

    #Vars
    const_user = session.get("const_user")

    lst_sector = mdl.sector_criterio.query.filter_by(idUser = const_user).all()
    lst_criterio = mdl.criterio.query.filter_by(idUser = const_user).order_by(mdl.criterio.idSector, mdl.criterio.idCriterio).all()
    lst_opcion = mdl.opcion_criterio.query.filter_by(idUser = const_user).order_by(mdl.opcion_criterio.idCriterio, mdl.opcion_criterio.numOpcion).all()

    return render_template("mantenimiento.html", 
    l_sector = lst_sector,
    l_criterio = lst_criterio,
    l_opcion = lst_opcion
    )

@app.route('/criterios_proveedores', methods=["GET"])
def criterios_proveedores():
    if session.get("const_user") is None: 
        flash({'title': "Error: Acceso denegado", 'message': "Inicia sesión antes de continuar"}, 'error')
        return redirect(url_for('login'))

    #Vars
    const_user = session.get("const_user")
    const_sesion = session.get("const_sesion")
    
    lst_sector = mdl.sector_criterio.query.filter_by(idUser = const_user).all()
    lst_prioridad = mdl.prioridad_criterio.query.filter_by(idSesion = const_sesion).all()
    lst_proveedor = mdl.proveedor.query.filter_by(idUser = const_user).all()

    const_sesion_sector = 0 if session.get("const_sesion_sector") is None else session.get("const_sesion_sector")
    lst_criterio = mdl.criterio.query.filter_by(idUser = const_user, idSector = const_sesion_sector).all()

    return render_template("criterios_proveedores.html", 
        l_sector = lst_sector,
        l_criterio = lst_criterio,
        l_prioridad = lst_prioridad,
        l_proveedor = lst_proveedor,
        sel_sector = int(const_sesion_sector),
        nombreRUC = session.get("const_nombre"),
        estadoRUC = session.get("const_estado"),
        habidoRUC = session.get("const_habido"),
        direcRUC = session.get("const_direccion"),
        rucSearch = session.get("const_ruc_search")
    )

@app.route('/puntaje-criterios', methods=["GET"])
def puntaje_criterios():
    if session.get("const_user") is None: 
        flash({'title': "Error: Acceso denegado", 'message': "Inicia sesión antes de continuar"}, 'error')
        return redirect(url_for('login'))
    
    if session.get("const_sesion") is None: 
        flash({'title': "Advertencia: Sector no establecido", 'message': "Establece un sector para el análisis antes de continuar"}, 'warning')
        return redirect(url_for('mantenimiento'))
    
    #Vars
    const_user = session.get("const_user")
    const_sesion = session.get("const_sesion")
    const_proveedor_seleccionado = session.get("const_proveedor_seleccionado")

    criterios_activos = mdl.prioridad_criterio.query.filter_by(idSesion=const_sesion).all()
    lst_sector = mdl.sector_criterio.query.filter_by(idUser = const_user).all()
    lst_criterio = mdl.criterio.query.filter_by(idUser = const_user).all()
    lst_opcion = mdl.opcion_criterio.query.filter_by(idUser = const_user).all()
    lst_proveedor = mdl.proveedor.query.filter_by(idUser = const_user).all()

    if len(criterios_activos) == 0:
        flash({'title': "Error: Criterios insuficientes", 'message': "Al menos debe existir un criterio con una prioridad asignada antes de continuar"}, 'error')
        return redirect(url_for('criterios_proveedores')) 
    
    if len(lst_proveedor) == 0:
        flash({'title': "Error: Proveedores insuficientes", 'message': "Al menos debe existir un proveedor registrado antes de continuar"}, 'error')
        return redirect(url_for('criterios_proveedores')) 

    for crit in criterios_activos:
        cnt_opciones = len(mdl.opcion_criterio.query.filter_by(idCriterio=crit.idCriterio).all())
        if cnt_opciones == 0:
            flash({'title': "Error: Criterios sin opciones", 'message': "Asegúrese que todos los criterios cuentan con al menos una opción antes de continuar"}, 'error')
            return redirect(url_for('criterios_proveedores')) 
        
        goto_prioridad = mdl.prioridad_criterio.query.filter_by(idSesion = const_sesion, idCriterio = crit.idCriterio).first()
        print("PRIORIDAD" + str(goto_prioridad) + "|" + str(goto_prioridad.idPrioridad) + "|" + str(goto_prioridad.criterio.strCriterio))
        for prov in lst_proveedor:
            flgEvaluacionExists = mdl.evaluacion_proveedor.query.filter_by(idSesion = const_sesion, idProveedor = prov.idProveedor, idPrioridad = goto_prioridad.idPrioridad).first()
            if flgEvaluacionExists is None:
                print("RESETED")
                reset_eva_criterio(prov.idProveedor, crit.idCriterio)

    if const_proveedor_seleccionado is None: sel_prov = ""
    else:
        _aux_prov = mdl.proveedor.query.filter_by(idUser = const_user, idProveedor = const_proveedor_seleccionado).first()
        if _aux_prov is None: sel_prov = ""
        else: sel_prov = _aux_prov.rucProveedor + " - " + _aux_prov.strNombre

    flg_prov_evaluado = mdl.evaluacion_proveedor.query.filter_by(idProveedor = const_proveedor_seleccionado, idSesion = const_sesion).first() is not None

    if flg_prov_evaluado: 
        lst_prioridad = mdl.evaluacion_proveedor.query.filter_by(idProveedor = const_proveedor_seleccionado, idSesion = const_sesion).all()
    else:
        lst_prioridad = mdl.prioridad_criterio.query.filter_by(idSesion = const_sesion).all()

    lst_evaluaciones = mdl.evaluacion_proveedor.query.filter_by(idSesion = const_sesion).all()

    return render_template("puntaje_criterios.html", 
        l_sector = lst_sector,
        l_criterio = lst_criterio,
        l_prioridad = lst_prioridad,
        l_proveedor = lst_proveedor,
        l_opcion = lst_opcion,
        sel_prov = sel_prov,
        flg_menu = flg_prov_evaluado,
        l_evaluacion = lst_evaluaciones
    )

@app.route('/resultados', methods=["GET"])
def resultados():
    if session.get("const_user") is None: 
        flash({'title': "Error: Acceso denegado", 'message': "Inicia sesión antes de continuar"}, 'error')
        return redirect(url_for('login'))
    
    if session.get("const_sesion") is None: 
        flash({'title': "Advertencia: Sector no establecido", 'message': "Establece un sector para el análisis antes de continuar"}, 'warning')
        return redirect(url_for('mantenimiento'))

    #Vars
    const_user = session.get("const_user")
    const_sesion = session.get("const_sesion")
    criterios_activos = mdl.prioridad_criterio.query.filter_by(idSesion=const_sesion).all()
    lst_proveedor = mdl.proveedor.query.filter_by(idUser = const_user).all()

    if len(criterios_activos) == 0:
        flash({'title': "Error: Criterios insuficientes", 'message': "Al menos debe existir un criterio con una prioridad asignada antes de continuar"}, 'error')
        return redirect(url_for('criterios_proveedores')) 
    
    if len(lst_proveedor) == 0:
        flash({'title': "Error: Proveedores insuficientes", 'message': "Al menos debe existir un proveedor registrado antes de continuar"}, 'error')
        return redirect(url_for('criterios_proveedores')) 

    for crit in criterios_activos:
        cnt_opciones = len(mdl.opcion_criterio.query.filter_by(idCriterio=crit.idCriterio).all())
        if cnt_opciones == 0:
            flash({'title': "Error: Criterios sin opciones", 'message': "Asegúrese que todos los criterios cuentan con al menos una opción antes de continuar"}, 'error')
            return redirect(url_for('criterios_proveedores')) 
        
        goto_prioridad = mdl.prioridad_criterio.query.filter_by(idSesion = const_sesion, idCriterio = crit.idCriterio).first()
        print("PRIORIDAD" + str(goto_prioridad) + "|" + str(goto_prioridad.idPrioridad) + "|" + str(goto_prioridad.criterio.strCriterio))
        for prov in lst_proveedor:
            flgEvaluacionExists = mdl.evaluacion_proveedor.query.filter_by(idSesion = const_sesion, idProveedor = prov.idProveedor, idPrioridad = goto_prioridad.idPrioridad).first()
            if flgEvaluacionExists is None:
                print("RESETED")
                reset_eva_criterio(prov.idProveedor, crit.idCriterio)
    
    #len_ev = len(mdl.evaluacion_proveedor.query.filter_by(idSesion = const_sesion).all())
    #if(len_ev < 1): return redirect(url_for('puntaje_criterios'))

    #FAHP
    #testing();
    #
    len_prov = len(mdl.proveedor.query.filter_by(idUser = const_user).all())

    puntajes_por_criterio = {}
    prioridades_criterios = []

    fahp_resultados_general_proveedores = [''] * len_prov
    fahp_resultados_general_puntajes = [0] * len_prov

    evaluaciones = mdl.evaluacion_proveedor.query.filter_by(idSesion = const_sesion).all()

    for eva in evaluaciones:
        if eva.opcion.criterio.idCriterio not in puntajes_por_criterio:
            puntajes_por_criterio[eva.opcion.criterio.idCriterio] = {'descripcion': eva.opcion.criterio.strCriterio, 'puntajes': []}

        puntajes_por_criterio[eva.opcion.criterio.idCriterio]['puntajes'].append(
            {
                'proveedor': eva.proveedor.rucProveedor + " - " + eva.proveedor.strNombre,
                'puntaje': float(eva.opcion.numOpcion)
            }
        )

    for criterio, data in puntajes_por_criterio.items():
        print("criterio: " + str(criterio))
        priori = mdl.prioridad_criterio.query.filter_by(idCriterio = criterio, idSesion = const_sesion).first()
        print("OBTENIDO: " + str(priori.numPrioridad))
        prioridades_criterios.append(priori.numPrioridad)

    print("_RES: " + str(generate_dataset(prioridades_criterios)))
    print("_RES: " + str(generate_results(prioridades_criterios)))
    rs_prioridades = generate_results(prioridades_criterios)

    idc = 0
    for criterio, data in puntajes_por_criterio.items():
        #Recorrer criterios
        descripcion = data['descripcion']
        puntajes = data['puntajes']
        lista_de_puntajes = []
            
        for puntaje_info in puntajes:
            lista_de_puntajes.append(puntaje_info['puntaje'])
        
        #
        print("_RES: " + str(generate_dataset(lista_de_puntajes)))
        rs_general = generate_results(lista_de_puntajes)
        print("RES" + descripcion + ": ||| " + str(rs_general))
        for idx, puntaje_info in enumerate(puntajes):
            fahp_resultados_general_proveedores[idx] = puntaje_info['proveedor']
            fahp_resultados_general_puntajes[idx] += rs_general[0][idx] * rs_prioridades[0][idc] * 100
        
        idc+=1

    print("LLEGO")
    print(fahp_resultados_general_proveedores)
    print(fahp_resultados_general_puntajes)


    #
    #
    #const_resultados_general_proveedores = session.get("const_resultados_general_proveedores")
    #const_resultados_general_puntajes = session.get("resultados_general_puntajes")

    print("PART 2")

    pts =  [round(num, 2) for num in fahp_resultados_general_puntajes]
    lst_out = list(zip(fahp_resultados_general_proveedores,pts))
    etiqueta_maxima = max(lst_out, key=lambda x: x[1])

    # Renderiza el gráfico en HTML y pasa el objeto Figure de Matplotlib
    return render_template("resultados.html", 
        rs_prov = lst_out,
        #plot = fig,
        prov_fin = etiqueta_maxima)

#######ACTIONS#######
@app.route('/insert-key', methods=["POST"])
def insert_key():
    user = mdl.user.query.filter_by(userKey = request.form["txt-key"]).first();

    if user: 
        #Crear sesion
        session['const_user'] = user.idUser
        #COMENTflash({'title': "Sesion iniciada exitosamente"}, 'success')
        #Login
        return redirect(url_for('mantenimiento'))
    else: 
        flash({'title': "Error: Clave no válida", 'message': "Ingrese una clave de acceso existente"}, 'error')
        return redirect(url_for('login'))
    
##SECTOR
@app.route('/add-sesion', methods=["POST"])
def add_sesion():
    try:
        const_user = session.get("const_user")
        in_sector = request.form["cbx-sel-sesion-sector"]
        sesion = mdl.sesion(
            fecSesion = datetime.now(),
            idSector = in_sector,
            idUser = const_user
        )

        n_sector = mdl.sector_criterio.query.filter_by(idUser = const_user, idSector = in_sector).first()
        db.session.add(sesion)
        db.session.commit()

        session["const_sesion"] = sesion.idSesion
        session["const_sesion_sector"] = in_sector

        #COMENTflash({'title': 'Sector "' + str(n_sector.strSector) + '" establecido'}, 'success')
        return redirect(url_for('criterios_proveedores'))
    except:
        flash({'title': "Error: Sector no válido", 'message': "Es necesario registrar previamente un sector"}, 'error')
        return redirect(url_for('criterios_proveedores'))

@app.route('/add-sector', methods=["POST"])
def add_sector():
    const_user = session.get("const_user")
    in_sector = request.form["txt-add-sector"].strip()
    flgExists = mdl.sector_criterio.query.filter_by(idUser = const_user, strSector = in_sector).first()

    if flgExists is None:
        sector = mdl.sector_criterio(
            strSector = in_sector,
            idUser = const_user
        )

        db.session.add(sector)
        db.session.commit()
        #COMENTflash({'title': "Sector añadido exitosamente"}, 'success')
    else:
        flash({'title': "Este sector ya se encuentra registrado"}, 'warning')

    return redirect(url_for('mantenimiento'))

@app.route('/edit-sector/<id>', methods=["GET","POST"])
def edit_sector(id):
    const_user = session.get("const_user")
    in_sector = request.form["txt-strSector"].strip()
    flgExists = mdl.sector_criterio.query.filter_by(idUser = const_user, strSector = in_sector).first()
    
    if flgExists is None:
        sector = mdl.sector_criterio.query.filter_by(idSector = id).first()
        sector.strSector = in_sector

        db.session.commit()
        #COMENTflash({'title': "Sector modificado exitosamente"}, 'success')
    else:
        if int(flgExists.idSector) != int(id):
            flash({'title': "Este sector ya se encuentra registrado"}, 'warning')
        else:
            sector = mdl.sector_criterio.query.filter_by(idSector = id).first()
            sector.strSector = in_sector

            db.session.commit()            
    
    return redirect(url_for('mantenimiento'))

@app.route('/delete-sector/<id>', methods=["GET","POST"])
def delete_sector(id):
    mdl.sector_criterio.query.filter_by(idSector = id).delete()

    if session.get("const_sesion_sector") is not None:
        if session.get("const_sesion_sector") == id:
            session.pop("const_sesion", default=None)
            session.pop("const_sesion_sector", default=None)

    db.session.commit()
    #COMENTflash({'title': "Sector eliminado exitosamente"}, 'success')
    return redirect(url_for('mantenimiento'))

#CRITERIO
@app.route('/add-criterio', methods=["POST"])
def add_criterio():
    const_user = session.get("const_user")

    try:
        in_criterio = request.form["txt-add-criterio"].strip()
        in_sector = request.form["cbx-add-sector"].strip()
        flgExists = mdl.criterio.query.filter_by(idUser = const_user, idSector = in_sector, strCriterio = in_criterio).first()
        session["const_ult_sector"] = int(in_sector)

        if flgExists is None:
            criterio = mdl.criterio(
                strCriterio = in_criterio, 
                idSector = in_sector,
                idUser = const_user
            )
            
            db.session.add(criterio)
            db.session.commit()
            #COMENTflash({'title': "Criterio añadido exitosamente"}, 'success')
        else:
            flash({'title': "Este criterio ya se encuentra registrado para este sector"}, 'warning')

        return redirect(url_for('mantenimiento'))
    
    except:
        flash({'title': "Error: Sector no válido", 'message': "Es necesario registrar previamente al menos un sector"}, 'error')
        return redirect(url_for('mantenimiento'))   

@app.route('/edit-criterio/<id>', methods=["GET","POST"])
def edit_criterio(id):
    const_user = session.get("const_user")
    in_criterio = request.form["txt-edit-criterio-strCriterio"].strip()
    in_sector = request.form["cbx-edit-criterio-idSector"].strip()
    flgExists = mdl.criterio.query.filter_by(idUser = const_user, idSector = in_sector, strCriterio = in_criterio).first()

    if flgExists is None:
        criterio = mdl.criterio.query.filter_by(idCriterio = id).first()
        criterio.idSector = in_sector
        criterio.strCriterio = in_criterio
        #COMENTflash({'title': "Criterio modificado exitosamente"}, 'success')

        db.session.commit()
    else:
        if int(flgExists.idCriterio) != int(id):
            flash({'title': "Este criterio ya se encuentra registrado para este sector"}, 'warning')
        else:
            criterio = mdl.criterio.query.filter_by(idCriterio = id).first()
            criterio.idSector = in_sector
            criterio.strCriterio = in_criterio

            db.session.commit()
    
    return redirect(url_for('mantenimiento'))

@app.route('/delete-criterio/<id>', methods=["GET","POST"])
def delete_criterio(id):
    mdl.criterio.query.filter_by(idCriterio = id).delete()
    
    db.session.commit()
    #COMENTflash({'title': "Criterio eliminado exitosamente"}, 'success')
    return redirect(url_for('mantenimiento'))

#OPCION CRITERIO
@app.route('/add-opcion-criterio', methods=["POST"])
def add_opcion_criterio():
    const_user = session.get("const_user")

    try:   
        in_criterio = request.form["cbx-add-criterio"].strip()
        in_opcion = request.form["txt-add-opcion-str"].strip()
        flgExists = mdl.opcion_criterio.query.filter_by(idUser = const_user, idCriterio = in_criterio, strOpcion = in_opcion).first()
        session["const_ult_criterio"] = int(in_criterio)

        if flgExists is None:
            opc_criterio = mdl.opcion_criterio(
                strOpcion = in_opcion, 
                idCriterio = in_criterio,
                numOpcion = request.form["txt-add-opcion-num"],
                idUser = const_user
            )
            db.session.add(opc_criterio)
            db.session.commit()
            #COMENTflash({'title': "Opción añadida exitosamente"}, 'success')
        else:
            flash({'title': "Esta opcion ya se encuentra registrada para este criterio"}, 'warning')

        return redirect(url_for('mantenimiento'))
    
    except:
        flash({'title': "Error: Opción de criterio no válida", 'message': "Es necesario registrar previamente un criterio"}, 'error')
        return redirect(url_for('mantenimiento'))

@app.route('/edit-opcion-criterio/<id>', methods=["GET","POST"])
def edit_opcion_criterio(id):
    const_user = session.get("const_user")
    in_criterio = request.form["cbx-edit-opcion-idCriterio"].strip()
    in_opcion = request.form["txt-edit-opcion-strOpcion"].strip()
    in_num_opcion = request.form["txt-edit-opcion-numOpcion"]
    flgExists = mdl.opcion_criterio.query.filter_by(idUser = const_user, idCriterio = in_criterio, strOpcion = in_opcion).first()
    flgExists2 = mdl.opcion_criterio.query.filter_by(idUser = const_user, idCriterio = in_criterio, strOpcion = in_opcion, numOpcion = in_num_opcion).first()
    opc_criterio = mdl.opcion_criterio.query.filter_by(idOpcion = id).first()

    if flgExists is not None:#Existe combinacion Criterio-strOpcion
        if int(flgExists.idOpcion) != int(id):
            flash({'title': "Esta opcion ya se encuentra registrada para este criterio"}, 'warning')
            return redirect(url_for('mantenimiento'))

    opc_criterio.idCriterio = in_criterio
    opc_criterio.strOpcion = in_opcion
    opc_criterio.numOpcion = in_num_opcion

    db.session.commit()
    
    return redirect(url_for('mantenimiento'))

@app.route('/delete-opcion-criterio/<id>', methods=["GET","POST"])
def delete_opcion_criterio(id):
    mdl.opcion_criterio.query.filter_by(idOpcion = id).delete()
    
    db.session.commit()
    #COMENTflash({'title': "Opción eliminada exitosamente"}, 'success')
    return redirect(url_for('mantenimiento'))

#CRITERIO HABIL
def reset_eva_criterio(_idProveedor, _idCriterio):
    const_sesion = session.get("const_sesion")

    opcion = mdl.opcion_criterio.query.filter_by(idCriterio = _idCriterio).first()
    prioridad = mdl.prioridad_criterio.query.filter_by(idSesion = const_sesion, idCriterio = opcion.criterio.idCriterio).first().idPrioridad
    evaluacion = mdl.evaluacion_proveedor(
        idProveedor = _idProveedor,
        idSesion = const_sesion,
        idOpcion = opcion.idOpcion,
        idPrioridad = prioridad
    )
    db.session.add(evaluacion)
    db.session.commit()

@app.route('/add-prioridad-crit', methods=["POST"])
def add_prioridad():
    try:
        in_criterio = request.form["cbx-sel-criterio"]
        const_sesion = session.get("const_sesion")
        flgExists = mdl.prioridad_criterio.query.filter_by(idSesion = const_sesion, idCriterio = in_criterio).first()
        if flgExists is None:
            print("A")
            prioridad = mdl.prioridad_criterio(
                strPrioridad = "",
                numPrioridad = request.form["cbx-sel-prioridad-numPrioridad"], 
                idCriterio = in_criterio,
                idSesion = const_sesion
            )

            db.session.add(prioridad)
            db.session.commit()

            if len(mdl.opcion_criterio.query.filter_by(idCriterio=in_criterio).all()) == 0:
                flash({'title': "Advertencia: Criterio sin opciones registradas", 'message': "Para el análisis, todos los criterios deberán contar con al menos 1 opción registrada"}, 'warning')
            #else:
                #COMENTflash({'title': "Prioridad asignada exitosamente"}, 'success')
        else:
            print("B")
            flash({'title': "Este criterio ya cuenta con una prioridad asignada"}, 'warning')      
    
        return redirect(url_for('criterios_proveedores'))
    
    except:
        flash({'title': "Error: prioridad de criterio inválida", 'message': "Es necesario registrar previamente un sector y un criterio"}, 'error')
        return redirect(url_for('criterios_proveedores'))
    
@app.route('/edit-prioridad-crit/<id>', methods=["GET","POST"])
def edit_prioridad(id):
    const_sesion = session.get("const_sesion")
    prioridad = mdl.prioridad_criterio.query.filter_by(idPrioridad = id, idSesion = const_sesion).first()
    prioridad.numPrioridad = request.form["cbx-edit-sel-prioridad-numPrioridad"]
    db.session.commit()
    #COMENTflash({'title': "Prioridad modificada exitosamente"}, 'success')
    return redirect(url_for('criterios_proveedores'))

@app.route('/delete-prioridad-crit/<id>', methods=["GET","POST"])
def delete_prioridad(id):
    const_sesion = session.get("const_sesion")

    mdl.prioridad_criterio.query.filter_by(idPrioridad = id, idSesion = const_sesion).delete()

    opciones = mdl.opcion_criterio.query.filter_by(idCriterio = id).all()
    for opc in opciones:
        mdl.evaluacion_proveedor.query.filter_by(idOpcion = opc.idOpcion, idSesion = const_sesion).delete()
        
    db.session.commit()
    #COMENTflash({'title': "Prioridad eliminada exitosamente"}, 'success')

    return redirect(url_for('criterios_proveedores'))

#PROVEEDOR
@app.route('/btn-proveedor', methods=["GET","POST"])
def btn_proveedor_ruc():
    try:
        const_user = session.get("const_user")
        ruc = request.form["txt-ruc"]
        detail_json = buscarRUCAPI(ruc)
        detail = detail_json.split("|")

        if request.form["action-ruc"] == "search":
            session["const_nombre"] = detail[0]
            session["const_estado"] = detail[1]
            session["const_habido"] = detail[2]
            session["const_direccion"] = detail[3]
            session["const_ruc_search"] = ruc

        if request.form["action-ruc"] == "add":
            flgExists = mdl.proveedor.query.filter_by(idUser = const_user, rucProveedor = ruc).first()

            if flgExists is None:
                proveedor = mdl.proveedor(
                    rucProveedor = ruc,
                    strNombre = detail[0],
                    strDescripcion = detail_json,
                    idUser = const_user
                )
                db.session.add(proveedor)
                db.session.commit()

                session["const_nombre"] = ""
                session["const_estado"] = ""
                session["const_habido"] = ""
                session["const_direccion"] = ""
                session["const_ruc_search"] = ""

                #COMENTflash({'title': "Proveedor añadido exitosamente"}, 'success')
            else:
                flash({'title': "Este proveedor ya se encuentra registrado"}, 'warning')
        
        return redirect(url_for('criterios_proveedores'))
    
    except:
        flash({'title': "Advertencia: RUC no válido", 'message': "No se encontró a un proveedor con este RUC"}, 'warning')
        return redirect(url_for('criterios_proveedores'))
    
@app.route('/edit-proveedor/<id>', methods=["GET","POST"])
def edit_proveedor(id):
    try:
        const_user = session.get("const_user")
        ruc = request.form["txt-edit-proveedor-ruc"]
        flgExists = mdl.proveedor.query.filter_by(idUser = const_user, rucProveedor = ruc).first()

        if flgExists is None:
            proveedor = mdl.proveedor.query.filter_by(idProveedor = id).first()
            detail_json = buscarRUCAPI(ruc)
            detail = detail_json.split("|")
            proveedor.rucProveedor = ruc
            proveedor.strNombre = detail[0]
            proveedor.strDescripcion = detail_json

            db.session.commit()

            #COMENTflash({'title': "Proveedor modificado exitosamente"}, 'success')
        else:
            if int(flgExists.idProveedor) != int(id):
                flash({'title': "Este proveedor ya se encuentra registrado"}, 'warning')
        
        return redirect(url_for('criterios_proveedores'))

    except:
        flash({'title': "Advertencia: RUC no válido", 'message': "No se encontró a un proveedor con este RUC"}, 'warning')
        return redirect(url_for('criterios_proveedores'))

@app.route('/delete-proveedor/<id>', methods=["GET","POST"])
def delete_proveedor(id):
    mdl.proveedor.query.filter_by(idProveedor = id).delete()
    
    db.session.commit()
    return redirect(url_for('criterios_proveedores'))

#EVALUACION
@app.route('/add-evaluacion-proveedor', methods=["POST"])
def add_evaluacion_proveedor():
    const_sesion = session.get("const_sesion")
    const_proveedor_seleccionado = session.get("const_proveedor_seleccionado")

    #Data
    lst_criterios = request.form.getlist("lst-criterios")
    flg_prov_evaluado = mdl.evaluacion_proveedor.query.filter_by(idProveedor = const_proveedor_seleccionado, idSesion = const_sesion).first() is not None
    saved_options = list()

    for criterio in lst_criterios:
        if flg_prov_evaluado:
            evaluaciones = mdl.evaluacion_proveedor.query.filter_by(idProveedor = const_proveedor_seleccionado, idSesion = const_sesion).all()
            
            for eva in evaluaciones:
                opcion = mdl.opcion_criterio.query.filter_by(idOpcion = criterio).first()
                saved_options.insert(0,opcion.criterio.idCriterio)
                if eva.opcion.criterio.idCriterio == opcion.criterio.idCriterio:
                    eva.idOpcion = criterio
                    db.session.commit()
            
        else:
            opcion = mdl.opcion_criterio.query.filter_by(idOpcion = criterio).first()
            prioridad = mdl.prioridad_criterio.query.filter_by(idSesion = const_sesion, idCriterio = opcion.criterio.idCriterio).first().idPrioridad

            evaluacion = mdl.evaluacion_proveedor(
                idProveedor = const_proveedor_seleccionado,
                idSesion = const_sesion,
                idOpcion = criterio,
                idPrioridad = prioridad
            )
            
            saved_options.insert(0,opcion.criterio.idCriterio)
            db.session.add(evaluacion)
            db.session.commit()

    for criterio in lst_criterios:
        opcion = mdl.opcion_criterio.query.filter_by(idOpcion = criterio).first()
        prioridad = mdl.prioridad_criterio.query.filter_by(idSesion = const_sesion, idCriterio = opcion.criterio.idCriterio).first().idPrioridad
        if opcion.criterio.idCriterio not in saved_options:
            evaluacion = mdl.evaluacion_proveedor(
                idProveedor = const_proveedor_seleccionado,
                idSesion = const_sesion,
                idOpcion = criterio,
                idPrioridad = prioridad
            )
            db.session.add(evaluacion)
            db.session.commit()

    return redirect(url_for('puntaje_criterios'))

@app.route('/select-evaluacion-proveedor/<id>', methods=["GET","POST"])
def select_evaluacion_proveedor(id):
    session["const_proveedor_seleccionado"] = id

    return redirect(url_for('puntaje_criterios'))

@app.route('/delete-evaluacion-proveedor/<id>', methods=["GET","POST"])
def delete_evaluacion_proveedor(id):
    const_sesion = session.get("const_sesion")

    mdl.evaluacion_proveedor.query.filter_by(idProveedor = id, idSesion = const_sesion).delete()
    
    db.session.commit()
    return redirect(url_for('puntaje_criterios'))

def testing():
    const_user = session.get("const_user")
    const_sesion = session.get("const_sesion")

    len_prov = len(mdl.proveedor.query.filter_by(idUser = const_user).all())

    puntajes_por_criterio = {}
    prioridades_criterios = []

    const_resultados_general_proveedores = [''] * len_prov
    const_resultados_general_puntajes = [0] * len_prov

    evaluaciones = mdl.evaluacion_proveedor.query.filter_by(idSesion = const_sesion).all()

    for eva in evaluaciones:
        if eva.opcion.criterio.idCriterio not in puntajes_por_criterio:
            puntajes_por_criterio[eva.opcion.criterio.idCriterio] = {'descripcion': eva.opcion.criterio.strCriterio, 'puntajes': []}

        puntajes_por_criterio[eva.opcion.criterio.idCriterio]['puntajes'].append(
            {
                'proveedor': eva.proveedor.rucProveedor + " - " + eva.proveedor.strNombre,
                'puntaje': float(eva.opcion.numOpcion)
            }
        )

    for criterio, data in puntajes_por_criterio.items():
        print("criterio: " + str(criterio))
        priori = mdl.prioridad_criterio.query.filter_by(idCriterio = criterio, idSesion = const_sesion).first()
        print("OBTENIDO: " + str(priori.numPrioridad))
        prioridades_criterios.append(priori.numPrioridad)

    rs_prioridades = generate_results(prioridades_criterios)
    print("prioridades: " + str(rs_prioridades[0]))

    idc = 0
    #TEST
    print("-----------prueba")
    print(puntajes_por_criterio.items())
    for criterio, data in puntajes_por_criterio.items():
        #Recorrer criterios
        descripcion = data['descripcion']
        puntajes = data['puntajes']
        lista_de_puntajes = []
            
        for puntaje_info in puntajes:
            lista_de_puntajes.append(puntaje_info['puntaje'])
        
        #
        rs_aux = generate_dataset(lista_de_puntajes)
        print("_RES" + str(rs_aux))
        print("TESTSFS")
        rs_general = generate_results(lista_de_puntajes)
        print("RES" + descripcion + ": ||| " + str(rs_general))
        for idx, puntaje_info in enumerate(puntajes):
            const_resultados_general_proveedores[idx] = puntaje_info['proveedor']
            const_resultados_general_puntajes[idx] += rs_general[0][idx] * rs_prioridades[0][idc] * 100
        
        idc+=1
    print("LLEGO")
    print(const_resultados_general_proveedores)
    print(const_resultados_general_puntajes)
    session["const_resultados_general_proveedores"] = const_resultados_general_proveedores
    session["const_resultados_general_puntajes"] = const_resultados_general_puntajes
