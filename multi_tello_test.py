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

def drone_handler(tello, instruc_dict):
    while True:
        independent = True
        incomplete = True
        left = True
        if independent:
            # print('take off')
            
            tello.send_command('takeoff')
            # instruc_dict['synced'] = False
            time.sleep(2)
            tello.send_command('battery?')
            # instruc_dict['synced'] = False
            try:
                battery_level = int(tello.Tello_Manager.response.split(' '))
                print(battery_level)
                instruc_dict['battery'] = battery_level
            except:
                pass
            # time.sleep(2)
            # tello.send_command('up 20')
            # time.sleep(2)
            # while instruc_dict['current_obstacle'] == 'wall':
            #     tello.send_command('forward 100')

            while instruc_dict['current_obstacle'] == 'pillars':
                # tello.send_command('up '+ str(instruc_dict['height']))
                # instruc_dict['synced'] = False
                tello.send_command('EXT tof?')
                try:
                    tof = int(tello.Tello_Manager.response.split(' ')[1])
                except:
                    continue
                if (tof > 700):
                    print('forward')
                    tello.send_command('forward 30')
                else:
                    while tof <= 700:
                        tello.send_command('EXT tof?')
                        try:
                            tof = int(tello.Tello_Manager.response.split(' ')[1])
                        except:
                            continue
                        if tof > 700:
                            break
                        if left: 
                            print('left')
                            tello.send_command('left 30')
                        else:
                            print('right')
                            tello.send_command('right 30')
                        time.sleep(2)
                    left = not left
                time.sleep(2)
                # tello.send_command('forward 20')

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
    height_list = [20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20]
    execution_pools = []
    sn_ip_dict = {}
    id_sn_dict = {}
    ip_fid_dict = {}

    instruc_list_dict = []

    num_of_tello = 10
    LOWBATTERY = 10

    manager.find_avaliable_tello(num_of_tello)
    tello_list = manager.get_tello_list()
    execution_pools = create_execution_pools(num_of_tello)
    
    for x in range(len(tello_list)):
        temp_dict = {'battery': None,\
                    'synced': False,\
                    'height': height_list[x],\
                    'current_obstacle': 'pillars',\
                    'obstacle_complete': False,\
                    }
        instruc_list_dict.append(temp_dict)
        t1 = Thread(target=drone_handler, args=(tello_list[x], instruc_list_dict[x]))
        ip_fid_dict[tello_list[x].tello_ip] = x
        #str_cmd_index_dict_init_flag [x] = None
        t1.daemon = True
        t1.start()

    while True:
        time.sleep(2)

    # while True:
    #     for x in range(len(tello_list)):
    #         if instruc_list_dict[x]['battery'] < LOWBATTERY:
    #             print 'Low Battery --->' % tello_list[x].tello_ip 
    #             raise KeyboardInterrupt

    #     check_done = all_got_response(manager)
    #     if check_done:
    #         for x in range(len(tello_list)):
    #             instruc_list_dict[x]['synced'] = check_done
    #             if instruc_list_dict[x]['current_obstacle']=='wall':
    #                 instruc_list_dict[x]['current_obstacle'] = 'pillars'
        
    #     time.sleep(2)


    while not all_queue_empty(execution_pools):
        time.sleep(1)

    time.sleep(1)

    # wait till all responses are received
    while not all_got_response(manager):
        time.sleep(1)

    save_log(manager)

except KeyboardInterrupt:
    print '[Quit_ALL]Multi_Tello_Task got exception. Sending land to all drones...\n'
    for ip in manager.tello_ip_list:
        manager.socket.sendto('land'.encode('utf-8'), (ip, 8889))

    save_log(manager)
