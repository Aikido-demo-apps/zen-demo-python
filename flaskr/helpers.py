import subprocess
import requests
from pathlib import Path

class Helpers:
    @staticmethod
    def execute_shell_command(command):
        """Execute a shell command and return its output"""
        output = ""
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            stdout, stderr = process.communicate()
            output = stdout if stdout else stderr
        except Exception as e:
            output = f"Error: {str(e)}"
        return output

    @staticmethod
    def make_http_request(url_string):
        """Make a HTTP GET request using requests library"""
        try:
            response = requests.get(url_string)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def read_file(file_path):
        """Read content from a file"""
        content = ""
        try:
            full_path = Path("flaskr/resources/blogs/") / file_path
            with open(full_path, 'r') as file:
                content = file.read()
        except Exception as e:
            content = f"Error: {str(e)}"
        return content
