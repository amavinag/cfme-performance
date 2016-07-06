"""Runs Refresh Workload by adding specified providers, and refreshing a specified number of vms,
waiting, then repeating for specified length of time."""
from utils.appliance import clean_appliance
from utils.appliance import get_server_roles_workload_refresh_vms
from utils.appliance import set_server_roles_workload_refresh_vms
from utils.appliance import wait_for_miq_server_ready
from utils.appliance import set_full_refresh_threshold
from utils.grafana import get_scenario_dashboard_url
from utils.log import logger
from utils.providers import add_providers
from utils.providers import get_all_vm_ids
from utils.providers import refresh_provider_vms
from utils.smem_memory_monitor import SmemMemoryMonitor
from utils.ssh import SSHClient
from utils.workloads import get_refresh_vms_scenarios
from itertools import cycle
import time
import pytest

FULL_REFRESH_THRESHOLD_DEFAULT = 100


@pytest.mark.parametrize('scenario', get_refresh_vms_scenarios())
def test_refresh_vms(request, scenario):
    """Refreshes all vm's then waits for a specific amount of time. Memory Monitor creates
    graphs and summary at the end of the scenario."""
    from_ts = int(time.time() * 1000)
    ssh_client = SSHClient()
    logger.debug('Scenario: {}'.format(scenario['name']))

    clean_appliance(ssh_client)

    monitor_thread = SmemMemoryMonitor(SSHClient(), 'workload-refresh-vm', scenario['name'],
        'refresh-vm', get_server_roles_workload_refresh_vms(separator=','),
        ', '.join(scenario['providers']))

    def cleanup_workload(scenario, from_ts):
        starttime = time.time()
        to_ts = int(starttime * 1000)
        g_url = get_scenario_dashboard_url(scenario, from_ts, to_ts)
        logger.debug('Started cleaning up monitoring thread.')
        monitor_thread.grafana_url = g_url
        monitor_thread.signal = False
        monitor_thread.join()
        timediff = time.time() - starttime
        logger.info('Finished cleaning up monitoring thread in {}'.format(timediff))
    request.addfinalizer(lambda: cleanup_workload(scenario, from_ts))

    monitor_thread.start()

    wait_for_miq_server_ready(poll_interval=2)
    set_server_roles_workload_refresh_vms(ssh_client)
    add_providers(scenario['providers'])
    logger.info('Sleeping for refresh: {}s'.format(scenario['refresh_sleep_time']))
    time.sleep(scenario['refresh_sleep_time'])

    full_refresh_threshold_set = False
    if 'full_refresh_threshold' in scenario:
        if scenario['full_refresh_threshold'] != FULL_REFRESH_THRESHOLD_DEFAULT:
            set_full_refresh_threshold(ssh_client, scenario['full_refresh_threshold'])
            full_refresh_threshold_set = True
    if not full_refresh_threshold_set:
        logger.debug('Keeping full_refresh_threshold at default ({}).'.format(
            FULL_REFRESH_THRESHOLD_DEFAULT))

    refresh_size = scenario['refresh_size']
    vm_ids = get_all_vm_ids()
    vm_ids_iter = cycle(vm_ids)
    logger.debug('Number of VM IDs: {}'.format(len(vm_ids)))

    # Variable amount of time for refresh workload
    total_time = scenario['total_time']
    starttime = time.time()
    time_between_refresh = scenario['time_between_refresh']

    while ((time.time() - starttime) < total_time):
        start_refresh_time = time.time()
        refresh_list = [next(vm_ids_iter) for x in range(refresh_size)]
        refresh_provider_vms(refresh_list)
        iteration_time = time.time()

        refresh_time = round(iteration_time - start_refresh_time, 2)
        elapsed_time = iteration_time - starttime
        logger.debug('Time to Queue VM Refreshes: {}'.format(refresh_time))
        logger.info('Time elapsed: {}/{}'.format(round(elapsed_time, 2), total_time))

        if refresh_time < time_between_refresh:
            wait_diff = time_between_refresh - refresh_time
            time_remaining = total_time - elapsed_time
            if (time_remaining > 0 and time_remaining < time_between_refresh):
                time.sleep(time_remaining)
            elif time_remaining > 0:
                time.sleep(wait_diff)
        else:
            logger.warn('Time to Queue Refreshes ({}) exceeded time between Refreshes({})'.format(
                refresh_time, time_between_refresh))
    ssh_client.close()
    logger.info('Test Ending...')
