import os

from crontab import CronTab

current_dir = os.path.dirname(os.path.abspath(__file__))

cron = CronTab()

job = cron.find_comment('mzcontrol')
if not list(job):
    command = 'python3 ' + current_dir + '/' + 'job_control.py'
    job = cron.new(command=command, comment='mzcontrol')
    job.setall('0 0 * * *') 
    job.enable(False)
    
job = cron.find_comment('mztransfer')
if not list(job):
    command = 'python3 ' + current_dir + '/' + 'job_transfer.py'
    job = cron.new(command=command, comment='mztransfer')
    job.setall('0 2,10,18 * * *') 
    job.enable(False)    
    
job = cron.find_comment('mzteam')
if not list(job):
    command = 'python3 ' + current_dir + '/' + 'job_team.py'
    job = cron.new(command=command, comment='mzteam')
    job.setall('15 7 * * *') 
    job.enable(False)    