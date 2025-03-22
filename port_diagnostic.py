import socket

def check_port_availability(port):
    try:
        # Create a socket object
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Set a timeout to prevent hanging
        sock.settimeout(2)
        
        # Attempt to bind to the port
        result = sock.connect_ex(('127.0.0.1', port))
        
        if result == 0:
            print(f"Port {port} is already in use")
            return False
        else:
            print(f"Port {port} is available")
            return True
        
    except Exception as e:
        print(f"Error checking port: {e}")
        return False
    finally:
        sock.close()

# Check port 5000
check_port_availability(5000) 