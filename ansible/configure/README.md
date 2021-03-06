# Configure

Playbooks that configure an appliance for Performance Analysis and Testing. Playbooks are ordered in which they should be run.

**Table of Contents**
========
- [Playbooks](#playbooks)
  - [all-in-one.yml](#all-in-oneyml)
  - [postdeploy.yml](#postdeployyml)
    - [sshkey.yml](#sshkeyyml)
    - [hostname.yml](#hostnameyml)
    - [repos.yml](#reposyml)
    - [time.yml](#timeyml)
    - [config-interface.yml](#config-interfaceyml)
    - [proctitle-patch.yml](#proctitle-patchyml)
    - [init-vmdb.yml](#init-vmdbyml)
    - [collectd.yml](#collectdyml)
  - [database-import.yml](#database-importyml)

# Playbooks

## all-in-one.yml
```
[root@perf ansible]# ansible-playbook -i hosts.local configure/all-in-one.yml
```
Runs all of the roles required to create an All-In-One Performance Monitored CFME/Miq appliance.  See this [document](README.allinone.md) for further details.

## postdeploy.yml
```
[root@perf ansible]# ansible-playbook -i hosts.local configure/postdeploy.yml
```
Runs all of the roles from the below playbooks on cfme-vmdb appliances.

### sshkey.yml
```
[root@perf ansible]# ansible-playbook -i hosts.local configure/sshkey.yml
```
Installs the current user's ssh key into the appliances root user's authorized_key file therefore enabling all other playbooks to run.  After running this playbook you can change the default CFME/Miq appliance password to something secure.

### hostname.yml
```
[root@perf ansible]# ansible-playbook -i hosts.local configure/hostname.yml
```
Sets the appliances hostname to the ansible inventory name.  To produce the intended affect, you should map each inventory file mapping to a host entry in your ~/.ssh/config file.

### repos.yml
```
[root@perf ansible]# ansible-playbook -i hosts.local configure/repos.yml
```
Installs a cfme-performance.repo file into /etc/yum.repos.d directory with necessary repos to install cfme-performance tooling.

### time.yml
```
[root@perf ansible]# ansible-playbook -i hosts.local configure/time.yml
```
Installs and configures chronyd/ntpd service to ensure time is synchronized.

### config-interface.yml
```
[root@perf ansible]# ansible-playbook -i hosts.local configure/config-interface.yml
```
(Optional) Configures static interfaces on CFME/Miq appliances with an address.

### proctitle-patch.yml
```
[root@perf ansible]# ansible-playbook -i hosts.local configure/proctitle-patch.yml
```
(CFME 5.5.x appliances only) Applies patch to CFME 5.5.x appliances to show process title for ruby workers.

### init-vmdb.yml
```
[root@perf ansible]# ansible-playbook -i hosts.local configure/init-vmdb.yml
```
(CFME VMDB appliances only) Installs the dev v2_key and initializes the Postgres database for the region configured in ../group_vars/all.yml (or overriden by all.local.yml) on cfme-vmdb appliances.

### collectd.yml
```
[root@perf ansible]# ansible-playbook -i hosts.local configure/collectd.yml
```
Installs and configures collectd on CFME/Miq appliances.

## database-import.yml
```
[root@perf ansible]# ansible-playbook -i hosts.local configure/database-import.yml
```
Removes current database and imports a database from a database dump file.
