#item.py

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import jwt_required, get_jwt

from db import db
from models import ItemModel
from schemas import ItemSchema, ItemUpdateSchema

blp = Blueprint("Items", __name__, description="Operations on items")


@blp.route("/item/<int:item_id>")
class Item(MethodView):
    @jwt_required()
    @blp.response(200, ItemSchema) #ehne make sure krna v jeda data apa return kar rahe a oho sahi format ch hove,
    #naal ehne typecasting v kar deni a
    def get(self, item_id):

        item = ItemModel.query.get_or_404(item_id)
        return item # we are trying to return a model but the schema we are using will convert it to Json


    @jwt_required()
    def delete(self, item_id):
        jwt = get_jwt()
        #jwt.get() is used to retrieve stored info in jwt, as we are checking below if jwt has is_admin == True
        if not jwt.get("is_admin"):
            abort(401, message="Admin privilege required")

        item = ItemModel.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        return {"message": "Item deleted"}

    @blp.arguments(ItemUpdateSchema)
    @blp.response(201, ItemSchema)
    def put(self,item_data, item_id):

        item = ItemModel.query.get(item_id)
        if item:
            item.price = item_data["price"]
            item.name = item_data["name"]
        else:
            item = ItemModel(id=item_id, **item_data)

        db.session.add(item)
        db.session.commit()

        return item


@blp.route("/item")
class ItemList(MethodView):

    @blp.response(200, ItemSchema(many=True)) #200 = OK
    def get(self):
        #return {"items": list(items.values())}
        #return items.values() #@blp.response(200,ItemSchema(many=True)) de kaaran upar wali return statement di lod nahi a
        return ItemModel.query.all() #Due to ItemSchema(many=True), this will be converted to a list

    @jwt_required(fresh=True)
    @blp.arguments(ItemSchema)
    @blp.response(201, ItemSchema)
    def post(self, item_data):
        '''
        # Since now we are working with databases, now we do not need to explicitly check for item ducplicacy
        # It will be done by databsase itself
        for item in items.values():
            if (
                item_data["name"] == item["name"]
                and item_data["store_id"] == item["store_id"]
            ):
                abort(400, message=f"Item already exists.")

        item_id = uuid.uuid4().hex
        item = {**item_data, "id": item_id}
        items[item_id] = item
        '''

        item = ItemModel(**item_data)
        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message= "An error occurred while creating an item.")

        return item