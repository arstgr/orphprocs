#!/usr/bin/python3.6

## percent instantaneous VM cpu load above which the test reports failure
INST_TRSHLD = 20.0
## percent average VM cpu load above which the test reports failure
AVG_TRSHLD = 10.0

import sys
import string
import math
import os
import subprocess 
import json
import re

print("running the health check script")

# obtains list of available VMs (currently PBS, should be extended to slurm as well)
def find_VMs():
    vmnames = []
    o, e = subprocess.getstatusoutput('pbsnodes --version')
    if o == 0:
        cmd = "pbsnodes -avS | grep free | awk -F ' ' '{print $1}'"
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        o, e = proc.communicate()
        o = o.decode('ascii')
        vmnames = list(o.split('\n'))
        del vmnames[-1]

    cmd = "hostname"
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    o, e = proc.communicate()
    o = o.decode('ascii')
    name = list(o.split('\n'))
    del name[-1]

    vmnames.insert(0,name[0])

    with open('hosts.txt', 'w') as f:
        for i in vmnames:
                f.write("%s\n" % i)

    return vmnames

# checkif pssh is installed, if not then install pssh
def check_pssh():
    o, e = subprocess.getstatusoutput('pssh --version')
    if o != 0:
        os.system('sudo yum install pssh -y')

#checks if the hosts accept SSH, if not, it removes them from the host list
def check_VMs_ssh():
    with open('hosts.txt') as f:
        hosts = f.read().splitlines()

    cmd = "pssh -p 194 -t 0 -i -h hosts.txt 'echo $(hostname)' | grep 'FAILURE' | awk '{print $4}'"
    procs = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    o, e = procs.communicate()
    o = o.decode('ascii')
    o = re.split('[, \t \n]',o)
    failed_hosts = list(filter(('').__ne__,o))
    failed_hosts = list(set(failed_hosts))

    hosts = [i for i in hosts if i not in failed_hosts]

    with open('hosts.txt', 'w') as f:
        for i in hosts:
            f.write("%s\n" % i)

    return failed_hosts

# checks the cpu load for a all the available VMs (currently only pbs, should be extended to slurm as well) 
# reports the process taking up the most of cpu on each VM
# currently has no error handling, pssh may return an error (i.e. VM not responding) which should be handled properly
# output is a dictionary
def multi_VM_inst_test():
    output = {}
    cmd = "pssh -p 194 -t 0 -i -h hosts.txt 'sudo ps -Ao user,uid,comm,pid,ppid,pcpu,pmem --sort=-%cpu | head -n 2' | awk -F ' ' '{print $4; getline; getline; print $1, $2, $3, $4, $5, $6, $7}'"
    procs = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    o, e = procs.communicate()
    o = o.decode('ascii')
    o = re.split('[, \t \n]',o)
    temp = list(filter(('').__ne__,o))
    for i in range(0,len(temp),8):
            tmp = {}
            tmp['USER'] = temp[i+1]
            tmp['UID'] = temp[i+2]
            tmp['COMMAND'] = temp[i+3]
            tmp['PID'] = temp[i+4]
            tmp['PPID'] = temp[i+5]
            tmp['CPU%'] = temp[i+6]
            tmp['MEM%'] = temp[i+7]
            output[temp[i]] = tmp
    
    return output

# reports the average cpu load (1min, 5min and 15min) for a all the available VMs (currently only pbs, should be extended to slurm as well)
# currently has no error handling, pssh may return an error (i.e. VM not responding) which should be handled properly
# output is added to the result dictionary
def multi_VM_uptime_test(results):
    cmd = "pssh -p 194 -t 0 -i -h hosts.txt uptime | awk -F ' ' '{print $4 $10 $11 $12}'"
    procs = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    o, e = procs.communicate()
    o = o.decode('ascii')
    o = re.split('[, \n]',o)
    o = list(filter(('days').__ne__,o))
    temp = list(filter(('').__ne__,o))

    for i in range(0,len(temp),4):
            tmp = {}
            tmp['1min'] = temp[i+1] 
            tmp['5min'] = temp[i+2]
            tmp['15min'] = temp[i+3]
            results[temp[i]].update(tmp)
    
    return results #output

def check_VM_load(results, failed_hosts):
    for i in results.keys():
        if float(results[i]['5min']) >= float(AVG_TRSHLD) and float(results[i]['1min']) >= float(AVG_TRSHLD) and float(results[i]['CPU%']) >= float(INST_TRSHLD):
            results[i]['STATUS'] = 'FAILED'
        elif float(results[i]['1min']) >= float(AVG_TRSHLD) and float(results[i]['CPU%']) >= float(INST_TRSHLD):
            results[i]['STATUS'] = 'FAILED'
        elif float(results[i]['1min']) < float(AVG_TRSHLD) and float(results[i]['CPU%']) >= float(INST_TRSHLD): 
            results[i]['STATUS'] = 'TRANSIENT'
        else:
            results[i]['STATUS'] = 'PASSED'

    for i in failed_hosts:
        results[i] = {}
        results[i]['STATUS'] = 'SSH FAILED' 

    return results

def summarize_VM_load(results):
    summary = {}
    for i in results.keys():
        summary[i] = results[i]['STATUS']

    return summary

############################################################################################
check_pssh()
outputlist = find_VMs()

failed_hosts = check_VMs_ssh()

results = {}
results = multi_VM_inst_test()

results = multi_VM_uptime_test(results)
results = check_VM_load(results, failed_hosts)
summary = summarize_VM_load(results)

print("Test Summary")
json_summary = json.dumps(summary, indent = 4)
print(json_summary)

with open("VM_loads.json", "w") as outfile:
        json.dump(results, outfile, indent = 4)

with open("VM_loads_summary.json", "w") as outfile:
        json.dump(summary, outfile, indent = 4)
