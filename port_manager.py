import os
import socket
import psutil
import subprocess
import sys
import signal
import time

def find_process_using_port(port):
    """Find and return the process using the specified port"""
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            try:
                process = psutil.Process(conn.pid)
                return {
                    'pid': conn.pid,
                    'name': process.name(),
                    'cmdline': process.cmdline()
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None
    return None

def kill_process_on_port(port):
    """Kill the process using the specified port"""
    process_info = find_process_using_port(port)
    
    if process_info:
        pid = process_info['pid']
        try:
            # Attempt graceful termination first
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            
            # Force kill if still running
            os.kill(pid, signal.SIGKILL)
            
            print(f"🔪 Killed process {pid} ({process_info['name']}) on port {port}")
            return True
        except Exception as e:
            print(f"❌ Error killing process: {e}")
            return False
    return False

def is_port_in_use(port):
    """Check if a port is currently in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_free_port(start_port=5000, max_port=6000):
    """Find the first available port in range"""
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return port
            except OSError:
                continue
    return None

def prepare_port(desired_port=5000):
    """
    Prepare the specified port for use
    - Check if port is in use
    - Kill existing process if needed
    - Return the port to use
    """
    if is_port_in_use(desired_port):
        print(f"🚧 Port {desired_port} is already in use")
        
        # Attempt to kill process
        if kill_process_on_port(desired_port):
            print(f"✅ Port {desired_port} has been cleared")
            return desired_port
        
        # Find alternative port if killing fails
        alternative_port = find_free_port()
        if alternative_port:
            print(f"🔄 Using alternative port: {alternative_port}")
            return alternative_port
        
        print("❌ Could not find an available port")
        return None
    
    return desired_port

# Example usage in app.py
if __name__ == '__main__':
    from app import app  # Import your Flask app
    
    # Prepare port
    port_to_use = prepare_port(5000)
    
    if port_to_use:
        print(f"🚀 Starting server on port {port_to_use}")
        app.run(
            host='0.0.0.0', 
            port=port_to_use, 
            debug=True
        )
    else:
        print("❌ Server could not start due to port conflicts")
        sys.exit(1) 