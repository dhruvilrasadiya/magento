from mongoengine import (
    Document as MongoDocument,
    StringField,
    DictField,
)


class PDFDocumentLog(MongoDocument):
    file_name = StringField(required=True, unique=True)
    document_ids = DictField() 