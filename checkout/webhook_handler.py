from django.http import HttpResponse

class WH_Handler:
    """ Handles Stripe Webhooks """
    def __init__(self, request):
        self.request = request

    def handle_events(self, event):
        """ Handles generic/unexpected/unknown webhook event """

        return HttpResponse(
            content = f'Unhandled Webhook received: {event["type"]}',
            status = 200
        )

    def handle_payment_succeeded(self, event):
        """ Handles payment_intent.succeeded webhooks from Stripe """

        return HttpResponse(
            content = f'Webhook received: {event["type"]}',
            status = 200
        )

    def handle_payment_failed(self, event):
        """ Handles payment_intent.failed webhooks from Stripe """

        return HttpResponse(
            content = f'Webhook received: {event["type"]}',
            status = 200
        )
