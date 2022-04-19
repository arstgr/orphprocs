#!/usr/bin/python3.6

## percent VM cpu load above which the test reports failure
TRSHLD = 20.0

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


# checks the cpu load for a all the available VMs (currently only pbs, should be extended to slurm as well) 
# reports the process taking up the most of cpu on each VM
# currently has no error handling, pssh may return an error (i.e. VM not responding) which should be handled properly
# output is a dictionary
def multi_VM_test():
    os.system('sudo yum install pssh -y')
    output = {}
    failed_nodes = []
    passed_nodes = []
    cmd = "pssh -p 194 -t 0 -i -h hosts.txt 'sudo ps -Ao user,uid,comm,pid,ppid,pcpu,pmem --sort=-%cpu | head -n 2'"
    procs = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    o, e = procs.communicate()
    o = o.decode('ascii')
    o = o.rstrip()
    o = o.lstrip()
    temp = list(o.splitlines())
    range(0,len(temp),3)
    for i in range(0,len(temp),3):
            result = [x.strip() for x in ((temp[i].lstrip()).rstrip()).split(' ')]
            #    result[2] = result[2].replace("[", "").replace("]","")
            result2 = [x.strip() for x in ((temp[i+2].lstrip()).rstrip()).split(' ')]
            result2 = list(filter(('').__ne__, result2))
            tmp = {}
            tmp['USER'] = result2[0]
            tmp['UID'] = result2[1]
            tmp['COMMAND'] = result2[2]
            tmp['PID'] = result2[3]
            tmp['PPID'] = result2[4]
            tmp['CPU%'] = result2[5]
            tmp['MEM%'] = result2[6]
            if float(tmp['CPU%']) > float(TRSHLD):
                tmp['RESULT'] = 'FAILED'
                failed_nodes.append(result[3])
            else:
                tmp['RESULT'] = 'PASSED'
                passed_nodes.append(result[3])
            output[result[3]] = tmp
    
    return output, failed_nodes, passed_nodes


def multi_VM_uptime_test():

#    cmd = "uptime | awk -F ' ' '{print $11 $12 $13}'"
#    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
#    o, e = proc.communicate()
#    o = o.decode('ascii')
#    o = re.split('[, \n]',o)
#    del o[-1]

    os.system('sudo yum install pssh -y')
    output = {}
    failed_nodes = []
    passed_nodes = []
    cmd = "pssh -p 194 -t 0 -i -h hosts.txt uptime | awk -F ' ' '{print $4 $10 $11 $12}'"
    procs = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    o, e = procs.communicate()
    o = o.decode('ascii')
    o = re.split('[, \n]',o)
    o = list(filter(('days').__ne__,o))
    temp = list(filter(('').__ne__,o))

    for i in range(0,len(temp),4):
            tmp = {}
            tmp['VM'] = temp[i]
            tmp['1min'] = temp[i+1] 
            tmp['5min'] = temp[i+2]
            tmp['15min'] = temp[i+3]
            if float(tmp['CPU%']) > float(TRSHLD):
                tmp['RESULT'] = 'FAILED'
                failed_nodes.append(result[3])
            else:
                tmp['RESULT'] = 'PASSED'
                passed_nodes.append(result[3])
            output[result[3]] = tmp
    



outputlist = find_VMs()
print(outputlist)

#can be run inside a loop to test individual VMs, maybe for error handling 
#ppc = single_VM_test(outputlist[0])
#print(ppc)


output = {}
failed_nodes = []
passed_nodes = []
output, failed_nodes, passed_nodes = multi_VM_test()

print("Output")
print(output)
print("Failed nodes:")
print(failed_nodes)
print("Passed nodes:")
print(passed_nodes)

#prints test results in json format
print("Test Result")
json_output = json.dumps(output, indent = 4)
print(json_output)

#outputs the test results into a json file
with open("VM_loads.json", "w") as outfile:
        json.dump(output, outfile, indent = 4)

