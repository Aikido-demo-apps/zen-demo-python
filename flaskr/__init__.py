import os

from aikido_zen import set_user
from aikido_zen.middleware import AikidoFlaskMiddleware
from flask import Flask, render_template, send_from_directory, request, jsonify
from flaskr.database import init_database, DatabaseHelper
from flaskr.helpers import Helpers
import aikido_zen
aikido_zen.protect()

def create_app(test_config=None):
    # create and configure the app
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="resources",
        template_folder="resources",
    )

    # app.config.from_mapping(
    #     SECRET_KEY='dev',
    #     DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    # )
    #
    # if test_config is None:
    #     # load the instance config, if it exists, when not testing
    #     app.config.from_pyfile('config.py', silent=True)
    # else:
    #     # load the test config if passed in
    #     app.config.from_mapping(test_config)
    #
    # # ensure the instance folder exists
    # try:
    #     os.makedirs(app.instance_path)
    # except OSError:
    #     pass

    # Routes
    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/pages/execute')
    def pages_execute():
        return render_template('execute_command.html')

    @app.route('/pages/create')
    def pages_create():
        return render_template('create.html')

    @app.route('/pages/request')
    def pages_request():
        return render_template('request.html')

    @app.route('/pages/read')
    def pages_read():
        return render_template('read_file.html')

    @app.route('/test_ratelimiting_1')
    def test_ratelimiting_1():
        return "Request successful (Ratelimiting 1)"

    @app.route('/test_ratelimiting_2')
    def test_ratelimiting_2():
        return "Request successful (Ratelimiting 2)"

    @app.route('/test_bot_blocking')
    def test_bot_blocking():
        return "Hello World! Bot blocking enabled on this route."

    @app.route('/test_user_blocking')
    def test_user_blocking():
        id = int(request.headers.get('user'))
        set_user({"id": id, "name": get_name(id)})
        return "Hello User with id: %s" % (id)

    class CreateRequest:
        def __init__(self, data):
            self.name = data.get('name')

    class CommandRequest:
        def __init__(self, data):
            self.user_command = data.get('userCommand')

    class RequestRequest:
        def __init__(self, data):
            self.url = data.get('url')

    @app.route('/clear', methods=['GET'])
    def clear():
        DatabaseHelper.clear_all()
        return "Cleared successfully."

    @app.route('/api/pets', methods=['GET'])
    def get_pets():
        pets = DatabaseHelper.get_all_pets()
        return jsonify(pets)

    @app.route('/api/create', methods=['POST'])
    def create_pet():
        data = request.get_json()
        create_request = CreateRequest(data)
        rows_created = DatabaseHelper.create_pet_by_name(create_request.name)

        if rows_created == -1:
            return "Database error occurred"
        return "Success!"

    @app.route('/api/execute', methods=['POST'])
    def execute_command_post():
        data = request.get_json()
        command_request = CommandRequest(data)
        result = Helpers.execute_shell_command(command_request.user_command)
        return result

    @app.route('/api/execute/<command>', methods=['GET'])
    def execute_command_get(command):
        result = Helpers.execute_shell_command(command)
        return result

    @app.route('/api/request', methods=['POST'])
    def make_request():
        data = request.get_json()
        request_data = RequestRequest(data)
        response = Helpers.make_http_request(request_data.url)
        return response

    @app.route('/api/request2', methods=['POST'])
    def make_request2():
        data = request.get_json()
        request_data = RequestRequest(data)
        response = Helpers.make_http_request(request_data.url)  # Using same method as request1 since we don't need OkHttp
        return response

    @app.route('/api/read', methods=['GET'])
    def read_file():
        file_path = request.args.get('path')
        content = Helpers.read_file(file_path)
        return content

    # Static files
    @app.route('/<path:path>')
    def send_report(path):
        print(path)
        # Using request args for path will expose you to directory traversal attacks
        return send_from_directory('resources/public', path)

    # Add zen middleware
    app.wsgi_app = AikidoFlaskMiddleware(app.wsgi_app)

    return app

def get_name(number):
    names = [
        "Hans",
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