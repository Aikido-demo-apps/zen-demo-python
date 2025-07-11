import subprocess
import requests
from pathlib import Path

class Helpers:
    @staticmethod
    def execute_shell_command(command):
        """Execute a shell command and return its output"""
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        stdout, stderr = process.communicate()
        return stdout if stdout else stderr

    @staticmethod
    def make_http_request(url_string):
        """Make a HTTP GET request using requests library"""
        response = requests.get(url_string)
        return response.text

    @staticmethod
    def read_file(file_path):
        """Read content from a file"""
        full_path = Path("flaskr/resources/blogs/") / file_path
        with open(full_path, 'r') as file:
            return file.read()
