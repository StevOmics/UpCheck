import sys
import requests
from time import sleep
import json
import email_alerts
from func_timeout import func_timeout, FunctionTimedOut , func_set_timeout
from datetime import datetime
import argparse
version = '1.0.0'
timeout = 10
retry_delay = 60

def load_sites():
    with open("sites.json","r") as sites_file:
        site_list = json.load(sites_file)
        return site_list

def timestamp():
    now = datetime.now()
    return now.strftime("%d/%m/%Y %H:%M:%S")

def send_alert(subject,message):
    with open("env.json") as env:
        creds = json.load(env)
        with open("dl.json") as dljson:
            dl = json.load(dljson)
            for contact in dl:
                print("Sending email alert to: "+contact['name'])
                email_alerts.send(auth=creds,subject=subject,message=message,destination=contact['email'])

@func_set_timeout(30)
def url_down(url):
    res = requests.get(url,timeout=timeout)
    if(res.status_code==200):
        print("URL verified: "+url)
        # return res.status_code
        return False
    else:
        print("Something went wrong... "+res.status_code)
        # return res.status_code
        return True

def format_url(url,http="http",port=None):
    url = url.lower()
    if('http' not in url):
        url = http+"://"+url
    if(port):
        url = url + ":"+port
    return url

def check_site(site,retries = None,email=False):
    if(not retries):retries = 1
    down = True   
    message = "Status for site: "+site['name']
    message = message + "\nAttempts for this site: "+str(retries)
    if('ports' in site):
        for port in site['ports']:
            if(port in ['443']): http = 'https'
            else: http = 'http'
            for i in range(retries):
                check_url = format_url(site['url'],http,port)
                message = message + "\n[Error]: Attempt "+str(i+1)
                message = message + " for URL: "+check_url
                try:
                    down = url_down(check_url)
                    break
                except FunctionTimedOut:
                    message = message + "\n[Error]: Connection timed out to URL: "+check_url
                    down = True
                except Exception as e:
                    message = message + "\n[Error]: Unable to connect to URL: "+check_url
                    message = message + "\n[Error]:" +str(e)
                    down = True
                print(message)
                print("Waitng %i seconds to try again."%(retry_delay))
                sleep(retry_delay)
    else:
        for i in range(retries):
            check_url = format_url(site['url'])
            message = message + "\n[Error]: Attempt "+str(i+1)
            message = message + " for URL: "+check_url
            try:
                down = url_down(check_url)
                break
            except FunctionTimedOut:
                message = message + "\n[Error]: Connection timed out to URL: "+site['url']
                down = True
            except Exception as e:
                message = message + "\n[Error]: Unable to connect to URL: "+site['url']
                message = message + "\n[Error]: " +str(e)
                down = True
            print(message)
            print("Waitng %i seconds to try again."%(retry_delay))
            sleep(retry_delay)
    if(down):
        subject = """[ALERT]Site '{}' is down!""".format(site['name'])
        message = message+"""\n[Error]: Time was: {}\n""".format(timestamp())
        print("Sending alert for this site.")
        print("Message: ")
        print(message)
        if(email): send_alert(subject,message)
        return False
    else:
        return True

def monitor(site_list,interval=None,retries=None,email=False):
    if(not retries): retries = 1
    if(interval):
        print("Running in continuous mode.")
        send_alert("UpCheck: Monitoring started","Upcheck monitoring started at: "+timestamp())
        while(True):
            for site in site_list:
                check_site(site,retries,email)
            sleep(interval) 
    else:
        print("Running once.")
        for site in site_list:
            check_site(site,retries,email)
                
if(__name__=="__main__"):
    interval = None
    retries = None
    if(len(sys.argv)==2):
        print("Running in single-site mode.")
        url = sys.argv[1]
        sites=[{"name":url,"url":url}]
        monitor(sites,None,1,False)
    else:
        print("Checking sites in specified sites file.")
        parser = argparse.ArgumentParser(description="""Uptime check version {}""".format(version))
        parser.add_argument("-V", "--version", help="program version", action="store_true")
        parser.add_argument("-t", "--test", help="test mode", action="store_true")
        parser.add_argument("-i", "--interval", help="interval in seconds")
        parser.add_argument("-u", "--url", help="url")
        parser.add_argument("-r", "--retries", help="Number of retries")
        args = parser.parse_args()
        if(args.test):
            print("Running in test mode")
            exit(0)
        elif(args.version):
            print("Running Twitter Bot Version %s"%(version))
        elif(args.interval):
            print("Setting interval to: "+args.interval)
            interval = int(args.interval)
        elif(args.retries):
            retries = int(args.retries)
        sites = load_sites()
        monitor(sites,interval,retries,True)