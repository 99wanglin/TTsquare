# -*- coding: utf-8 -*-
import sys
import time
from tello_manager import *
import Queue
import time
import os
import binascii
import logging

log = logging.getLogger('record.log')
reload(sys)
sys.setdefaultencoding('utf-8')

sn_dict = {
    1:"0TQZJ3ACNT0RKT",\
    2:"0TQZJ2TCNT0PZM",\
    3: "0TQZJ2TCNT0Q37",\
    4: "0TQZJ7PCNT10S8",\
    5: "0TQZJ3ACNT0RJB",\
    7:"0TQZJ3ACNT0RL4",\
    8:"0TQZJ3ACNT0RJD",\
    9:"0TQZJ2TCNT0PZR",\
    10: "0TQZJ3ACNT0RKC",\
    11: "0TQZJ3ACNT0Q3K",\
    12: "0TQZJ3ACNT0RT6",\
    13: "0TQZJ7PCNT10PZ",\
    14:"0TQZJ7PCNT10S8",\
    15:"0TQZJ7PCNT10VZ",\
    16:"0TQZJ7PCNT10VM",\
    17:"0TQZJ7WCNT115E",\
    18:"0TQZJ9KCNT13DB",\
    19:"0TQZJ9KCNT131M",\
    18:"0TQZJ9KCNT154N",\
    18:"0TQZJ9KCNT14F7",\
    'u1': "0TQZH9AED00Y13",\
    'u2':"0TQZHB9EUT002A",\
    'u3':"0TQZG9WED00150"\
    }

def send_wait_command(tello, instruc_dict):
    # Tello to wait for the rest to complete action
    # For cases where actions might take more than 15s
    # Send stop command to tell tello to wait longer
    timer = 0
    while instruc_dict['synced'] == False:
        timer += 1
        if timer == 13:
            tello.send_command('stop')
            timer = 0
        time.sleep(1)

def await_sync(instruc_dict):
    # Tello to wait for the rest to complete action
    # for cases where actions should be completed within 15s
    while instruc_dict['synced'] == False:
        time.sleep(0.5)

def drone_handler(tello, instruc_dict):
    INITIATING_SEQUENCE = True
    INITIATE_FAIL = False
    left = True
    while True:
        # print(instruc_dict)
        if INITIATING_SEQUENCE or INITIATE_FAIL:
            INITIATING_SEQUENCE = False
            # Set ip address
            instruc_dict['ip'] = tello.tello_ip

            # Get sn
            try:
                tello.send_command('sn?', instruc_dict)
                time.sleep(1)
                sn = str(tello.Tello_Manager.get_log()[tello.tello_ip][-1].response)
            except:
                INITIATE_FAIL = True
                continue
            # print('sn: ', sn)
            instruc_dict['sn'] = sn

            # Check battery status
            try:
                tello.send_command('battery?', instruc_dict)
                time.sleep(1)
                battery_level = int(tello.Tello_Manager.get_log()[tello.tello_ip][-1].response)
            except:
                INITIATE_FAIL = True
                continue
            # print(battery_level)
            if (battery_level < LOWBATTERY):
                instruc_dict['current_action'] = 'kill'
            await_sync(instruc_dict)

            # Tello take off
            tello.send_command('takeoff', instruc_dict)
            # print('take off')
            time.sleep(1)
            
            # Tello to fly to assigned height
            tello.send_command('up '+ str(instruc_dict['height']), instruc_dict)
            # print('up 20')
            time.sleep(1)
            await_sync(instruc_dict)
            INITIATE_FAIL = False

        # Tello to fly over wall
        # print(instruc_dict)
        if instruc_dict['current_action'] == 'wall' and instruc_dict['obstacle_complete'] == False:
            # tello.send_command('forward 40', instruc_dict)
            print('forward 100 for wall')
            time.sleep(1)
            await_sync(instruc_dict)
            # print(instruc_dict)
           
            
            instruc_dict['obstacle_complete'] = True
            # print(instruc_dict)
            # time.sleep(1)
            
        # print(instruc_dict)
        if instruc_dict['current_action'] == 'pillars':
            # print('loop')
            try:
                tello.send_command('EXT tof?', instruc_dict)
                tof = int(tello.Tello_Manager.get_log()[tello.tello_ip][-1].response.split(' ')[1])
                time.sleep(1)
            except:
                continue
            if (tof > 700):
                # print('forward')
                tello.send_command('forward 20', instruc_dict)
            else: 
                while tof <= 500:
                    if left: 
                        # print('left')
                        tello.send_command('left 20', instruc_dict)
                    else:
                        # print('right')
                        tello.send_command('right 20', instruc_dict)
                    time.sleep(1)
                    await_sync(instruc_dict)
                    try:
                        tello.send_command('EXT tof?', instruc_dict)
                        # print('getting tof')
                        tof = int(tello.Tello_Manager.get_log()[tello.tello_ip][-1].response.split(' ')[1])
                    except:
                        # print('get tof fail')
                        continue
                    time.sleep(2)
                left = not left
            await_sync(instruc_dict)
            time.sleep(2)
        time.sleep(1)

def create_execution_pools(num):
    pools = []
    for x in range(num):
        execution_pool = Queue.Queue()
        pools.append(execution_pool)
    return pools

def all_queue_empty(execution_pools):
    for queue in execution_pools:
        if not queue.empty():
            return False
    return True

def all_got_response(manager):
    for tello_log in manager.get_log().values():
        if not tello_log[-1].got_response():
            return False
    return True

def save_log(manager):
    log = manager.get_log()

    if not os.path.exists('log'):
        try:
            os.makedirs('log')
        except Exception, e:
            pass

    out = open('log/' + start_time + '.txt', 'w')
    cnt = 1
    for stat_list in log.values():
        out.write('------\nDrone:          55555555%s\n' % cnt)
        cnt += 1
        for stat in stat_list:
            #stat.print_stats()
            str = stat.return_stats()
            out.write(str)
        out.write('\n')

# def check_timeout(start_time, end_time, timeout):
#     diff = end_time - start_time
#     time.sleep(0.1)
#     return diff > timeout

manager = Tello_Manager()
start_time = str(time.strftime("%a-%d-%b-%Y_%H-%M-%S-%Z", time.localtime(time.time())))

try:
    # file_name = sys.argv[1]
    # f = open(file_name, "r")
    # commands = f.readlines()

    tello_list = []
    # height_list = [10, 20, 30, 40, 30, 20, 10, 20, 30, 40, 30, 20]
    height_list = [40, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20]
    # execution_pools = []
    # sn_ip_dict = {}
    id_sn_dict = {}
    ip_fid_dict = {}

    instruc_list_dict = []

    num_of_tello = 2
    LOWBATTERY = 10

    manager.find_avaliable_tello(num_of_tello)
    tello_list = manager.get_tello_list()
    # execution_pools = create_execution_pools(num_of_tello)
    actions = ['get_sn',\
            'battery_check',\
            'takeoff',\
            'rise to height',\
            'wall',\
            'pillars'
            ]
    action_index = 0
    for x in range(len(tello_list)):
        temp_dict = {'ip': None,\
                    'sn': None,\
                    'synced': False,\
                    'height': 20,\
                    'current_action': actions[action_index],\
                    'obstacle_complete': False,\
                    }
        instruc_list_dict.append(temp_dict)
        t1 = Thread(target=drone_handler, args=(tello_list[x], instruc_list_dict[x]))
        ip_fid_dict[tello_list[x].tello_ip] = x
        #str_cmd_index_dict_init_flag [x] = None
        t1.daemon = True
        t1.start()

    course_completed = False
    all_complete = False
    while not course_completed:
        # print(instruc_list_dict)
        # print('counter')
        for x in range(len(tello_list)):
            if instruc_list_dict[x]['current_action'] == 'kill':
                raise KeyboardInterrupt
        if not all_got_response(manager):
            # print('waiting')
            time.sleep(0.5)
            continue
        else:
            # print('all_completed: ', all_complete)
            # print('action_index: ', action_index)
            if action_index > 4:
                for x in range(len(tello_list)):
                    if instruc_list_dict[x]['obstacle_complete'] == False:
                        all_complete = False
                        break
                    else:
                        all_complete = True
                # print('all_complete: ', all_complete)
                for x in range(len(tello_list)):
                    # print('sync done')
                    instruc_list_dict[x]['synced'] = True
                if not all_complete:
                    # time.sleep(2)
                    # print('reloop')
                    continue
            for x in range(len(tello_list)):
                # print('sync done')
                instruc_list_dict[x]['synced'] = True
            time.sleep(2)
            action_index += 1
            for x in range(len(tello_list)):
                action = actions[action_index]
                # print(action)
                instruc_list_dict[x]['synced'] = False
                instruc_list_dict[x]['obstacle_complete'] = False
                instruc_list_dict[x]['current_action'] = action
            time.sleep(2)

    # wait till all responses are received
    while not all_got_response(manager):
        time.sleep(1)

    save_log(manager)

except KeyboardInterrupt:
    print '[Quit_ALL]Multi_Tello_Task got exception. Sending land to all drones...\n'
    for ip in manager.tello_ip_list:
        manager.socket.sendto('land'.encode('utf-8'), (ip, 8889))

    save_log(manager)
