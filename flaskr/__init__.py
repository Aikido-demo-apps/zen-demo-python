import os

from flask import Flask, render_template, send_from_directory, request


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
        return "Hello User with id: %s" % (request.headers.get('user'))

    # Static files
    @app.route('/<path:path>')
    def send_report(path):
        print(path)
        # Using request args for path will expose you to directory traversal attacks
        return send_from_directory('resources/public', path)

    return app
