from plugins.outputs.statsd import output_statsd_count

def process_hosts(line):
    try:
        process_hosts.hosts
    except AttributeError:
        process_hosts.hosts = set([])
    
    if "host" not in line:
        print "Invalid Line", line
        
    if line["host"] not in process_hosts.hosts:
        print line["host"]
        process_hosts.hosts.add(line["host"])