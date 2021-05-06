import sys
import requests
import socket
import uuid
import random
import string
from icmplib import ping, multiping, traceroute, resolve, Host, Hop
from time import sleep
import json
import email_alerts
from func_timeout import func_timeout, FunctionTimedOut , func_set_timeout
from datetime import datetime
alert_ids = {}
import argparse
settings = {
    "version":"1.0.0",
    "auth_file":"env.json",
    "dl_file":"dl.json",
    "sites_file":"sites.json",
    "retry_delay":60,
    "timeout":10,
    "default_interval":60
}
helptext = """Uptime check version 1.0.0 
usage: upcheck.py [-h] [-i INTERVAL] [-r RETRIES] [-a AUTH] [-d DL] [-s SITES]
    optional arguments:
    -i INTERVAL, --interval INTERVAL interval in MINUTES
    -r RETRIES, --retries RETRIES Number of retries
    -a AUTH, --auth AUTH  Auth file
    -d DL, --dl Email distribution list file
    -s SITES, --sites SITES Sites list file
    """

def load_sites(sites_file="sites.json"):
    with open(sites_file,"r") as sf:
        site_list = json.load(sf)
        return site_list

def timestamp():
    now = datetime.now()
    return now.strftime("%d/%m/%Y %H:%M:%S")

def getid():
    global alert_ids
    while True:
        id= 'D'+''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(5))
        if(id not in alert_ids): #make certain ids are unique
            alert_ids[id] = True
            return id
    # return uuid.uuid1().hex

def minToSec(mins):
    return mins*60

def secToMin(sec):
    return int(sec)/60

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

def socket_connection(server, port=None, timeout=settings['timeout']):
    print("Pinging server "+server)
    if(not port):
        url_split = server.split(':')
        if(len(url_split)==3):
            server=url_split[0]+url_split[1]
            port = int(url_split[2])
        elif(len(url_split)==2):
            server = url_split[0]
            port = int(url_split[1])
        else:
            port = 80
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((server, port))
        s.close()
    except OSError as error:
        return False
    else:
        return True

def ping_server(address): #requires sudo
    try:
        ping(address)
        True
    except Exception as e:
        print(e)
        return False

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

def get_all_paths(site):
    paths = {}
    if('ports' in site):
        port_urls = []
        for port in site['ports']:
            if(port in ['443']): http = 'https' #secure ports https
            else: http = 'http'
            port_urls.append(format_url(site['url'],http,str(port))) #note: http is only added if it isn't already in the url.
    else:
        port_urls = [format_url(site['url'])] 
    if('paths' in site): #append all paths for all ports if specified
        sub_paths = site['paths']
        sub_paths.append('/')
    else:
        sub_paths = ['/']
    path_urls = []
    for path in sub_paths:
        for port_url in port_urls: #add each url already defined
            if(path[0:1] != '/'): full_path = port_url+'/'+path
            else: full_path = port_url+path
            paths[full_path]=True
    return paths.keys()

def check_site(site,retries = 1,email=False,auth_file=None,dl_file=None,sites_file=None,issue=None):
    down = True   
    message = "Site: "+site['name']
    check_paths = get_all_paths(site)
    for check_url in check_paths:
        for attempt in range(1,retries+1):
            if(retries > 1): message = message + "\n[Connection Test]: Attempt %i of %i for URL: %s"%((attempt),retries,check_url)
            else:            message = message + "\n[Connection Test]: Attempt to connect to URL: %s"%(check_url)
            try:
                down = url_down(check_url)
                message = message + "\n[Connection Test]: Connection successful."
                break
            except FunctionTimedOut:
                message = message + "\n[Error]: Connection timed out."
                down = True
            except Exception as e:
                message = message + "\n[Error]: Unable to connect."
                message = message + "\n[Error]:" +str(e)
                # ping = ping_server(check_url)
                # if(not ping): message = message + "\n[Error]: Server was unpingable"
                # else: message = message + "\n Ping was successful"
                down = True
            if(down and attempt < retries):
                print(message)
                print("Problem connecting to this site. Attempt %i of %i Waiting %i minutes to try again."%((attempt),retries,secToMin(settings['retry_delay'])))
                sleep(settings['retry_delay'])
    if(down):
        if(not issue): issue = getid()
        subject = """[{}] Site '{}' is down!""".format(issue,site['name'])
        message = message+"""\n[{}] Current time: {} """.format(issue,timestamp())
        print("Sending alert for this site.")
        print("Message: ")
        print(message)
        if(email): 
            try:
                send_alert(subject,message,auth_file,dl_file)
            except FunctionTimedOut:
                print("Unable to send alert (timed out).")
        return issue
    else:
        if(issue):
            subject = """CLOSED[{}] Site '{}' is back up! [{}] is closed.""".format(issue,site['name'],issue)
            message = message + """\n Issue closed [{}]""".format(issue)
            alert_ids[issue]=False 
            if(email): 
                try:
                    send_alert(subject,message,auth_file,dl_file)
                except FunctionTimedOut:
                    print("Unable to send alert (timed out).")
        return None

def monitor(site_list=None,interval=None,down_interval=None,retries=None,email=False,auth_file=None,dl_file=None):
    if(not auth_file): auth_file = settings['auth_file']
    if(not dl_file): dl_file = settings['dl_file']
    if(not site_list):  site_list = load_sites(settings['sites_file'])
    for site in site_list:
        site['issue'] = None
    if(not retries): retries = 1
    if(not interval):
        print("Running once.")
        for site in site_list:
            check_site(site,retries,email,auth_file,dl_file)
    else: #run in interval mode if specified
        if(not down_interval): down_interval = interval/2 #If not specified, check twice as often if site is down 
        print("Running in continuous mode.")
        try: #I'm including try/except blocks for all email alerts so that the program won't fail if it can't do email
            message = """UpCheck monitoring started at: {} \nThe following sites are being monitored: \n{}\nThis script will send alerts for any observed loss of connectivity.""".format(timestamp(),("\n".join([ "  "+str(i+1)+": "+site['name'] for i,site in enumerate(site_list)])))
            print(message)
            send_alert("UpCheck Monitoring started",message,auth_file,dl_file)
        except FunctionTimedOut:
            print("Unable to send alert (timed out).")
        while(True):
            next_interval = interval
            for site in site_list:
                #note that if an issue is reported, the id will be generated, stored in the issue field
                #and then provided as a parameter. When it is cleared, an all-clear message will be sent
                site['issue'] = check_site(site=site,retries=retries,email=email,auth_file=auth_file,dl_file=dl_file,issue = site['issue'])
                if(site['issue']): next_interval = down_interval
            print("Waiting for %i minutes until next check."%(secToMin(next_interval)))
            sleep(next_interval) 

                
if(__name__=="__main__"):
    interval = None
    down_interval = None
    retries = None
    if(len(sys.argv)==2):
        if(sys.argv[1]=='-h'):
            print(helptext)
            exit(0)
        else:
            print("Running in single-site mode.")
            url = sys.argv[1]
            sites=[{"name":url,"url":url}]
            monitor(sites,None,1,False)
    else:
        print("Check site status.")
        parser = argparse.ArgumentParser(description="""Uptime check version {}""".format(settings['version']))
        parser.add_argument("-i", "--interval", help="interval in MINUTES")
        parser.add_argument("-d", "--down-interval", help="down-interval in MINUTES--a shorter check interval for when a site is down")
        parser.add_argument("-r", "--retries", help="Number of retries")
        parser.add_argument("-a", "--auth", help="Auth file")
        parser.add_argument("-l", "--dl", help="Email distribution list file")
        parser.add_argument("-s", "--sites", help="Sites list file")
        args = parser.parse_args()
        if(args.interval):
            print("Setting interval to: "+args.interval)
            interval = minToSec(int(args.interval))
        else:
            interval = minToSec(settings['default_interval'])
        if(args.down_interval):
            down_interval = minToSec(int(args.down_interval))
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
        monitor(site_list=site_list,interval=interval,down_interval = down_interval,retries=retries,email=True,auth_file=auth_file,dl_file=dl_file)