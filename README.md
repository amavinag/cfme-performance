# cfme-performance
A repo with the goal to provide end-to-end CFME/ManageIQ performance analysis and testing. Browse each folder for more details on how to install, configure, and run each playbook/workload.

## Installing for Testing
```shell
# virtualenv cfme-performance
# cd cfme-performance
# . bin/activate
# git clone https://github.com/akrzos/cfme-performance.git
# cd cfme-performance
# pip install -Ur requirements.txt
```
*Note there are several rpms you may have to install depending on what is already installed in your environment.*


## Major Components
This repo is contains two major components to facilitate its goals:
* [Ansible](#ansible)
* [Cfme-performance](#cfme-performance)


### Ansible
[Ansible Playbooks](ansible/) <br/>
Ansible playbooks used for deploying and managing infrastructure used in the testing framework.


### Cfme-performance
[Python Testing Framework](cfme-performance/) <br/>
Testing framework used to run workloads and benchmarks against CFME. The current workloads are:
* Idle (default, no websocket/git_owner roles, all roles)
* Refresh Providers
* Refresh VMs
* Capacity and Utilization
* SmartState Analysis (Scans VMs)
* Provisioning
