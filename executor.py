import docker
import os
import tempfile
import threading
import datetime
import time

# Initialize the client from environment variables
client = docker.from_env()

def run_code(code : str):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name
        
    run = None
    timed_out = False
    logs = []
    report = {"output" : "", "status" : None, "execution_time" : None}
        
    try:
        run = client.containers.run(
    "python:3.11-slim", 
    "python /code/solution.py", 
    remove=False, 
    volumes={temp_path: {"bind": "/code/solution.py", "mode": "ro"}},
    user="nobody", 
    network_disabled=True, 
    detach=True, 
    
    # Existing CPU/Process limits
    pids_limit=50, 
    cpu_quota=50000, 
    cpu_period=100000,
    
    # NEW: Stop them from eating all your RAM
    mem_limit="128m",             
    memswap_limit="128m",         
    
    # NEW: Stop them from filling up your hard drive
    read_only=True,               
    
    # NEW: Drop all Linux capabilities to prevent container escape
    cap_drop=["ALL"],             
    security_opt=["no-new-privileges"]
)

        
        start = time.time()
        
        def kill_after_timeout():
            nonlocal timed_out
            timed_out = True
            try:
                run.kill()
            except:
                pass
            
        timer = threading.Timer(5.0, kill_after_timeout)
        timer.start()
        
        for log in run.logs(stream=True, follow=True):
            logs.append(log.decode())
            if timed_out:
                break
        
        
        if not timed_out:
            status = run.wait().get('StatusCode')
        else:
            status = -1
        
        timer.cancel()
        execution_time = round(time.time() - start, 2)
        output = "".join(logs)
        
        if timed_out:
            report_status = "TIMEOUT"
            report["output"] = "// TIMEOUT: Execution exceeded 5 seconds\n" + report.get("output")
        elif status == 0:
            report_status = "SUCCESS"
        else:
            report_status = "ERROR"
            
        
        report = {"output" : output, "status" : report_status, "execution_time" : execution_time}
                    
        if timed_out:
            report["output"] = "// TIMEOUT: Execution exceeded 5 seconds\n" + report.get("output")
            
        if not report.get("output"):
            report["output"] = "(no output)"
        
    except docker.errors.ContainerError as e:
        report = {"output" : e.stderr.decode(), "status" : "ERROR", "execution_time": None}
    
        
    finally:
        if run:
            try:
                run.remove(force=True)
            except:
                pass
        os.unlink(temp_path)
        
    return report
    