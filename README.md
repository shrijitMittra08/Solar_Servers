# SolarServers
How to test:
1. Download project to local system
2. Inside main folder, open terminal and run
# "uvicorn SolarServers_server:app --port 8000"
3. Inside frontend, open terminal and run
# "python -m http.server 8000"
4. In browser, specifically go to
# "http://localhost:8000 or http://localhost:8000/"
5. DO NOT directly open index.html.

### Troubleshooting
- If you see only a white sphere: Backend server isn't running
- If page doesn't load: Frontend server isn't running
- Check console for WebSocket connection errors

> On top left, a small green square will appear. It is the placeholder for HUD

## Features
1. Real-time network connection monitoring
2. AI-powered threat detection
3. 3D visualization of network activity
4. Browser connection tracking with improved domain names
5. Process monitoring and system information

# Changelog
1. Added planets to show connections to sites via browser
2. Added on-click shown tooltips for planets, showing connection details
3. Integrated AI engine for real-time threat detection using machine learning on network connections
4. Built FastAPI backend with WebSocket support for streaming connection data
5. Created web frontend with HTML, CSS, and JavaScript for visualizing network activity
6. Added core scanning module for monitoring processes, connections, and system info
7. Included AI training script and NSL-KDD datasets for model development
8. Added requirements file with all Python dependencies
9. Suppressed sklearn warnings to clean up server output
