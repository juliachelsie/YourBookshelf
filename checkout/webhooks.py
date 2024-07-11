from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from checkout.webhook_handler import WH_Handler
import stripe


@require_POST
@csrf_exempt
def webhook(request):
    """ Listen afterwebhooks from Stripe """
    wh_secret = settings.STRIPE_WH_SECRET
    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Receive webhook data and verify the signature
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, wh_secret
        )
    except ValueError as e:
        # Invalid payload.
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature.
        return HttpResponse(status=400)
    except Exception as e:
        return HttpResponse(content=e, status=400)

    # Webhook handler setup.
    handler = WH_Handler(request)

    # Map webhook event to relevant handler functions.
    event_map = {
        'payment_intent.succeeded': handler.handle_payment_succeeded,
        'payment_intent.payment_failed': handler.handle_payment_failed,
    }

    # Get the webhook type from Stripe.
    event_type = event['type']

    # If there is a handler for it, get it from the event map
    # Use the generic one by default.
    event_handler = event_map.get(event_type, handler.handle_events)

    # Call the event handler with the event
    response = event_handler(event)
    return response
