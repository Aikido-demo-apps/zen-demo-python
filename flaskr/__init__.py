import os

from aikido_zen import set_user
from aikido_zen.middleware import AikidoFlaskMiddleware
from flask import Flask, render_template, send_from_directory, request, jsonify
from flaskr.database import DatabaseHelper
from flaskr.helpers import Helpers
import aikido_zen
import threading
from flaskr.test_llm import test_llm
from flaskr.user_middleware import UserMiddleware
import time
# Enable Zen
aikido_zen.protect()

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

    class RequestDifferentPortRequest:
        def __init__(self, data):
            self.url = data.get('url')
            self.port = data.get('port')
   
    class RequestStoredSsrfRequest:
        def __init__(self, data):
            self.url_index = data.get('urlIndex')

    @app.route('/clear', methods=['GET'])
    def clear():
        DatabaseHelper.clear_all()
        return "Cleared successfully."

    @app.route('/api/pets/', methods=['GET'])
    def get_pets():
        pets = DatabaseHelper.get_all_pets()
        return jsonify(pets)

    @app.route('/api/pets/<id>', methods=['GET'])
    def get_pet_by_id(id):
        pet = DatabaseHelper.get_pet_by_id(id)
        if pet:
            return jsonify(pet)
        return jsonify({"error": "Pet not found"}), 404

    @app.route('/api/create', methods=['POST'])
    def create_pet():
        data = request.get_json()
        create_request = CreateRequest(data)
        DatabaseHelper.create_pet_by_name(create_request.name)
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

    @app.route('/api/request_different_port', methods=['POST'])
    def make_request_different_port():
        data = request.get_json()
        request_data = RequestDifferentPortRequest(data)
        response = Helpers.make_http_request_different_port(
            request_data.url, request_data.port)
        return response

    @app.route('/api/stored_ssrf', methods=['POST'])
    def make_stored_ssrf():
        data = request.get_json()
        request_data = RequestStoredSsrfRequest(data)
        if request_data.url_index is None:
            url_index = 0
        else:
            url_index = request_data.url_index
        urls = [
            'http://evil-stored-ssrf-hostname/latest/api/token',
            'http://metadata.google.internal/latest/api/token',
            'http://metadata.goog/latest/api/token',
            'http://169.254.169.254/latest/api/token',
        ]
        url = urls[url_index % urls.length]
        response = Helpers.make_http_request(url)
        return response

    @app.route('/api/stored_ssrf_2', methods=['POST'])
    def make_stored_ssrf_2():
       
        def ssrf():
            time.sleep(10)
            Helpers.make_http_request("http://evil-stored-ssrf-hostname/latest/api/token")
        
        thread = threading.Thread(target=ssrf)
        thread.start()
        return "Request successful (Stored SSRF 2 no context)"

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
