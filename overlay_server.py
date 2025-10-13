#!/usr/bin/env python3
"""
Overlay server utility for automatically starting a local web server
to display the overlay.html dashboard during training or gameplay.
"""

import http.server
import socketserver
import threading
import webbrowser
import time
import os
import sys
from pathlib import Path

class OverlayServer:
    def __init__(self, port=8001, auto_open=True):
        self.port = port
        self.auto_open = auto_open
        self.server = None
        self.server_thread = None
        self.running = False
        
    def start_server(self):
        """Start the overlay server in a separate thread"""
        try:
            # Change to the project directory
            project_dir = Path(__file__).parent
            os.chdir(project_dir)
            
            # Create a simple HTTP server
            handler = http.server.SimpleHTTPRequestHandler
            self.server = socketserver.TCPServer(("", self.port), handler)
            
            # Start server in a separate thread
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            self.running = True
            print(f"🌐 Overlay server started at http://localhost:{self.port}")
            print(f"📊 Overlay dashboard: http://localhost:{self.port}/overlay.html")
            
            # Auto-open browser if requested
            if self.auto_open:
                time.sleep(1)  # Give server a moment to start
                try:
                    webbrowser.open(f"http://localhost:{self.port}/overlay.html")
                    print("🚀 Overlay opened in your default browser")
                except Exception as e:
                    print(f"⚠️  Could not auto-open browser: {e}")
                    print(f"   Please manually open: http://localhost:{self.port}/overlay.html")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start overlay server: {e}")
            return False
    
    def _run_server(self):
        """Run the HTTP server (called in separate thread)"""
        try:
            self.server.serve_forever()
        except Exception as e:
            if self.running:  # Only print error if we're supposed to be running
                print(f"❌ Overlay server error: {e}")
    
    def stop_server(self):
        """Stop the overlay server"""
        if self.server and self.running:
            try:
                self.server.shutdown()
                self.server.server_close()
                self.running = False
                print("🛑 Overlay server stopped")
            except Exception as e:
                print(f"⚠️  Error stopping overlay server: {e}")
    
    def is_running(self):
        """Check if the server is running"""
        return self.running

def start_overlay_server(port=8001, auto_open=True):
    """
    Start the overlay server and return the server instance
    
    Args:
        port (int): Port number for the server (default: 8001)
        auto_open (bool): Whether to automatically open the browser (default: True)
    
    Returns:
        OverlayServer: The server instance
    """
    server = OverlayServer(port=port, auto_open=auto_open)
    if server.start_server():
        return server
    else:
        return None

def main():
    """Main function for testing the overlay server"""
    print("🚀 Starting overlay server...")
    
    # Try different ports if 8001 is busy
    for port in [8001, 8002, 8003, 8004]:
        try:
            server = start_overlay_server(port=port, auto_open=True)
            if server:
                print(f"\n✅ Overlay server is running!")
                print(f"📊 Dashboard: http://localhost:{port}/overlay.html")
                print(f"📁 Files: http://localhost:{port}/")
                print("\nPress Ctrl+C to stop the server...")
                
                try:
                    # Keep the server running
                    while server.is_running():
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 Stopping server...")
                    server.stop_server()
                    break
                return
        except Exception as e:
            print(f"Port {port} failed: {e}")
            continue
    
    print("❌ Could not start overlay server on any port")

if __name__ == "__main__":
    main()
