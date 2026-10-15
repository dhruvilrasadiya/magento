from mongoengine import (
    Document as MongoDocument,
    StringField,
    DictField,
)


class CustomerDocumentLog(MongoDocument):
    customer_id = StringField(required=True, unique=True)
    document_ids = DictField()
