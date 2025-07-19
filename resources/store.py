#store.py
import uuid
from sqlite3 import IntegrityError

from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError

from db import db
from models import StoreModel
from schemas import StoreSchema

blp = Blueprint("stores", __name__, description="Operations on stores")

@blp.route("/store")
class StoreList(MethodView):
    @blp.response(200, StoreSchema(many=True))
    def get(self):
        #return {"stores": list(stores.values())}
        #return stores.values()
        return StoreModel.query.all()

    @blp.arguments(StoreSchema)
    @blp.response(201, StoreSchema)
    def post(self, store_data):
        store = StoreModel(**store_data)

        try:
            db.session.add(store)
            db.session.commit()
        except IntegrityError:
            abort(400, message="Store name already exists.")
        except SQLAlchemyError:
            abort(500, message="An error occurred while creating an Store.")

        return store

@blp.route("/store/<int:store_id>")
class Store(MethodView):
    @blp.response(200, StoreSchema)
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id) # This get_or_404 method works on primary key
        return store # Here note that although we are returning an object, but the shema we are using "StoreSchema"
        # will convert it into json


    def delete(self, store_id):

        store = StoreModel.query.get_or_404(store_id)
        db.session.delete(store)
        db.session.commit()
        return {"message": "Item deleted"}