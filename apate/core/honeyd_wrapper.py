#!/usr/bin/python

import re
import sys
import random
import socket

from apate.core.globals import *
from apate.core.ssh_wrapper import SSHInstance
from apate.core.dynamic_globals import GetGlobalVars
from apate.core.snitch import LogMe, INFORMATION, SUCCESS, WARNING, ERROR


GetGlobalVars(globals())


class HoneyDWrapper():

    def __init__(self, host, port, network_interface, creds, configurations, machines_ip):
        """
        This class is the general wrapper to help dealing with honeyd on
        remote machines using the SSHWrapper
        :param host: IP Address of the host to use.
        :param port: Port to connect to as integer.
        :param network_interface: The network interface to use as string.
        :param creds: A list of the credentials. ['uname', 'password']
        :param configurations: A path to a configuration file.
        :param machines_ip: the IP of the simulated machine.
        :return: None
        """

        # Getting parameters and verifying
        self.__name__ = "HoneyDWrapper"
        self.host_addr = host
        self.host_port = port
        self.interface = network_interface
        self.configuration = configurations
        self.simulate_ip = machines_ip

        if type(creds) == list:
            self.uname, self.passwd = creds
        else:
            LogMe(caller=self.__name__, m_type=ERROR, message="Credentials should be a list or ['username', 'password'].")
            raise

        # Zeroing variables
        self.ssh_instance = None
        self.conf_file = None
        self.conf_id = None

        # Setting things up
        if self._CreateSSHInstance() is ERR:
            raise

    def _ClearPreviousLeftovers(self):
        self.ssh_instance.SendCommand(command="pkill -9 farpd", async=False, sudo=True)
        self.ssh_instance.SendCommand(command="pkill -9 honeyd", async=False, sudo=True)
        LogMe(caller=__name__, m_type=INFORMATION, message="Cleaned previously running honeypots on %s." % self.host_addr)
        return

    def _VerifyAdapter(self):
        """
        Verifies that the adapter requested by the instance exists on that machine.
        """
        adapters_list = self.ssh_instance.GetNetworkAdapters()
        if self.interface in adapters_list:
            return True
        else:
            return False

    def _CreateSSHInstance(self):
        """
        Setup an SSH connection to the host.
        """

        try:
            tempInst = existingSSH[self.host_addr]
            LogMe(caller=__name__, m_type=INFORMATION, message="Obtained previously active SSH Connection.")
            self.ssh_instance = tempInst
            return OKAY

        except KeyError:
            tempInst = SSHInstance(host=self.host_addr, username=self.uname, password=self.passwd, port=self.host_port, debug=True)
            tempInst.InitiateConnection()

            # Add it to the group
            existingSSH[self.host_addr] = tempInst

            # Clean if there are any instances running
            self._ClearPreviousLeftovers()

            if tempInst is not ERR:
                self.ssh_instance = tempInst
                return OKAY

            else:
                return ERR

    def _CreateAndUploadRetriever(self):

        # Get Script
        f = open('apate/foragent/push_logs.py', 'r')
        script = f.read()
        f.close()

        # Get LocalIP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((self.ssh_instance.host,80))
        my_ip = s.getsockname()[0]
        s.close()

        # Patch up the script
        script = script.replace("\"SERVERIP\"", "\"" + my_ip + "\"")
        script = script.replace("\"SERVERPORT\"", str(self.conf_id))

        fname = "%s_%s" % (self.conf_id, RETRIVER_NAME)

        # Upload it but it might exist to ignore it
        self.ssh_instance.PutFile(content=script, remote_directory=HONEYD_LOGS_DIRECTORY, file_name=fname)

        cmnd = "python %s -t %s -p %s & disown" % (HONEYD_LOGS_DIRECTORY+"/"+fname, self.conf_id, self.conf_id)
        a,b,c = self.ssh_instance.connection.exec_command(cmnd)
        cmnd = "python %s -r %s -p %s & disown" % (HONEYD_LOGS_DIRECTORY+"/"+fname, self.conf_id, self.conf_id)
        a,b,c = self.ssh_instance.connection.exec_command(cmnd)
        LogMe(caller=__name__, m_type=SUCCESS, message="Wrote and started retriver to client %s." % self.conf_id)
        return

    def _WriteConfigurationFile(self):
        conf = str(random.randint(10000,20000))
        self.conf_id = int(conf)
        a = self.ssh_instance.PutFile(self.configuration, HONEYD_CONFS_DIRECTORY, conf+"_winnie.conf")
        if a is OKAY:
            self.conf_file = HONEYD_CONFS_DIRECTORY+"/"+conf+"_winnie.conf"
            LogMe(caller=__name__, m_type=SUCCESS, message="Wrote configuration file to client %s." % self.conf_id)
            return OKAY
        return ERR

    def _StartHoneyd(self):

        # Create directories:
        self.ssh_instance.SendCommand(command="mkdir -p %s" % HONEYD_LOGS_DIRECTORY, async=False, sudo=True)

        # Start farpd to catch IP
        self.ssh_instance.SendCommand(command="farpd %s -i %s" % (self.simulate_ip, self.interface), async=False, sudo=True)

        # Start honeyd with the configuration
        cmnd = "honeyd -s %s -l %s -f %s -i %s %s" % (HONEYD_LOGS_DIRECTORY+"/service"+str(self.conf_id)+".log",HONEYD_LOGS_DIRECTORY+"/"+str(self.conf_id)+".log",self.conf_file, self.interface, self.simulate_ip)
        ret = self.ssh_instance.SendCommand(command=cmnd, async=False, sudo=True)

        return OKAY

    def _KillItDead(self):
        self.ssh_instance.KillTask(name="farpd %s" % self.simulate_ip, sudo=True)
        self.ssh_instance.KillTask(name="%s" %self.conf_id+".log", sudo=True)
        self.ssh_instance.Close()

    def _GetLogFile(self):
        f = self.ssh_instance.GetFileContent(HONEYD_LOGS_DIRECTORY+"/"+str(self.conf_id)+".log")
        return f

if __name__ == "__main__":
    sys.stderr.write("Please don't run me as a stand alone.\n")
    sys.exit(ERR)
