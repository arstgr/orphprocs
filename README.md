# orphprocs
Scripts to identify the orphan processes on HPC clusters

## Getting Started
To run the script use
```

```
The input arguments are 
| Input Arguments | Description |
|-----------------|-------------|
|-a ..., --avg-load-threshold ... | Threshold for average load on the VM (%) (default: 10.0) |
|-i ..., --inst-load-threshold ...| Threshold for instantaneous load on the VM (default: 20.0) |

To see a list of input arguments
```
./nhc_multi_node_orphprocs.py --help
```
## Output

Prints 2 output json files, 
VM_loads.json containing the full test results along with the VM names, and
VM_loads_summary.json containing a short summary of the test results.


