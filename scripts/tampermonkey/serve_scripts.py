#!/usr/bin/env python3
"""
HTTP Server for serving Tampermonkey userscripts
Serves .user.js files from the scripts/tampermonkey directory
with proper CORS headers for Tampermonkey access
"""

import os
import sys
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
class TampermonkeyScriptHandler(BaseHTTPRequestHandler):
    """HTTP request handler for serving Tampermonkey userscripts"""
    
    def __init__(self, *args, script_directory=None, **kwargs):
        self.script_directory = script_directory or os.path.dirname(os.path.abspath(__file__))
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests for userscript files"""
        parsed_path = urlparse(self.path)
        requested_file = parsed_path.path.lstrip('/')
        
        print(f"Serving request for: {requested_file}")
        
        # Send response with CORS headers for Tampermonkey access
        self.send_response(200)
        
        # Determine proper MIME type based on file extension
        if requested_file.endswith('.user.js'):
            content_type = 'application/javascript'  # Standard for userscripts
            print(f"🔧 LAYER 1: MIME type detected: {content_type} (Tampermonkey userscript)")
        elif requested_file.endswith('.js'):
            content_type = 'application/javascript'
            print(f"🔧 LAYER 1: MIME type detected: {content_type} (JavaScript)")
        else:
            content_type = 'text/plain'
            print(f"🔧 LAYER 1: MIME type detected: {content_type} (fallback)")
            
        self.send_header('Content-type', content_type)
        
        # Add CORS headers to allow Tampermonkey access
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        
        self.end_headers()
        
        # File existence checking and serving logic
        if not requested_file:
            self.wfile.write(b'// Tampermonkey Script Server - No file specified')
            return
            
        # Construct full file path
        file_path = os.path.join(self.script_directory, requested_file)
        
        # Check if file exists
        if not os.path.exists(file_path):
            # Comprehensive logging for file not found errors (LAYER 1)
            print(f"🔴 LAYER 1 ERROR: File not found")
            print(f"📄 LAYER 1: Requested: {requested_file}")
            print(f"📂 LAYER 1: Full path: {file_path}")
            print(f"📁 LAYER 1: Script directory: {self.script_directory}")
            print(f"🔗 LAYER 1: Failed URL: http://localhost:{getattr(self.server, 'server_port', 8080)}/{requested_file}")
            print(f"🕒 LAYER 1: Failed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Check if this is the critical autoOrder.user.js file
            if 'autoOrder' in requested_file.lower():
                print(f"💥 LAYER 1: CRITICAL ERROR - autoOrder.user.js not found! Tampermonkey updates will fail!")
                
            # List available files for debugging
            try:
                available_files = [f for f in os.listdir(self.script_directory) if f.endswith('.user.js')]
                if available_files:
                    print(f"📋 LAYER 1: Available .user.js files: {', '.join(available_files)}")
                else:
                    print(f"📋 LAYER 1: No .user.js files found in directory")
            except Exception as e:
                print(f"📋 LAYER 1: Error listing directory: {e}")
            
            self.wfile.write(f'// File not found: {requested_file}'.encode('utf-8'))
            return
            
        print(f"✅ LAYER 1: File exists, preparing to serve: {file_path}")
        
        # File reading with error handling
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            print(f"✅ LAYER 1: Successfully read file content ({len(file_content)} characters)")
        except UnicodeDecodeError as e:
            print(f"🔴 LAYER 1 ERROR: Unicode decode error reading {file_path}: {e}")
            self.wfile.write(f'// Error: Could not decode file as UTF-8: {requested_file}'.encode('utf-8'))
            return
        except IOError as e:
            print(f"🔴 LAYER 1 ERROR: IO error reading {file_path}: {e}")
            self.wfile.write(f'// Error: Could not read file: {requested_file}'.encode('utf-8'))
            return
        except Exception as e:
            print(f"🔴 LAYER 1 ERROR: Unexpected error reading {file_path}: {e}")
            self.wfile.write(f'// Error: Unexpected error reading file: {requested_file}'.encode('utf-8'))
            return
        
        # Special handling for autoOrder.user.js vs other scripts
        is_critical_file = 'autoOrder' in requested_file.lower()
        
        if is_critical_file:
            print(f"🔥 LAYER 1: CRITICAL FILE DETECTED - autoOrder.user.js")
            print(f"🔥 LAYER 1: Priority handling activated for trading script")
            
            # Add special headers for critical trading script
            self.send_header('X-Script-Type', 'trading-critical')
            self.send_header('X-Script-Priority', 'high')
            
            # Validate file content for critical autoOrder script
            if '// ==UserScript==' not in file_content:
                print(f"⚠️ LAYER 1: WARNING - autoOrder.user.js missing UserScript header!")
            if '@match' not in file_content and '@include' not in file_content:
                print(f"⚠️ LAYER 1: WARNING - autoOrder.user.js missing @match/@include directive!")
            if '@updateURL' not in file_content:
                print(f"⚠️ LAYER 1: WARNING - autoOrder.user.js missing @updateURL for auto-updates!")
                
            # Check for trading-specific content
            if 'autoTrade' in file_content or 'submitOrder' in file_content:
                print(f"✅ LAYER 1: Trading functions detected in autoOrder.user.js")
            else:
                print(f"⚠️ LAYER 1: WARNING - No trading functions found in autoOrder.user.js!")
                
        else:
            print(f"📄 LAYER 1: Standard userscript - {requested_file}")
            self.send_header('X-Script-Type', 'standard')
            self.send_header('X-Script-Priority', 'normal')
        
        # Serve the file content
        self.wfile.write(file_content.encode('utf-8'))
        
        # Comprehensive logging for successful file serving (LAYER 1)
        print(f"🟢 LAYER 1 SUCCESS: File served successfully")
        print(f"📄 LAYER 1: File: {requested_file}")
        print(f"📏 LAYER 1: Size: {len(file_content)} characters ({len(file_content.encode('utf-8'))} bytes)")
        print(f"🌐 LAYER 1: MIME Type: {content_type}")
        print(f"🔗 LAYER 1: Full URL: http://localhost:{getattr(self.server, 'server_port', 8080)}/{requested_file}")
        
        # Add timestamp for request tracking
        print(f"🕒 LAYER 1: Served at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Log if this is the critical autoOrder.user.js file
        if 'autoOrder' in requested_file.lower():
            print(f"⭐ LAYER 1: CRITICAL FILE - autoOrder.user.js served to Tampermonkey!")
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Override to customize logging"""
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")


class ScriptServer:
    """HTTP server for serving Tampermonkey userscripts"""
    
    def __init__(self, port=8080, script_directory=None):
        self.port = port
        self.script_directory = script_directory or os.path.dirname(os.path.abspath(__file__))
        self.server = None
        self.server_thread = None
        
    def start(self):
        """Start the HTTP server in a separate thread"""
        def make_handler(*args, **kwargs):
            return TampermonkeyScriptHandler(*args, script_directory=self.script_directory, **kwargs)
        
        self.server = HTTPServer(('localhost', self.port), make_handler)
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        
        print(f"Tampermonkey script server started on http://localhost:{self.port}")
        print(f"Serving scripts from: {self.script_directory}")
        
    def stop(self):
        """Stop the HTTP server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("Tampermonkey script server stopped")

if __name__ == "__main__":
    print("🚀 LAYER 1: Starting Tampermonkey Script Server")
    
    # Get script directory from command line or use default
    import sys
    script_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
    
    print(f"📁 LAYER 1: Script directory: {script_dir}")
    print(f"🌐 LAYER 1: Server port: {port}")
    
    # Create and start the script server
    try:
        server = ScriptServer(port=port, script_directory=script_dir)
        server.start()
        
        print(f"✅ LAYER 1: HTTP Server running at http://localhost:{port}")
        print(f"🔗 LAYER 1: Test URL: http://localhost:{port}/autoOrder.user.js")
        print(f"🔧 LAYER 1: Tampermonkey @updateURL ready")
        print("⏹️  LAYER 1: Press Ctrl+C to stop server")
        
        # Keep the server running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 LAYER 1: Shutting down server...")
            server.stop()
            print("✅ LAYER 1: Server stopped")
            
    except Exception as e:
        print(f"🔴 LAYER 1 ERROR: Failed to start server: {e}")
        sys.exit(1)