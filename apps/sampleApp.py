# Example usage
import json
import threading
from daemon.weaprous import WeApRous
from  daemon.request import Request  

# Initialize the WeApRous app
app = WeApRous()

# Global data structures for tracking
peers_list = []  # List of active peers: [{"username": str, "ip": str, "port": int, "channels": []}]
channels_list = {}  # Dictionary of channels: {channel_name: [usernames]}
users_credentials = {"admin": "password"}  # Simple user database
peers_lock = threading.Lock()  # Thread-safe access to peers_list
channels_lock = threading.Lock()  # Thread-safe access to channels_list

@app.route(path='/api/login', methods=['POST'])
def login(headers="guest", body="anonymous"):
    """
    Handle user login via POST request.

    This route simulates a login process and prints the provided headers and body
    to the console.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or login payload.
    """
    print("[SampleApp] Logging in {} to {}".format(headers, body))
    try:
        # Parse JSON body
        data = json.loads(body) if body and body != "anonymous" else {}
        username = data.get("username", "")
        password = data.get("password", "")
        
        print("[SampleApp] Login attempt: username={}".format(username))
        
        # Validate credentials
        if username in users_credentials and users_credentials[username] == password:
            response = {
                "status": "success",
                "message": "Login successful",
                "username": username,
                "token": "token_{}".format(username)  # Simple token generation
            }
            print("[SampleApp] Login successful for user: {}".format(username))
        else:
            response = {
                "status": "failed",
                "message": "Invalid username or password"
            }
            print("[SampleApp] Login failed for user: {}".format(username))
        
        return json.dumps(response)
    
    except Exception as e:
        print("[SampleApp] Error in login: {}".format(e))
        return json.dumps({"status": "error", "message": str(e)})

@app.route('/hello', methods=['PUT'])
def hello(headers, body):
    """
    Handle greeting via PUT request.

    This route prints a greeting message to the console using the provided headers
    and body.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or message payload.
    """
    print("[SampleApp] ['PUT'] Hello in {} to {}".format(headers, body))

@app.route("/", methods=["GET"])
def home(_=None):
    return {"message": "Welcome to the RESTful TCP WebApp"}

@app.route("/user", methods=["GET"])
def get_user(_):
    return {"id": 1, "name": "Alice", "email": "alice@example.com"}

@app.route("/echo", methods=["POST"])
def echo(body):
    try:
        data = json.loads(body)
        return {"received": data}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON"}

