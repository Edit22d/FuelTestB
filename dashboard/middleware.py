from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import HttpResponseForbidden

class JWTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        auth = JWTAuthentication()

        try:
            user_auth = auth.authenticate(request)
            if user_auth:
                request.user, _ = user_auth
        except:
            request.user = None

        response = self.get_response(request)
        return response