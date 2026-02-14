from fastapi import FastAPI
import psutil
import time
import json

app=FastAPI()

SESSION=[]



# Record Network Connections
@app.get("/record")
def record():
    connections = psutil.net_connections()
    count=0

    for c in connections:
        if c.raddr:
            event = {
                "timestamp": time.ctime(),
                "remote_ip": c.raddr.ip,
                "remote_port": c.raddr.port,
                "status": "NORMAL"
            }

            # Simple anomaly rule
            if c.raddr.port > 10000:
                event["status"] = "SUSPICIOUS"

            SESSION.append(event)
            count += 1

    return {"recorded_events": count}


# Save Session to JSON
@app.get("/save")
def save():
    with open("session.json", "w") as f:
        json.dump(SESSION, f, indent=4)

    return {"message": "Session saved successfully"}


# Replay Session
@app.get("/replay")
def replay():
    return SESSION



# Terminate Safe Process
@app.get("/terminate/{pid}")
def terminate(pid: int):
    try:
        p = psutil.Process(pid)

        SAFE = ["notepad.exe", "calc.exe"]

        if p.name().lower() not in SAFE:
            return {"error": "Blocked for safety"}

        p.terminate()
        return {"message": f"{p.name()} terminated"}

    except:
        return {"error": "Invalid PID"}
