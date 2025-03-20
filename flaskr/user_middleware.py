from aikido_zen import set_user
from werkzeug.wrappers import Request, Response, ResponseStream

class UserMiddleware():

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request = Request(environ)

        user = request.headers.get('user')
        if user:
            id = int(request.headers.get('user'))
            set_user({"id": id, "name": self.get_name(id)})

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