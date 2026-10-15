from mongoengine import (
    Document as MongoDocument,
    StringField,
    DictField,
    connect,
)
import os
from dotenv import load_dotenv


load_dotenv()
connect(
    db=os.environ["MONGODB_DATABASE"],
    username=os.environ["MONGODB_USERNAME"],
    password=os.environ["MONGODB_PASSWORD"],
    host=os.environ["MONGODB_HOST"],
    port=int(os.environ["MONGODB_PORT"]),
)


class OrderDocumentLog(MongoDocument):
    order_id = StringField(primary_key=True)
    document_ids = DictField()
