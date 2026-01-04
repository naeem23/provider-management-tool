from django.conf import settings
from django.http import JsonResponse


class FlowableServiceAuthMiddleware:
    """
    Authenticates Flowable service calls using a static API key.
    This is ONLY for service-to-service calls, not for human users.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if this is a Flowable service call
        api_key = request.headers.get("X-FLOWABLE-API-KEY")

        if api_key and api_key == settings.FLOWABLE_API_KEY:
            # Mark this request as authenticated by Flowable
            request.is_flowable = True
            # You can also set a system user here if needed
            # request.user = User.objects.get(username='flowable_system')
        
        return self.get_response(request)

        # # Only protect endpoints Flowable will call
        # if request.path.startswith("/api/flowable/"):
        #     api_key = request.headers.get("X-FLOWABLE-API-KEY")

        #     if api_key != settings.FLOWABLE_API_KEY:
        #         return JsonResponse(
        #             {"detail": "Unauthorized Flowable service"},
        #             status=401,
        #         )

        # return self.get_response(request)
