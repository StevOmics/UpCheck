import sys
import requests
from time import sleep
import json
import email_alerts
from func_timeout import func_timeout, FunctionTimedOut , func_set_timeout
from datetime import datetime
import argparse
settings = {
    "version":"1.0.0",
    "auth_file":"env.json",
    "dl_file":"dl.json",
    "sites_file":"sites.json",
    "retry_delay":60,
    "timeout":10
}

def load_sites(sites_file="sites.json"):
    with open(sites_file,"r") as sf:
        site_list = json.load(sf)
        return site_list

def timestamp():
    now = datetime.now()
    return now.strftime("%d/%m/%Y %H:%M:%S")

def minToSec(mins=1):
    return mins*60

def format_url(url,http="http",port=None):
    url = url.lower()
    if('http' not in url):
        url = http+"://"+url
    if(port):
        url = url + ":"+port
    return url

@func_set_timeout(300) #function times out after 5 minutes for sending all email alerts.
def send_alert(subject,message,auth_file="env.json",dl_file="dl.json"):
    with open(auth_file) as env:
        creds = json.load(env)
        with open(dl_file) as dljson:
            dl = json.load(dljson)
            for contact in dl:
                print("Sending email alert to: "+contact['name'])
                #Can fail on individual emails
                try:
                    email_alerts.send(auth=creds,subject=subject,message=message,destination=contact['email'])
                except Exception as e:
                    print("Sending mail to %s failed."%(contact['name']))
                    print(e)

@func_set_timeout(30)
def url_down(url):
    res = requests.get(url,timeout=settings['timeout'])
    if(res.status_code==200):
        print("URL verified: "+url)
        # return res.status_code
        return False
    else:
        print("Something went wrong... "+res.status_code)
        # return res.status_code
        return True

def check_site(site,retries = 1,email=False,auth_file=None,dl_file=None,sites_file=None):
    down = True   
    message = "Alert: An issue was encountered in attempting to connect to the following site: "+site['name']
    message = message + "\nAttempts for this site: "+str(retries)
    if('ports' in site):
        check_urls = []
        for port in site['ports']:
            if(port in ['443']): http = 'https'
            else: http = 'http'
            check_urls.append(format_url(site['url'],http,port)) #note: http is only added if it isn't already in the url.
    else:
        check_urls = [format_url(site['url'])] #if no ports specified then assume it's already a complete URL
    for check_url in check_urls:
        for attempt in range(1,retries+1):
            message = message + "\n[Error]: Attempt %i of %i"%((attempt),retries)
            message = message + " for URL: "+check_url
            try:
                down = url_down(check_url)
                break
            except FunctionTimedOut:
                message = message + "\n[Error]: Connection timed out to URL: "+check_url+"\n"
                down = True
            except Exception as e:
                message = message + "\n[Error]: Unable to connect to URL: "+check_url
                message = message + "\n[Error]:" +str(e)+"\n"
                down = True
            if(down and attempt < retries):
                print(message)
                print("Problem connecting to this site. Attempt %i of %i Waiting %i seconds to try again."%((attempt),retries,settings['retry_delay']))
                sleep(settings['retry_delay'])
    if(down):
        subject = """[ALERT]Site '{}' is down!""".format(site['name'])
        message = message+"""\n[Error]: Time was: {}\n""".format(timestamp())
        print("Sending alert for this site.")
        print("Message: ")
        print(message)
        if(email): 
            try:
                send_alert(subject,message,auth_file,dl_file)
            except FunctionTimedOut:
                print("Unable to send alert (timed out).")
        return False
    else:
        return True

def monitor(site_list=None,interval=None,retries=None,email=False,auth_file=None,dl_file=None):
    if(not auth_file): auth_file = settings['auth_file']
    if(not dl_file): dl_file = settings['dl_file']
    if(not site_list):  site_list = load_sites(settings['sites_file'])
    if(not retries): retries = 1
    if(interval):
        print("Running in continuous mode.")
        try:
            message = """UpCheck monitoring started at: {} \nThe following sites are being monitored: \n{}\nThis script will send alerts for any observed loss of connectivity.""".format(timestamp(),("\n".join([ "  "+str(i+1)+": "+site['name'] for i,site in enumerate(site_list)])))
            print(message)
            send_alert("UpCheck: Monitoring started",message,auth_file,dl_file)
        except FunctionTimedOut:
            print("Unable to send alert (timed out).")
        while(True):
            for site in site_list:
                check_site(site,retries,email,auth_file,dl_file)
            print("Waiting for %i seconds until next check."%(interval))
            sleep(interval) 
    else:
        print("Running once.")
        for site in site_list:
            check_site(site,retries,email,auth_file,dl_file)
                
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
        parser = argparse.ArgumentParser(description="""Uptime check version {}""".format(settings['version']))
        parser.add_argument("-V", "--version", help="program version", action="store_true")
        parser.add_argument("-t", "--test", help="test mode", action="store_true")
        parser.add_argument("-i", "--interval", help="interval in seconds")
        parser.add_argument("-u", "--url", help="url")
        parser.add_argument("-r", "--retries", help="Number of retries")
        parser.add_argument("-a", "--auth", help="Auth file")
        parser.add_argument("-d", "--dl", help="Email distribution list")
        parser.add_argument("-s", "--sites", help="Sites list")
        args = parser.parse_args()
        if(args.test):
            print("Running in test mode")
            exit(0)
        elif(args.version):
            print("Running Twitter Bot Version %s"%(version))
        elif(args.interval):
            print("Setting interval to: "+args.interval)
            interval = int(args.interval)
        if(args.retries):
            retries = int(args.retries)
        if(args.auth):
            auth_file = args.auth
        else:
            auth_file = settings['auth_file']
        if(args.dl):
            dl_file = args.dl
        else:
            dl_file = settings['dl_file']
        if(args.sites):
            sites_file=args.sites
        else:
            sites_file=settings['sites_file']
        site_list = load_sites(sites_file)
        monitor(site_list=site_list,interval=interval,retries=retries,email=True,auth_file=auth_file,dl_file=dl_file)