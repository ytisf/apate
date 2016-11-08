#!/usr/bin/python

import os
import re
import sys
import pytz
import random

from datetime import datetime

from apate.views import *
from apate.models import *
from apate.core.globals import *
from apate.core.dynamic_globals import GetGlobalVars
from apate.core.snitch import LogMe, INFORMATION, SUCCESS, WARNING, ERROR


GetGlobalVars(globals())


def _get_os_list():
    ret = []
    try:
        f = open('apate/dat/oss.lst', 'r')
        lst = f.readlines()
        f.close()
    except IOError,e:
        LogMe(caller="_get_os_list", m_type=WARNING, message='Could not open OSs file due to: %s' % e)
        return False

    for ln in lst:
        ret.append(ln.strip())

    return sorted(list(set(ret)))


def _build_honeyd_configuration_file(machine_name, personality, ip, ping_response=True, services=[]):

    conf = ""
    conf += "# %s - %s\n" % (machine_name, personality)
    conf += "create %s\n" % machine_name
    conf += "set %s personality \"%s\"\n" % (machine_name, personality)
    conf += "set %s default tcp action reset\n" % machine_name
    conf += "set %s default udp action block\n" % machine_name
    if ping_response:
        conf += "set %s default icmp action open\n" % machine_name
    else:
        conf += "set %s default icmp action closed\n" % machine_name
    conf += "set %s uptime %s\n" % (machine_name, random.randint(20000,99999))

    for service in services:

        protocol = "tcp"
        port = 0

        if "ftp" in service:
            port = 21
        elif "iis" in service or "web" in service:
            port = 80
        elif "pop" in service:
            port = 110
        elif "imap" in service:
            port = 143
        elif ("smtp" or "sendmail") in service:
            port = 25
        elif "telnet" in service:
            port = 23
        elif "ssh" in service:
            port = 22
        elif "mysql" in service:
            port = 3306
        elif "snmp" in service:
            protocol = "udp"
            port = 161
        elif "vnc" in service:
            port = 5900
        elif "echo" in service:
            port = 7
        elif "finger" in service:
            port = 79
        elif "mssql" in service:
            port = 1433
        elif "ident" in services:
            port = 113
        elif "lpd" in services:
            port = 515
        elif "squid" in services:
            port = 8000
        elif "nntp" in services:
            port = 119
        elif "ldap" in services:
            port = 389
        elif "nbns" in services:
            port = 137
            protocol = "udp"
        elif "syslogd" in service:
            port = 514
        else:
            port = random.randint(1000, 4000)

        conf += "add %s %s port %s \"sh /usr/share/honeyd/scripts/%s $ipsrc $sport $ipdst $dport\"\n" % (machine_name, protocol, port, service)

    conf += "bind %s %s\n" % (ip, machine_name)

    return conf


def _analyzeLogFile(logdata, conf_id):

    try:
        relHon = HoneyPots.objects.get(honey_id=conf_id)
    except:
        return ERR

    tu = re.findall(pattern=TCPUDP_LOG_REGEX, string=logdata)
    ic = re.findall(pattern=ICMP_LOG_REGEX, string=logdata)

    for row in tu:
        dateobj = datetime.strptime(row[0], '%Y-%m-%d-%H:%M:%S.%f')
        pytz.timezone("Asia/Bangkok").localize(dateobj)
        prot = row[1]
        code = row[2]
        src_ip = row[3]
        sport = row[4]
        dst_ip = row[5]
        dport = row[6]
        size = row[7]
        flags = row[8]

        if prot is "tcp":
            prot = 0
        elif prot is "udp":
            prot = 1
        else:
            prot = 0

        try:
            # Object exists. Dont need to update it.
            temp = Events.objects.get(time_stamp=dateobj, src_ip=src_ip, dst_ip=dst_ip, protocol_type=prot)
            continue
        except:
            newEvent = Events(
                    relHoneyPot=relHon,
                    time_stamp=dateobj,
                    protocol_type=prot,
                    protocol_code=int(code),
                    src_ip=src_ip,
                    src_port=int(sport),
                    dst_ip=dst_ip,
                    dst_port=int(dport),
                    size=int(size),
                    flags=flags
            )
            newEvent.save()

    for row in ic:
        prot = 2
        dateobj = datetime.strptime(row[0], '%Y-%m-%d-%H:%M:%S.%f')
        pytz.timezone("Asia/Bangkok").localize(dateobj)
        src_ip = row[3]
        dst_ip = row[4]
        code = row[5]
        try:
            # Object exists. Dont need to update it.
            temp = Events.objects.get(time_stamp=dateobj, src_ip=src_ip, dst_ip=dst_ip, protocol_type=prot)
            continue
        except:
            newEvent = Events(
                    relHoneyPot=relHon,
                    time_stamp=dateobj,
                    protocol_type=prot,
                    protocol_code=int(code),
                    src_ip=src_ip,
                    src_port=0,
                    dst_ip=dst_ip,
                    dst_port=0,
                    size=0,
                    flags="None"
            )
            newEvent.save()

    _analyzeEventLog()
    return OKAY


def _analyzeEventLog():

    # Get all active honeypots
    activeHoneypots = HoneyPots.objects.filter(state=True)
    if len(activeHoneypots) is 0:
        return True

    # Do the logic for each honeypot seperatly
    for hp in activeHoneypots:

        events = Events.objects.filter(relHoneyPot=hp)
        if len(events) is 0:
            continue


        port_scan = {}

        for ev in events:

            if ev.crunched is True:
                continue

            if ev.protocol_type is 2:
                newEval = Evaluation(
                        relHoneyPot = hp,
                        time_stamp = ev.time_stamp,
                        title="Ping attempt",
                        description="A host has attempted to ping this host.",
                        source=ev.src_ip
                )
                newEval.save()
                notifications.append("Detected a ping sweep from '%s' on '%s'." % (ev.src_ip, hp.ip))
                LogMe(caller=__name__, m_type=WARNING, message="Ping Sweep detected from '%s' by '%s'!" % (hp.ip, ev.src_ip))

            else:
                if ev.dst_port in COMMON_PORTS:
                    try:
                        port_scan[ev.src_ip][0] += 1
                    except KeyError:
                        port_scan[ev.src_ip] = [1, ev.time_stamp]

            ev.crunched = True
            ev.save()


        if len(port_scan) is 0:
            return True

        for host, details in port_scan.iteritems():
            if details[0] > 5:
                newEval = Evaluation(
                        relHoneyPot = hp,
                        time_stamp = details[1],
                        title="Port Scanning",
                        description="Detected a Port Scan attempts from %s." % host,
                        source=host
                )
                newEval.save()
                notifications.append("Detected a Port Scan attempts from %s on %s." % (host, hp.ip))
                LogMe(caller=__name__, m_type=WARNING, message="Port scanning detected on '%s' by '%s'!" % (hp.ip, host))

        return True
