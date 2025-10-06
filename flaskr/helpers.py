import subprocess
import requests
from pathlib import Path
from aikido_zen.errors import AikidoSSRF, AikidoPathTraversal

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
        try:
            response = requests.get(url_string, timeout=10)
            return response.text, response.status_code
        except AikidoSSRF as e:
            return f"Error: {str(e)}", 500
        except Exception as e:
            if "Failed to resolve" in str(e):
                return f"Error: {str(e)}", 500
            return f"Error: {str(e)}", 400


    @staticmethod
    def read_file(file_path):
        """Read content from a file"""
        full_path = Path("flaskr/resources/blogs/") / file_path
        try:
            with open(full_path, 'r') as file:
                return file.read()
        except AikidoPathTraversal as e:
            return f"Error: {str(e)}", 500
        except Exception as e:
            if "No such file or directory" in str(e) or "Is a directory:" in str(e) or "embedded null byte" in str(e):
                return f"Error: {str(e)}", 500
            return f"Error: {str(e)}", 400

    @staticmethod
    def make_http_request_different_port(url_string, port):
        """Make a HTTP GET request with a different port"""
        import re
        # Replace the port in the URL
        url_with_port = re.sub(r':\d+', f':{port}', url_string)
        try:
            response = requests.get(url_with_port, timeout=10)
            return response.text, response.status_code
        except AikidoSSRF as e:
            return f"Error: {str(e)}", 500
        except Exception as e:
            if "Failed to resolve" in str(e):
                return f"Error: {str(e)}", 500
            return f"Error: {str(e)}", 400
