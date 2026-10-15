from mongoengine import Document, StringField, DictField


class AnalyticsDocumentLog(Document):
    time_id = StringField(primary_key=True)
    insights_type = StringField(required=True)
    document_ids = DictField()
