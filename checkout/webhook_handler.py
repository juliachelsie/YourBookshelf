from django.http import HttpResponse

class WH_Handler:
    """ Handles Stripe Webhooks """
    def __init__(self, request):
        self.request = request

    def handle_events(self, event):
        """ Handles generic/unexpected/unknown webhook event """

        return HttpResponse(
            content = f'Webhook received: {event["type"]}',
            status = 200
        )
        
