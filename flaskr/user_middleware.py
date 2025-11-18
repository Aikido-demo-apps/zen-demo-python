from aikido_zen import set_user, set_rate_limit_group
from werkzeug.wrappers import Request, Response, ResponseStream

class UserMiddleware():

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request = Request(environ)

        # --- Rate Limiting Group Logic ---
        rate_limiting_group_id = request.cookies.get('RateLimitingGroupID')
        if rate_limiting_group_id:
            set_rate_limit_group(rate_limiting_group_id)

        user = request.headers.get('user')
        if user:
            id = int(request.headers.get('user'))
            set_user({"id": id, "name": self.get_name(id)})
        else:
            # Check for X-User-ID and X-User-Name headers
            user_id = request.headers.get('X-User-ID')
            user_name = request.headers.get('X-User-Name')
            if user_id and user_name:
                id = int(user_id)
                set_user({"id": id, "name": user_name})

        return self.app(environ, start_response)

    def get_name(self, number):
        names = [
            "Hans",
            "Pablo",
            "Samuel",
            "Timo",
            "Tudor",
            "Willem",
            "Wout",
            "Yannis",
        ]

        # Use absolute value to handle negative numbers
        # Use modulo to wrap around the list
        index = abs(number) % len(names)
        return names[index]
