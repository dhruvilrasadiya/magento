from mongoengine import (
    Document as MongoDocument,
    StringField,
    DictField,
)


class ProductDocumentLog(MongoDocument):
    sku = StringField(required=True, unique=True)
    product_id = StringField(primary_key=True)
    document_ids = DictField()