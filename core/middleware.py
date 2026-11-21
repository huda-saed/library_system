from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode


class LoginRequiredMiddleware:
    """
    Qofka aan login gareyn ma arki karo wax bog ah oo ka mid ah nidaamka.
    Kaliya bogagga login-ka iyo register-ka (iyo static/media/admin) ayaa furan.
    Anyone who is not logged in is redirected to the login page.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def _exempt_paths(self):
        paths = [reverse(name) for name in getattr(settings, 'LOGIN_EXEMPT_URL_NAMES', [])]
        prefixes = [settings.STATIC_URL, settings.MEDIA_URL, '/admin/']
        return paths, prefixes

    def __call__(self, request):
        if request.user.is_authenticated:
            return self.get_response(request)

        paths, prefixes = self._exempt_paths()
        if request.path in paths or any(request.path.startswith(p) for p in prefixes):
            return self.get_response(request)

        messages.info(request, "Fadlan marka hore soo gal si aad u aragto nidaamka (Please log in first).")
        login_url = reverse(settings.LOGIN_URL) if ':' in settings.LOGIN_URL else settings.LOGIN_URL
        query = urlencode({'next': request.get_full_path()}) if request.path != '/' else ''
        return redirect(f"{login_url}?{query}" if query else login_url)
