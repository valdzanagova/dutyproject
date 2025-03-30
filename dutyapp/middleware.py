from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class VerificationRequiredMiddleware:
    """
    Middleware that requires verification for all requests,
    except for allowed paths and requests with a valid timeless token.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check for a non-reference token in the header
        token = request.META.get('HTTP_X_API_TOKEN')
        if token and token == settings.API_PERMANENT_TOKEN:
            return self.get_response(request)

        # Paths that do not require verification (e.g. login pages and admin panel)
        allowed_paths = [
            reverse('send_code'),
            reverse('verify_code'),
            reverse('admin:index'),
        ]
        if request.path not in allowed_paths and not request.session.get('is_verified'):
            return redirect('send_code')

        return self.get_response(request)
