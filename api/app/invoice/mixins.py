from datetime import datetime

from flask_restful import reqparse

class InvoiceMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('invoice_id', type=int, required=True)

class InvoiceAdminMixin(object):
    dt_format = lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ')

    get_parser = reqparse.RequestParser()
    get_parser.add_argument('event_id', type=int, required=True)

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('event_id', type=int, required=True)
    post_parser.add_argument('offer_ids', type=int, required=True, action='append')
    post_parser.add_argument('event_fee_ids', type=int, required=True, action='append')
    post_parser.add_argument('due_date', type=dt_format, required=True)

class PaymentsMixin(object):
    post_parser = reqparse.RequestParser()
    post_parser.add_argument('invoice_id', type=int, required=True)

class PaymentsWebhookMixin(object):
    post_parser = reqparse.RequestParser()
    post_parser.add_argument('Stripe-Signature', type=str, location='headers')
