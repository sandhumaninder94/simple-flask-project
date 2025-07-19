#app.py
import os

from flask import Flask, jsonify
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from db import db
from blocklist import BLOCKLIST
from resources.item import blp as ItemBlueprint
from resources.store import blp as StoreBlueprint
from resources.tag import blp as TagBlueprint
from resources.user import blp as UserBlueprint

def create_app(db_url=None):
    app = Flask(__name__)

    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Stores REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URL", "sqlite:///app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app) #Connects SQLAlchemy to the Flask app

    migrate = Migrate(app,db)

    api = Api(app)

    #JWTs should not be stored in our code but in env variables which we will do while deployment of this app later
    app.config["JWT_SECRET_KEY"] = "jose"
    jwt = JWTManager(app)

    app.config["JWT_SECRET_KEY"] = "jose"
    jwt = JWTManager(app)


    """
    The following functions : @jwt.additional_claims_loader, @jwt.expired_token_loader, etc are LIKE hooks or callups, 
    They listen for specific events that happen during the JWT lifecycle.
    
    The library calls them automatically at the right time. For example:
    
    When a user logs in and you generate a token, the additional_claims_loader is called automatically to add 
    custom claims (like whether the user is an admin).
    
    When a request is made with a JWT, Flask-JWT-Extended checks if the token is expired, invalid, or missing, 
    and it will call the respective function (expired_token_loader, invalid_token_loader, etc.) when needed.
    
    Why Are These Functions in app.py?
    You configure them in app.py because you want the behavior to apply globally to your entire Flask application. 
    You don’t want to manually check for token expiration or invalidity in every route. 
    By defining these functions in one place (in app.py), Flask-JWT-Extended can handle these tasks for you, 
    automatically checking the JWTs during every request.
    
    """

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {
                    "description": "The token is not fresh.",
                    "error": "fresh_token_required",
                }
            ),
            401,
        )

    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        return jwt_payload["jti"] in BLOCKLIST

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {"description": "The token has been revoked.", "error": "token_revoked"}
            ),
            401,
        )

    @jwt.additional_claims_loader
    def add_claims_to_jwt(identity):
        if identity == 1:
            return {"is_admin": True}
        return {"is_admin": False}

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (
            jsonify({"message": "The token has expired.", "error": "token_expired"}),
            401,
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify(
                {"message": "Signature verification failed.", "error": "invalid_token"}
            ),
            401,
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify(
                {
                    "description": "Request does not contain an access token.",
                    "error": "authorization_required"
                }
            ),
            401,
        )


    api.register_blueprint(ItemBlueprint)
    api.register_blueprint(StoreBlueprint)
    api.register_blueprint(TagBlueprint)
    api.register_blueprint(UserBlueprint)

    return app

'''
@app.get("/store")
def get_stores():
    return {"stores": list(stores.values())}

@app.get("/store/string:<store_id>")
def get_store(store_id):
    try:
        return stores[store_id]
    except KeyError:
        #abort(404, message="Store not found")
        return {"Message": "store not found"}, 404

@app.post("/store")
def create_store():
    # first we need to get the json the client had sent us
    store_data = request.get_json() # here the json string is converted into python dictionary (request_data is the python dictionary)

    #store_data should contain name of the store
    if "name" not in store_data:
        abort(400, message="Bad request. Ensure 'name' is included in the JSON payload.")

    #check if store already exists
    for store in stores.values():
        if store["name"] == store_data["name"]:
            abort(400, message="Store already exists.")

    store_id = uuid.uuid4().hex
    new_store = {**store_data, "id": store_id} #dictionary unpacking + adding data (id) ->
    
    stores[store_id] = new_store #it will create a new store with store id -> store_id
    return new_store, 201

@app.post("/item")
def create_item():
    item_data = request.get_json()

    #sab to pehla dekhna v 3 cheeza honia chahidia item de vich - name, price and store_id
    if ("name" not in item_data or "price" not in item_data or "store_id" not in item_data):
        abort(400, message="Bad request. Ensure 'price', 'store_id', and 'name' are included in the JSON payload.")

    #if same item already exists in particular store then we will throw an error message
    for item in items.values():
        if (item["store_id"] == item_data["store_id"] and item["name"] == item_data["name"]):
            abort(400, message="Item already exists")

    # Now check for the case if that store exists where we are trying to add the item
    if item_data["store_id"] not in stores:
        return {"Message": "store not found"}, 404

    item_id = uuid.uuid4().hex
    new_item = {**item_data, "id":item_id}
    items[item_id] = new_item

    return new_item, 201
# dekh bhra do cheeza bare keh rea video ch - particular item dia details te all items dia detail
#je particular item di gall ho rahi a ta apa item_id expect krage te details bhej dwage
#je all items di gal ho rahi a ta jma simple aa, sidda items dictionary vicho value list bhej deni hai
@app.get("/item")
def get_all_items():
    return {"items": list(items.values())}

@app.get("/item/<string:item_id>")
def get_item(item_id):
    
    try:
        return items[item_id]
    except KeyError:
        abort(404, message="Item not found")




@app.delete("/item/<string:item_id>")
def delete_item(item_id):
    try:
        del items[item_id]
        return {"Message": f"Item deleted"}, 200
    except KeyError:
        abort(400, message=f"Item with id {item_id} not found")




@app.put("/item/<string:item_id>")
def update_item(item_id):
    request_data = request.get_json()
    if "price" not in request_data and "name" not in request_data:
        abort(400, message="Bad request. Ensure 'price' and 'name' is included in the JSON payload.")
    try:
        item = items[item_id]
        item |= request_data
        return {"Message": f"Item - {item["name"]} Updated"}, 200
    except KeyError:
        abort(400, message=f"Bad Request: Item with id {item_id} not found")



@app.delete("/store/<string:store_id>")
def delete_store(store_id):
    try:
        del stores[store_id]
        return {"Message": f"Store deleted"}, 200
    except KeyError:
        abort(400, message=f"Store with id {store_id} not found")



@app.route("/test")
def test():
    return {"message": f"Here are all the stores: {stores}"}, 200
'''
