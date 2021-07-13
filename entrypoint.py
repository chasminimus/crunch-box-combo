import subprocess
import signal
import os

os.chdir("/home/minimus/cbc/")
# create bot subprocess
print("Starting bot...")
bot_instance = subprocess.Popen(["python3", "./bot/start.py"],
                                start_new_session=True)

# create flask subprocess
print("Starting Flask server...")

# can also just set FLASK_APP but then i think the autoreloader will detect EVERY .py change in the project lol???
os.chdir("./web/backend/")
# os.environ["FLASK_APP"] = "web.backend.app"
os.environ["FLASK_ENV"] = "development"
flask_server = subprocess.Popen(["flask", "run"],
                                start_new_session=True)

# loop control
try:
    print("CTRL-C to quit")
    while True:
        pass
    
except KeyboardInterrupt:
    # need to kill the process group since it spawns its own child processes presumably
    print("Shutting down Flask server...")
    os.killpg(os.getpgid(flask_server.pid), signal.SIGTERM)
    print("Shutting down bot...")
    os.killpg(os.getpgid(bot_instance.pid), signal.SIGTERM)
