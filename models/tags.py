from db import db

class TagsModel(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=False)

    store = db.relationship("StoreModel", back_populates="tags")
    items = db.relationship("ItemModel", back_populates="tags", secondary="items_tags")
    # sqlalchemy will go through secondary table to know which items this tag is related to
    # Process - It will go into secondary table, look at the tag_id foreignkey that is linked to id in this table (tag table)
    # and it will give items that are related to this tag_id in the secondary table