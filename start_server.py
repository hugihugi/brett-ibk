#!/usr/bin/env python3
"""
Simple Web Server for Board Game Collection

This script starts a local web server to serve your board game collection webpage.
This is needed because browsers block loading local CSV files for security reasons.
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import socket

def get_local_ip():
    """Get the local IP address of this computer"""
    try:
        # Connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "localhost"

def start_server(port=8000):
    """Start a simple HTTP server"""
    
    # Check if required files exist
    required_files = ['board_games_collection.html', 'brett_spiele.csv']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease make sure all files are in the current directory.")
        return
    
    # Check if images folder exists
    if not os.path.exists('images'):
        print("⚠️  Warning: 'images' folder not found. Game images may not display.")
    else:
        image_count = len([f for f in os.listdir('images') if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))])
        print(f"✓ Found {image_count} images in the images folder")
    
    print(f"🎲 Board Game Collection Server")
    print(f"=" * 40)
    print(f"✓ Starting server on port {port}")
    print(f"✓ Files found: {', '.join(required_files)}")
    
    try:
        # Create server
        handler = http.server.SimpleHTTPRequestHandler
        
        # Add CORS headers to allow local file access
        class CORSRequestHandler(handler):
            def end_headers(self):
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', '*')
                super().end_headers()
        
        with socketserver.TCPServer(("0.0.0.0", port), CORSRequestHandler) as httpd:
            local_ip = get_local_ip()
            print(f"✓ Server running at: http://localhost:{port}")
            print(f"📱 Phone access: http://{local_ip}:{port}")
            print(f"✓ Opening board game collection in your browser...")
            print(f"\n🌐 Your board game collection will open automatically!")
            print(f"   If it doesn't open, go to: http://localhost:{port}/board_games_collection.html")
            print(f"📱 On your phone, go to: http://{local_ip}:{port}/board_games_collection.html")
            print(f"\n📝 Press Ctrl+C to stop the server")
            print(f"=" * 40)
            
            # Open browser automatically
            webbrowser.open(f'http://localhost:{port}/board_games_collection.html')
            
            # Start server
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\n\n🛑 Server stopped by user")
        print(f"✓ Thank you for viewing your board game collection!")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use.")
            print(f"   Try a different port: python serve_collection.py --port 8001")
        else:
            print(f"❌ Error starting server: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def main():
    """Main function"""
    port = 8000
    
    # Check for custom port argument
    if len(sys.argv) > 1:
        if '--port' in sys.argv:
            try:
                port_index = sys.argv.index('--port') + 1
                if port_index < len(sys.argv):
                    port = int(sys.argv[port_index])
            except (ValueError, IndexError):
                print("❌ Invalid port number. Using default port 8000.")
        elif '--help' in sys.argv or '-h' in sys.argv:
            print("Board Game Collection Server")
            print("Usage: python serve_collection.py [--port PORT]")
            print("       python serve_collection.py --help")
            print("")
            print("Options:")
            print("  --port PORT    Port number to use (default: 8000)")
            print("  --help, -h     Show this help message")
            return
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir:
        os.chdir(script_dir)
    
    start_server(port)

if __name__ == "__main__":
    main()