import project
#import subprocess

#command = 'service cron start'
#result = subprocess.run(command, shell=True, capture_output=True, text=True)

app = project.create_app()

app.run(host="0.0.0.0", port=7020)

