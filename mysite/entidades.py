from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref
from datetime import datetime

#CONFIG
app = Flask(__name__)
app.config["DEBUG"] = True
'''
SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="upcisitp",
    password="ronnie_21",
    hostname="upcisitp.mysql.pythonanywhere-services.com",
    databasename="upcisitp$tp",
)
'''

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="root",
    password="root",
    hostname="localhost",
    databasename="upcisitp$tp",
)

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
app.app_context().push()

class user(db.Model):
    __tablename__ = "user"

    idUser = db.Column(db.Integer, primary_key=True)
    userKey = db.Column(db.String(32))
    descUser = db.Column(db.String(4096))

class sector_criterio(db.Model):
    __tablename__ = "sector_criterio"

    idSector = db.Column(db.Integer, primary_key=True)
    strSector = db.Column(db.String(4096))

    user = db.relationship("user", backref=backref('sector_criterio', passive_deletes=True))
    idUser = db.Column(db.Integer, db.ForeignKey('user.idUser', ondelete='CASCADE'))   

class sesion(db.Model):
    __tablename__ = "sesion"

    idSesion = db.Column(db.Integer, primary_key=True)
    fecSesion = db.Column(db.DateTime)
    
    sector = db.relationship("sector_criterio", backref=backref('sesion', passive_deletes=True))
    user = db.relationship("user", backref=backref('sesion', passive_deletes=True))
    idSector = db.Column(db.Integer, db.ForeignKey('sector_criterio.idSector', ondelete='CASCADE'))
    idUser = db.Column(db.Integer, db.ForeignKey('user.idUser', ondelete='CASCADE'))   

class proveedor(db.Model):
    __tablename__ = "proveedor"

    idProveedor = db.Column(db.Integer, primary_key=True)
    rucProveedor = db.Column(db.String(11))
    strNombre = db.Column(db.String(4096))
    strDescripcion = db.Column(db.String(4096))

    user = db.relationship("user", backref=backref('proveedor', passive_deletes=True))
    idUser = db.Column(db.Integer, db.ForeignKey('user.idUser', ondelete='CASCADE'))   

class criterio(db.Model):
    __tablename__ = "criterio"

    idCriterio = db.Column(db.Integer, primary_key=True)
    strCriterio = db.Column(db.String(4096))

    sector = db.relationship("sector_criterio", backref=backref('criterio', passive_deletes=True))
    user = db.relationship("user", backref=backref('criterio', passive_deletes=True))
    idSector = db.Column(db.Integer, db.ForeignKey('sector_criterio.idSector', ondelete='CASCADE'))
    idUser = db.Column(db.Integer, db.ForeignKey('user.idUser', ondelete='CASCADE'))  

class opcion_criterio(db.Model):
    __tablename__ = "opcion_criterio"

    idOpcion = db.Column(db.Integer, primary_key=True)
    strOpcion = db.Column(db.String(4096))
    numOpcion = db.Column(db.Numeric(precision=10,scale=2))

    criterio = db.relationship("criterio", backref=backref('opcion_criterio', passive_deletes=True))
    user = db.relationship("user", backref=backref('opcion_criterio', passive_deletes=True))
    idCriterio = db.Column(db.Integer, db.ForeignKey('criterio.idCriterio', ondelete='CASCADE'))
    idUser = db.Column(db.Integer, db.ForeignKey('user.idUser', ondelete='CASCADE'))   

class proveedor_habil(db.Model):
    __tablename__ = "proveedor_habil"

    idProvHab = db.Column(db.Integer, primary_key=True)

    proveedor = db.relationship("proveedor", backref=backref('proveedor_habil', passive_deletes=True))
    sesion = db.relationship("sesion", backref=backref('proveedor_habil', passive_deletes=True))
    idProveedor = db.Column(db.Integer, db.ForeignKey('proveedor.idProveedor', ondelete='CASCADE'))
    idSesion = db.Column(db.Integer, db.ForeignKey('sesion.idSesion', ondelete='CASCADE'))
  
class prioridad_criterio(db.Model):
    __tablename__ = "prioridad_criterio"

    idPrioridad = db.Column(db.Integer, primary_key=True)
    strPrioridad = db.Column(db.String(4096))
    numPrioridad = db.Column(db.Integer)
    
    criterio = db.relationship("criterio", backref=backref('prioridad_criterio', passive_deletes=True))
    sesion = db.relationship("sesion", backref=backref('prioridad_criterio', passive_deletes=True))
    idCriterio = db.Column(db.Integer, db.ForeignKey('criterio.idCriterio', ondelete='CASCADE'))
    idSesion = db.Column(db.Integer, db.ForeignKey('sesion.idSesion', ondelete='CASCADE'))

class evaluacion_proveedor(db.Model):
    __tablename__ = "evaluacion_proveedor"

    idEvaluacion = db.Column(db.Integer, primary_key=True)
    
    proveedor = db.relationship("proveedor", backref=backref('evaluacion_proveedor', passive_deletes=True))
    sesion = db.relationship("sesion", backref=backref('evaluacion_proveedor', passive_deletes=True))
    opcion = db.relationship("opcion_criterio", backref=backref('evaluacion_proveedor', passive_deletes=True))
    prioridad = db.relationship("prioridad_criterio", backref=backref('evaluacion_proveedor', passive_deletes=True))
    idProveedor = db.Column(db.Integer, db.ForeignKey('proveedor.idProveedor', ondelete='CASCADE'))   
    idSesion = db.Column(db.Integer, db.ForeignKey('sesion.idSesion', ondelete='CASCADE'))
    idOpcion = db.Column(db.Integer, db.ForeignKey('opcion_criterio.idOpcion', ondelete='CASCADE'))
    idPrioridad = db.Column(db.Integer, db.ForeignKey('prioridad_criterio.idPrioridad', ondelete='CASCADE'))
