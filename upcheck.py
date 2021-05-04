import requests
from time import sleep
import json
import email_alerts
from func_timeout import func_timeout, FunctionTimedOut , func_set_timeout
from datetime import datetime
import argparse
version = '1'

timeout = 5

def load_sites():
    with open("sites.json","r") as sites_file:
        site_list = json.load(sites_file)
        return site_list

@func_set_timeout(10)
def site_is_down(url=""):
    print("Trying to connect to: "+url)
    try:
        res = requests.get(url,timeout=timeout)
        if(res.status_code==200):
            print("Able to connect.")
        else:
            print("Something went wrong... "+res.status_code)
        return False
    except (requests. ConnectionError, requests. Timeout) as exception:
        print(exception)
        print("Unable to connect")
        return True

def send_alert(subject,message):
    with open("env.json") as env:
        creds = json.load(env)
        with open("dl.json") as dljson:
            dl = json.load(dljson)
            for contact in dl:
                print("Sending email alert to: "+contact['name'])
                email_alerts.send(auth=creds,subject=subject,message=message,destination=contact['email'])
    print("Sending alert!")

def monitor(site_list,interval=60):
    while(True):
        for site in site_list:
            print("""*** Checking site: {} *** """.format(site['name']))
            default_ports=['80','443']
            if('ports' in site):
                ports = site['ports']
                if(len(ports)==0): ports = default_ports
            else:
                ports = default_ports
            for port in ports:
                if(port in ['443']):
                    http = "https"
                else:
                    http = "http"
                url = """{}://{}:{}""".format(http,site['url'],port)
                print("Checking: "+url)
                down = False
                try:
                    down = site_is_down(url)
                except FunctionTimedOut:
                    print("Timed out connecting to site.")
                    down = True
                if(down):
                    now = datetime.now()
                    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
                    subject = """[ALERT]Site '{}' is down""".format(site['name'])
                    message = """Unable to connect to site: {}\nAt: {}\nURL: {}
                    """.format(site['name'],dt_string,url)
                    send_alert(subject,message)
                else:
                    print("Site is OK.")
        print("""Sleeping for {} seconds""".format(str(interval)))        
        sleep(interval) 

if(__name__=="__main__"):
    interval = 60
    parser = argparse.ArgumentParser(description="""Uptime check version {}""".format(version))
    parser.add_argument("-V", "--version", help="program version", action="store_true")
    parser.add_argument("-t", "--test", help="test mode", action="store_true")
    parser.add_argument("-i", "--interval", help="interval in seconds")
    args = parser.parse_args()
    if(args.test):
        print("Running in test mode")
        exit(0)
    elif(args.version):
        print("Running Twitter Bot Version %s"%(version))
    elif(args.interval):
        print("Setting interval to: "+args.interval)
        interval = int(args.interval)
    sites = load_sites()
    monitor(sites,interval)