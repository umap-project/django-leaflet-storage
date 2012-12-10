from functools import wraps

from django.core.urlresolvers import reverse

from .views import simple_json_response


def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated():
            return simple_json_response(login_required=reverse("login"))
        return view_func(request, *args, **kwargs)
    return wrapper


def jsonize_view(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        response_kwargs = {}
        if hasattr(response, 'rendered_content'):
            response_kwargs['html'] = response.rendered_content
        if hasattr(response, 'location'):
            response_kwargs['redirect'] = response.location
        return simple_json_response(**response_kwargs)
    return wrapper
