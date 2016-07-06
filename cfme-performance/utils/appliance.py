"""Appliance specific settings and functions."""
from utils.conf import cfme_performance
from utils.log import logger
from utils.ssh import SSHTail
from textwrap import dedent
import time
import yaml

yaml_loader = dedent("""\
new_conf = YAML::load(File.open('/tmp/vmdb.yml'))
new_conf_symbol = new_conf.deep_symbolize_keys.to_yaml
result = VMDB::Config.save_file(new_conf_symbol)
if result != true
  exit 255
end""")

roles56_default = ['automate', 'database_operations', 'ems_inventory', 'ems_operations', 'event',
    'reporting', 'scheduler', 'smartstate', 'user_interface', 'web_services', 'websocket']

roles56_idle = ['automate', 'database_operations', 'database_synchronization', 'ems_inventory',
    'ems_metrics_collector', 'ems_metrics_coordinator', 'ems_metrics_processor', 'ems_operations',
    'event', 'notifier', 'reporting', 'rhn_mirror', 'scheduler', 'smartproxy', 'smartstate',
    'user_interface', 'web_services']

roles56_all = ['automate', 'database_operations', 'database_synchronization', 'ems_inventory',
    'ems_metrics_collector', 'ems_metrics_coordinator', 'ems_metrics_processor', 'ems_operations',
    'event', 'git_owner', 'notifier', 'reporting', 'rhn_mirror', 'scheduler', 'smartproxy',
    'smartstate', 'user_interface', 'web_services', 'websocket']

roles56_cap_and_util = ['automate', 'database_operations', 'ems_inventory', 'ems_metrics_collector',
    'ems_metrics_coordinator', 'ems_metrics_processor', 'ems_operations', 'event', 'notifier',
    'reporting', 'scheduler', 'user_interface', 'web_services']

roles56_refresh_providers = ['automate', 'database_operations', 'ems_inventory', 'ems_operations',
    'event', 'reporting', 'scheduler', 'smartstate', 'user_interface', 'web_services', 'websocket']

roles56_refresh_vms = ['automate', 'database_operations', 'ems_inventory', 'ems_operations',
    'event', 'reporting', 'scheduler', 'smartstate', 'user_interface', 'web_services', 'websocket']

roles56_smartstate = ['automate', 'database_operations', 'ems_inventory', 'ems_operations', 'event',
    'notifier', 'reporting', 'scheduler', 'smartproxy', 'smartstate', 'user_interface',
    'web_services']

roles56_provisioning = ['automate', 'database_operations', 'ems_inventory', 'ems_operations',
    'event', 'notifier', 'reporting', 'scheduler', 'user_interface', 'web_services']

roles56_workload_all = ['automate', 'database_operations', 'ems_inventory', 'ems_metrics_collector',
    'ems_metrics_coordinator', 'ems_metrics_processor', 'ems_operations', 'event', 'notifier',
    'reporting', 'rhn_mirror', 'scheduler', 'smartproxy', 'smartstate', 'user_interface',
    'web_services']


def clean_appliance(ssh_client):
    starttime = time.time()
    ssh_client.run_command('service evmserverd stop')
    ssh_client.run_command('sync; sync; echo 3 > /proc/sys/vm/drop_caches')
    ssh_client.run_command('service collectd stop')
    ssh_client.run_command('service rh-postgresql94-postgresql restart')
    ssh_client.run_rake_command('evm:dbsync:local_uninstall')
    # 5.6 requires DISABLE_DATABASE_ENVIRONMENT_CHECK=1
    ssh_client.run_command(
        'cd /var/www/miq/vmdb;DISABLE_DATABASE_ENVIRONMENT_CHECK=1 bin/rake evm:db:reset')
    ssh_client.run_rake_command('db:seed')
    ssh_client.run_command('service collectd start')
    # Work around for https://bugzilla.redhat.com/show_bug.cgi?id=1337525
    ssh_client.run_command('service httpd stop')
    ssh_client.run_command('rm -rf /run/httpd/*')
    ssh_client.run_command('service evmserverd start')
    logger.debug('Cleaned appliance in: {}'.format(time.time() - starttime))
    ssh_client.close()


def get_vmdb_yaml_config(ssh_client):
    base_data = ssh_client.run_rails_command('puts\(Settings.to_hash.deep_stringify_keys.to_yaml\)')
    if base_data.rc:
        logger.error("Config couldn't be found")
        logger.error(base_data.output)
        raise Exception('Error obtaining vmdb config')
    yaml_data = base_data.output[:base_data.output.find('DEPRE')]
    ssh_client.close()
    return yaml.load(yaml_data)


def set_vmdb_yaml_config(ssh_client, yaml_data):
    logger.info('Uploading VMDB yaml Loader')
    ssh_client.run_command('echo "{}" > /tmp/yaml_loader.rb'.format(yaml_loader), log_less=True)
    logger.info('Uploading VMDB Config')
    ssh_client.run_command('echo "{}" > /tmp/vmdb.yml'.format(
        yaml.dump(yaml_data, default_flow_style=False)), log_less=True)
    result = ssh_client.run_rails_command('/tmp/yaml_loader.rb')
    ssh_client.close()
    if result.rc:
        raise Exception('Unable to set config')
    else:
        logger.info('Set VMDB Config')


def set_full_refresh_threshold(ssh_client, threshold=100):
    yaml = get_vmdb_yaml_config(ssh_client)
    yaml['ems_refresh']['full_refresh_threshold'] = threshold
    set_vmdb_yaml_config(ssh_client, yaml)
    ssh_client.close()


def install_vddk(ssh_client, vddk_version='vddk6_0'):
    """Install the vddk on a appliance"""
    logger.debug('Installing the VDDK RPM')
    if ssh_client.run_command('test -d /usr/lib/vmware-vix-disklib/lib64')[0] == 0:
        logger.info('VDDK is installed already.')
    else:
        vddk_url = cfme_performance['resources'][vddk_version]
        file_name = vddk_url.split('/')[-1]
        if ssh_client.run_command('test -e /root/{}'.format(file_name))[0] == 0:
            logger.info('VDDK already downloaded')
        else:
            ssh_client.run_command('wget {}'.format(vddk_url))
        rc, output = ssh_client.run_command('yum -y install {}'.format(file_name))
        if rc != 0:
            logger.error('VDDK Install Failure: {}'.format(output))
        rc, output = ssh_client.run_command('ldconfig -p | grep vix')
        if len(output) < 2:
            logger.error('VDDK Install Failure libraries detected ({})'.format(output))
    logger.debug('VDDK Install finished')
    ssh_client.close()


def get_server_roles_workload_idle_default(separator=','):
    return separator.join(roles56_default)


def get_server_roles_workload_idle(separator=','):
    return separator.join(roles56_idle)


def get_server_roles_workload_idle_all(separator=','):
    return separator.join(roles56_all)


def get_server_roles_workload_cap_and_util(separator=','):
    return separator.join(roles56_cap_and_util)


def get_server_roles_workload_refresh_providers(separator=','):
    return separator.join(roles56_refresh_providers)


def get_server_roles_workload_refresh_vms(separator=','):
    return separator.join(roles56_refresh_vms)


def get_server_roles_workload_smartstate(separator=','):
    return separator.join(roles56_smartstate)


def get_server_roles_workload_provisioning(separator=','):
    return separator.join(roles56_provisioning)


def get_server_roles_workload_all(separator=','):
    return separator.join(roles56_workload_all)


def set_server_roles_workload_idle(ssh_client):
    """Turns on all server roles except for git owner and websocket used for idle workload."""
    yaml = get_vmdb_yaml_config(ssh_client)
    yaml['server']['role'] = get_server_roles_workload_idle()
    set_vmdb_yaml_config(ssh_client, yaml)
    ssh_client.close()


def set_server_roles_workload_idle_all(ssh_client):
    """Turns on all server roles used for idle all workload."""
    yaml = get_vmdb_yaml_config(ssh_client)
    yaml['server']['role'] = get_server_roles_workload_idle_all()
    set_vmdb_yaml_config(ssh_client, yaml)
    ssh_client.close()


def set_server_roles_workload_cap_and_util(ssh_client):
    """Sets server roles used for all C&U workloads."""
    yaml = get_vmdb_yaml_config(ssh_client)
    yaml['server']['role'] = get_server_roles_workload_cap_and_util()
    set_vmdb_yaml_config(ssh_client, yaml)
    ssh_client.close()


def set_server_roles_workload_refresh_providers(ssh_client):
    """Sets server roles used for all refresh_providers workloads."""
    yaml = get_vmdb_yaml_config(ssh_client)
    yaml['server']['role'] = get_server_roles_workload_refresh_providers()
    set_vmdb_yaml_config(ssh_client, yaml)


def set_server_roles_workload_refresh_vms(ssh_client):
    """Sets server roles used for all refresh_vms workloads"""
    yaml = get_vmdb_yaml_config(ssh_client)
    yaml['server']['role'] = get_server_roles_workload_refresh_vms()
    set_vmdb_yaml_config(ssh_client, yaml)


def set_server_roles_workload_smartstate(ssh_client):
    """Sets server roles for Smartstate workload."""
    yaml = get_vmdb_yaml_config(ssh_client)
    yaml['server']['role'] = get_server_roles_workload_smartstate()
    set_vmdb_yaml_config(ssh_client, yaml)


def set_server_roles_workload_provisioning(ssh_client):
    """Sets server roles for Provisioning workload."""
    yaml = get_vmdb_yaml_config(ssh_client)
    yaml['server']['role'] = get_server_roles_workload_provisioning()
    set_vmdb_yaml_config(ssh_client, yaml)


def set_server_roles_workload_all(ssh_client):
    """Turns on all server roles used for all workload memory measurement benchmark. Does not turn
    on datbase_synchronization role."""
    yaml = get_vmdb_yaml_config(ssh_client)
    yaml['server']['role'] = get_server_roles_workload_all()
    set_vmdb_yaml_config(ssh_client, yaml)


def set_cap_and_util_all_via_rails(ssh_client):
    """Turns on Collect for All Clusters and Collect for all Datastores without using the Web UI."""
    command = ('Metric::Targets.perf_capture_always = {:storage=>true, :host_and_cluster=>true};')
    ssh_client.run_rails_console(command, timeout=None, log_less=True)
    ssh_client.close()


def set_cfme_server_relationship(ssh_client, vm_name, server_id=1):
    """Set MiqServer record to the id of a VM by name, effectively setting the CFME Server
    Relationship without using the Web UI."""
    command = ('miq_server = MiqServer.find_by(id: {});'
               'miq_server.vm_id = Vm.find_by(name: \'{}\').id;'
               'miq_server.save'.format(server_id, vm_name))
    ssh_client.run_rails_console(command, timeout=None, log_less=False)
    ssh_client.close()


def set_pglogical_replication(ssh_client, replication_type=':none'):
    """Set pglogical replication type (:none, :remote, :global) without using the Web UI."""
    command = ('MiqRegion.replication_type = {}'.format(replication_type))
    ssh_client.run_rails_console(command, timeout=None, log_less=False)
    ssh_client.close()


def set_rubyrep_replication(ssh_client, host, database='vmdb_production', username='root',
        password='v2:{I2SQ5PdmGPwN7t5goRiyaQ==}', port='5432'):
    """Sets up rubyrep replication via advanced configuration settings yaml."""
    yaml = get_vmdb_yaml_config(ssh_client)
    dest = yaml['workers']['worker_base']['replication_worker']['replication']['destination']
    dest['database'] = database
    dest['username'] = username
    dest['password'] = password
    dest['port'] = port
    dest['host'] = host
    set_vmdb_yaml_config(ssh_client, yaml)
    ssh_client.close()


def wait_for_miq_server_ready(poll_interval=5):
    """Waits for the CFME to be ready by tailing evm.log for:
    'INFO -- : MIQ(MiqServer#start) Server starting complete'
    Verified works with 5.6 appliances.
    """
    logger.info('Opening /var/www/miq/vmdb/log/evm.log for tail')
    evm_tail = SSHTail('/var/www/miq/vmdb/log/evm.log')
    evm_tail.set_initial_file_end()

    attempts = 0
    detected = False
    max_attempts = 60
    while (not detected and attempts < max_attempts):
        logger.debug('Attempting to detect MIQ Server ready: {}'.format(attempts))
        for line in evm_tail:
            if 'MiqServer#start' in line:
                if 'Server starting complete' in line:
                    logger.info('Detected MIQ Server is ready.')
                    detected = True
                    break
        time.sleep(poll_interval)  # Allow more log lines to accumulate
        attempts += 1
    if not (attempts < max_attempts):
        logger.error('Could not detect MIQ Server ready in 600s.')
    evm_tail.close()
