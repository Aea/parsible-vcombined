import os
import shutil
import datetime
import traceback
import pprint

def setup(path):
    base, file = os.path.split(path)
        
    if not os.path.exists(base):
        os.mkdir(base)

    if not os.path.exists(file):
        open(path, 'a').close()
        
    return path    

def write(path, value):
    fp = open(path, "a")
    record = "%s\t%s\n" % (datetime.datetime.now().isoformat(), value)
    fp.write(record)
    fp.close()
    
def urlize(data):
    components = [data["host"], data["path"],]
    
    if len(data.get("query", "")):
        components.extend(["?", data["query"],])
        
    return "".join(components)
    
def exceptional(fn):
    """
    Parsible seems to be trapping all exceptions, print them out and attempt 
    to re-raise
    
    """
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            print traceback.format_exc()
            raise
    return wrapped

@exceptional
def process_hosts(data):    
    path = "/var/log/parsible/hosts.log"
    
    try:
        cache = process_hosts.cache
    except AttributeError:
        cache = process_hosts.cache = {"hosts": set([])}
        setup(path)
        
        # Retrieve Data
        fp = open(path, "r")
        map(lambda x: cache["hosts"].add(x.split("\t")[1]), fp.read().splitlines())
        fp.close()
        
    if "host" not in data:
        print "Invalid Line", data
        
    if data["host"] not in cache["hosts"]:
        cache["hosts"].add(data["host"])
        write(path, data["host"])
        
@exceptional
def process_integration(data):        
    # Skip Non-HTTP
    if "response_code" not in data:
        return
    
    # Skip Invalid Codes
    try:
        code = int(data["response_code"])
    except ValueError:
        return
    
    # Skip Monitoring
    if "Rackspace" in data.get("client", ""):
        return
    
    # Skip Non-Integration Items
    if "include.js" not in data["path"] and "/js/site" not in data["path"]:
        return
    
    # Process
    _process_integration_all(data, code)
    _process_integration_error(data, code)
    
@exceptional
def process_html_paths(data):
    path = "/var/log/parsible/html-unique.log"
    
    try:
        cache = process_html_paths.cache
    except AttributeError:
        cache = process_html_paths.cache = {"urls": set([])}
        setup(path)
    
        # Retrieve Data
        fp = open(path, "r")
        map(lambda x: cache["urls"].add(x.split("\t")[2]), fp.read().splitlines())
        fp.close()
    
    # Skip non-html
    if "text/html" in data.get("content_type", ""):
        return
    
    # Skip Invalid Codes
    try:
        code = int(data["response_code"])
    except ValueError:
        return
    except KeyError:
        return
    
    # Check Host
    if "host" not in data:
        print "Invalid Line", data
        
    if data["host"] not in ("www.clientchatlive.com", "clientchatlive.com"):
        return
                
    url = "".join([data["host"], data["path"],])
    
    if url in cache["urls"]:
        return
    
    cache["urls"].add(url)
    write(path, "%d\t%s" % (code, url))

def _process_integration_all(data, code):
    path = "/var/log/parsible/integration-unique.log"
    
    try:
        cache = _process_integration_all.cache
    except AttributeError:
        cache = _process_integration_all.cache = {"urls": set([])}
        setup(path)
    
        # Retrieve Data
        fp = open(path, "r")
        map(lambda x: cache["urls"].add(x.split("\t")[2]), fp.read().splitlines())
        fp.close()
                
    url = urlize(data)
    
    if url in cache["urls"]:
        return
    
    cache["urls"].add(url)
    write(path, "%d\t%s" % (code, url))
        
def _process_integration_error(data, code):
    path = "/var/log/parsible/integration-error.log"
    
    try:
        cache = _process_integration_error.cache
    except AttributeError:
        cache = _process_integration_error.cache = {}
        setup(path)
        
    if code == 200:
        return
        
    write(path, "%d\t%s\t%s" % (code, urlize(data), data.get("referrer", "")))
