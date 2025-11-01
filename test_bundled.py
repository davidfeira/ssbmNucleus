"""Test to see what's available in PyInstaller context"""
import sys
import importlib

print("Testing module availability...")
print(f"Is frozen (bundled)?: {getattr(sys, 'frozen', False)}")

modules_to_test = [
    'threading',
    'queue',
    'simple_websocket',
    'engineio',
    'socketio',
    'flask',
    'flask_socketio',
    'werkzeug'
]

print("\nChecking modules:")
for mod in modules_to_test:
    try:
        importlib.import_module(mod)
        print(f"  {mod}: Available")
    except ImportError as e:
        print(f"  {mod}: NOT AVAILABLE - {e}")

print("\nTrying to create SocketIO with threading mode...")
try:
    from flask import Flask
    from flask_socketio import SocketIO

    app = Flask(__name__)
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    print(f"SUCCESS: SocketIO created with mode: {socketio.async_mode}")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()