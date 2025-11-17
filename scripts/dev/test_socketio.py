"""Test what async modes are available for SocketIO"""
import sys
from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)

print("Testing SocketIO async modes...")

# Try different async modes
modes = ['threading', 'eventlet', 'gevent', 'gevent_uwsgi', None]

for mode in modes:
    try:
        if mode:
            print(f"\nTrying async_mode='{mode}'...")
        else:
            print(f"\nTrying async_mode=None (auto-detect)...")

        socketio = SocketIO(app, cors_allowed_origins="*", async_mode=mode)
        print(f"  [SUCCESS] Using: {socketio.async_mode}")

        # Clean up
        del socketio
    except ValueError as e:
        print(f"  [FAILED] {e}")
    except ImportError as e:
        print(f"  [IMPORT ERROR] {e}")
    except Exception as e:
        print(f"  [ERROR] {e}")

print("\nConclusion: Use the successful mode in your code!")