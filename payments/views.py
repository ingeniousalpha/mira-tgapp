from django.views.decorators.csrf import csrf_exempt

from . import utils


@csrf_exempt
def prepare(request):
    return utils.prepare(request)

@csrf_exempt
def complete(request):
    return utils.complete(request)
