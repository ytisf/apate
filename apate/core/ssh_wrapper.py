#!/usr/bin/python

import re
import sys
import paramiko

from pexpect import pxssh

from apate.core.globals import *
from apate.core.snitch import LogMe, INFORMATION, SUCCESS, WARNING, ERROR


class SSHInstance():
    """
    This code was written in Jan 2016 as a part of an open source project and
    is only to be used with GPLv3 License used by tisf.
    """

    def __init__(self, host, username, password, port=22, debug=False):
        self.__name__ = "SSHInstance: %s" % host

        # Configurations
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.Debug = debug

        # Live Vars
        self.connection = None
        self.async_cmds = {}
        self.top = {}
        self.adapters = []

    def InitiateConnection(self):
        """
        Starts a connection to the host specified.
        :return: OKAY or ERR
        """

        self.connection = paramiko.SSHClient()
        self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        LogMe(caller=self.__name__, m_type=INFORMATION,
              message="Attempting to connect to '%s'..." % self.host)
        try:
            self.connection.connect(hostname=self.host, port=self.port, username=self.username, password=self.password)
            LogMe(caller=self.__name__, m_type=SUCCESS,
                  message="Connection to %s is established." % self.host)
            return OKAY

        except:
            LogMe(caller=self.__name__, m_type=ERROR,
                  message="Unable to login to %s." % self.host)
            self.connection = None
            return ERR

    def SendCommand(self, command=None, async=False, sudo=False):
        """
        Sends a command to the active connection.
        :param command: Command to execute.
        :param async: Boolean as to be async or not.
        :return: OKAY or ERR
        """
        if command is None:
            LogMe(caller=self.__name__, m_type=ERROR,
                  message="You must provide a command.")
            return ERR

        if self.connection is None:
            LogMe(caller=self.__name__, m_type=ERROR,
                  message="No active connection so cannot send a command.")
            return ERR

        if async:
            # Is Async Command
            if sudo:
                cmnd_line = "sudo screen -d -m &" + command
            else:
                cmnd_line = "screen -d -m &" + command

            if self.Debug:
                LogMe(caller=self.__name__, m_type=INFORMATION,
                      message="Sending the command '%s'." % cmnd_line)

            stdin, stdout, stderr = self.connection.exec_command(cmnd_line)
            stdin, stdout, stderr = self.connection.exec_command("echo $!")
            this_pid = stdout.read().replace(cmnd_line + "\r\n[1] ", "")
            this_pid = this_pid.replace("echo $!", "")

            try:
                this_pid = int(this_pid)
                self.async_cmds[this_pid] = [True, command]
                return this_pid
            except ValueError:
                pass
            return OKAY

        else:
            # Not async
            if sudo:
                cmnd_line = "sudo " + command
            else:
                cmnd_line = command

            if self.Debug:
                LogMe(caller=self.__name__, m_type=INFORMATION, message="Sending the command '%s'." % cmnd_line)

            stdin, stdout, stderr = self.connection.exec_command(cmnd_line)

            # Removing the command (which is appended as prefix) and the \r\n.
            ret_data = stdout.read().replace(command, "")[2:]
            return ret_data


    def KillTask(self, pid=None, name=None, sudo=False):
        """
        Kill an active task by PID
        :param id: The PID of the task to kill.
        :return: OKAY or ERR
        """
        if pid is None and name is None:
            sys.stderr.write("I need a PID or name to kill.\n")
            return ERR

        # Kill by name
        elif pid is None and name is not None:
            if sudo is False:
                a,b,c  = self.connection.exec_command("pkill %s" % name)
            else:
                a,b,c  = self.connection.exec_command("sudo pkill %s" % name)

        # Kill by PID
        elif pid is None and name is not None:
            if sudo is False:
                a,b,c  = self.connection.exec_command("kill %s" % pid)
            else:
                a,b,c  = self.connection.exec_command("sudo kill %s" % pid)

        a,answer,c  = self.connection.exec_command
        if answer.read().strip() is "" or "Stopped" in answer.read() or str(pid) in answer.read():
            try:
                self.async_cmds[pid].remove()
            except KeyError:
                pass
            except TypeError:
                pass
            return OKAY

        else:
            return ERR

    def Close(self):
        """
        Closes the connection and kill all active tasks.
        :return: Nothing
        """

        # Todo: Fix this
        # Killing all active tasks
        # if len(self.async_cmds) is not 0:
        #     for pid, state, command in self.async_cmds.iteritems():
        #         self.KillTask(id=pid)

        # Closing the connection
        if self.connection is not None:
            self.connection.close()
            LogMe(caller=self.__name__, m_type=INFORMATION,
                  message="Connection has been closed to host '%s'." % self.host)
            return OKAY
        else:
            LogMe(caller=self.__name__, m_type=INFORMATION,
                  message="There is no active connection to '%s'." % self.host)
            return ERR

    def GetServiceStatus(self, service_name):
        """
        This will report the status of a service.
        :param service_name: str, name of service as in /etc/init.d.
        :return: True, False, ERR
        """

        cmnd_strng = "/etc/init.d/%s status" % service_name
        status = self.SendCommand(command=cmnd_strng, async=False)

        if status is ERR:
            return ERR

        elif "No such file or directory" in status:
            sys.stderr.write(
                "Could not find service name '%s' on the machine.\n" % service_name)
            return ERR

        elif "cannot read PID file" in status:
            sys.stderr.write("You have no permissions to read PID file.\n")
            return ERR

        elif "is running" in status:
            return True

        elif "is not running" in status:
            return False

        else:
            sys.stderr.write(
                "Got an error i'm not familiar with when setting status of '%s'.\n" % service_name)
            return ERR

    def StartService(self, service_name):
        """
        This will attempt to start a service.
        :param service_name: str, name of service as in /etc/init.d.
        :return: OKAY, ERR
        """

        cmnd_strng = "/etc/init.d/%s start" % service_name
        status = self.SendCommand(command=cmnd_strng, async=False)

        if status is ERR:
            return ERR

        elif "[ OK ]" in status:
            return OKAY

        else:
            return ERR

    def StopService(self, service_name):
        """
        This will attempt to stop a service.
        :param service_name: str, name of service as in /etc/init.d.
        :return: OKAY, ERR
        """

        cmnd_strng = "/etc/init.d/%s stop" % service_name
        status = self.SendCommand(command=cmnd_strng, async=False)

        if status is ERR:
            return ERR

        elif "[ OK ]" in status:
            return OKAY

        else:
            return ERR

    def GetFileContent(self, full_path):
        """
        This will attempt to get file's content
        :param full_path: str, full path to file.
        :return: content of file or ERR
        """

        cmnd_strng = "cat %s" % full_path

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.host, username=self.username, password=self.password)
        stdin, stdout, stderr = ssh.exec_command(cmnd_strng)

        out = stdout.readlines()
        err = stdout.readlines()

        ssh.close()

        if len(out) is 0:
            return OKAY
        elif len(err) is not 0:
            return ERR
        elif "Permission denied" in err:
            sys.stderr.write(
                COLORS.WARNING + "You have no permissions to read '%s'.%s" % (full_path, COLORS.ENDC))
            return ERR
        elif "No such file or directory" in err:
            sys.stderr.write("Could not find file '%s'.\n" % full_path)
            return ERR

        return out

    def GetTaskList(self):
        cmnd_strng = "ps -aux"
        status = self.SendCommand(command=cmnd_strng, async=False)
        if status is ERR:
            return ERR

        # User, PID, %CPU, %MEM, VSZ, RSS, TTY, STAT, START, TIME, COMMAND
        ps_line_regex = r'([a-zA-Z0-9\-\_\+]+)\s+(\d+)\s+(\d{1,3}\.\d{1,2})\s+(\d{1,3}\.\d{1,2})\s+(\d+)\s+(\d+)\s+([a-z\\/0-9\?]+)\s+([Ss\+RrlN<]+)\s+([a-zA-Z0-9\:]+)\s+(\d{1,3}:\d{1,3})\s+(.+)'
        ps_regex = re.compile(ps_line_regex)

        # Reset current TOP
        self.top = {}

        for line in status.split("\n"):
            if ps_regex.match(line):
                proc = re.search(ps_regex, line)

                self.top[proc.group(2)] = {"user": proc.group(1),
                                           "pid": proc.group(2),
                                           "cpu": proc.group(3),
                                           "mem": proc.group(4),
                                           "vsz": proc.group(5),
                                           "rss": proc.group(6),
                                           "tty": proc.group(7),
                                           "stat": proc.group(8),
                                           "start": proc.group(9),
                                           "time": proc.group(10),
                                           "command": proc.group(11)
                                           }
            else:
                pass

        return OKAY

    def GetNetworkAdapters(self):
        cmnd_strng = "ls /sys/class/net/ --color=never"
        status = self.SendCommand(command=cmnd_strng, async=False)
        if status is ERR:
            return ERR

        else:
            adapters = status.replace("\r\n", "").split("  ")
            self.adapters = adapters
            return OKAY

    def PutFile(self, content, remote_directory, file_name):
        """
        Copy a local file to the remote server.
        :param content: data to write.
        :param remote_directory: Directory on remote machine to put the files at.
        :param file_name: name of file to give.
        :return: OKAY or ERR
        """

        # Open SFTP connection to the server
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.host, username=self.username, password=self.password)
            sftp = ssh.open_sftp()
        except:
            LogMe(caller=self.__name__, m_type=ERROR, message="Could connect to '%s'." % self.host)
            return ERR

        # Make sure directory is there
        try:
            sftp.mkdir(remote_directory)
        except IOError:
            pass

        # Write File Content
        try:
            f = sftp.open(remote_directory + '/' + file_name, 'w')
            f.write(content)
            f.close()
            ssh.close()
            return OKAY
        except IOError, e:
            LogMe(caller=__name__, m_type=ERROR, message="Could not upload file '%s'. Reason: %s." % (remote_directory+'/'+file_name,e))
            ssh.close()
            return ERR


if __name__ == "__main__":
    sys.stderr.write(
        "Please don't run this a stand alone as it is a module.\n")
    sys.exit(ERR)
