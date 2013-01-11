from functools import wraps

from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden
from django.conf import settings

from .views import simple_json_response
from .models import Map


LOGIN_URL_NAME = getattr(settings, "LOGIN_URL", "login")


def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated():
            return simple_json_response(login_required=reverse(LOGIN_URL_NAME))
        return view_func(request, *args, **kwargs)
    return wrapper


def map_permissions_check(view_func):
    """
    Used for URLs dealing with the map.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        map_inst = get_object_or_404(Map, pk=kwargs['map_id'])
        user = request.user
        kwargs['map_inst'] = map_inst  # Avoid rerequesting the map in the view
        if map_inst.edit_status >= map_inst.EDITORS:
            if not user.is_authenticated():
                return simple_json_response(login_required=reverse(LOGIN_URL_NAME))
            elif not map_inst.can_edit(user):
                return HttpResponseForbidden('Action not allowed for user.')
        return view_func(request, *args, **kwargs)
    return wrapper


def jsonize_view(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        response_kwargs = {}
        if hasattr(response, 'rendered_content'):
            response_kwargs['html'] = response.rendered_content
        if response.has_header('location'):
            response_kwargs['redirect'] = response['location']
        return simple_json_response(**response_kwargs)
    return wrapper
