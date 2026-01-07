import os
from functools import wraps

from aikido_zen import set_user
from aikido_zen.middleware import AikidoFlaskMiddleware
from flask import Flask, render_template, send_from_directory, request, jsonify
from flaskr.database import DatabaseHelper
from flaskr.helpers import Helpers
import aikido_zen
import re
from flaskr.test_llm import test_llm
from flaskr.user_middleware import UserMiddleware

# Enable Zen
aikido_zen.protect()


def require_authentication(f):
    """Decorator to require authentication for sensitive endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for user authentication via headers
        user_id = request.headers.get('user') or request.headers.get('X-User-ID')
        user_name = request.headers.get('X-User-Name')
        
        # Require both user ID and name for authenticated access
        if not user_id or not user_name:
            return jsonify({"error": "Authentication required. Please provide valid user credentials."}), 401
        
        # Validate user_id is numeric
        try:
            int(user_id)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid user credentials."}), 401
            
        return f(*args, **kwargs)
    return decorated_function

def create_app(test_config=None):
    # create and configure the app
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="resources",
        template_folder="resources",
    )

    # Add zen middleware
    app.wsgi_app = AikidoFlaskMiddleware(app.wsgi_app)

    # Add user middleware
    app.wsgi_app = UserMiddleware(app.wsgi_app)

    # Routes
    @app.route('/', methods=['GET'])
    def home():
        return render_template('index.html')

    @app.route('/pages/execute', methods=['GET'])
    def pages_execute():
        return render_template('execute_command.html')

    @app.route('/pages/create', methods=['GET'])
    def pages_create():
        return render_template('create.html')

    @app.route('/pages/request', methods=['GET'])
    def pages_request():
        return render_template('request.html')

    @app.route('/pages/read', methods=['GET'])
    def pages_read():
        return render_template('read_file.html')

    @app.route('/test_ratelimiting_1', methods=['GET'])
    def test_ratelimiting_1():
        return "Request successful (Ratelimiting 1)"

    @app.route('/test_ratelimiting_2', methods=['GET'])
    def test_ratelimiting_2():
        return "Request successful (Ratelimiting 2)"

    @app.route('/test_bot_blocking', methods=['GET'])
    def test_bot_blocking():
        return "Hello World! Bot blocking enabled on this route."

    @app.route('/test_user_blocking', methods=['GET'])
    def test_user_blocking():
        return "Hello User with id: %s" % (request.headers.get('user'))

    class CreateRequest:
        def __init__(self, data):
            self.name = data.get('name')

    class CommandRequest:
        def __init__(self, data):
            self.user_command = data.get('userCommand')

    class RequestRequest:
        def __init__(self, data):
            self.url = data.get('url')
            self.port = data.get('port', None)

    @app.route('/clear', methods=['GET'])
    def clear():
        DatabaseHelper.clear_all()
        return "Cleared successfully."

    @app.route('/api/pets/', methods=['GET'])
    def get_pets():
        pets = DatabaseHelper.get_all_pets()
        return jsonify(pets)

    @app.route('/api/create', methods=['POST'])
    def create_pet():
        data = request.get_json()
        create_request = CreateRequest(data)
        DatabaseHelper.create_pet_by_name(create_request.name)
        return "Success!"

    @app.route('/api/execute', methods=['POST'])
    @require_authentication
    def execute_command_post():
        data = request.get_json()
        command_request = CommandRequest(data)
        result = Helpers.execute_shell_command(command_request.user_command)
        return result

    @app.route('/api/execute/<command>', methods=['GET'])
    @require_authentication
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
        # Using same method as request1 since we don't need OkHttp
        response = Helpers.make_http_request(request_data.url)
        return response

    @app.route('/api/request_different_port', methods=['POST'])
    def make_request_different_port():
        data = request.get_json()
        request_data = RequestRequest(data)
        url = request_data.url
        port = request_data.port
        new_url = re.sub(r':\d+', f':{port}', url)
        response = Helpers.make_http_request(new_url)
        return response

    @app.route('/api/read', methods=['GET'])
    def read_file():
        file_path = request.args.get('path')
        content = Helpers.read_file(file_path)
        return content

    @app.route('/api/read2', methods=['GET'])
    def read_file2():
        file_path = request.args.get('path')
        content = Helpers.read_file2(file_path)
        return content

    @app.route('/test_llm', methods=['POST'])
    def test_llm_route():
        return test_llm()

    # Static files
    @app.route('/<path:path>', methods=['GET'])
    def send_report(path):
        # Using request args for path will expose you to directory traversal attacks
        return send_from_directory('resources/public', path)

    return app
