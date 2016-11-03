from __future__ import unicode_literals

from django.db import models



class AvailableHosts(models.Model):
    name        = models.TextField(max_length=100, help_text='How do you call this server?')
    host        = models.TextField(max_length=100, help_text='IP address or hostname.')
    ssh_port    = models.IntegerField(help_text='SSH port available to connect to the device.')
    username    = models.TextField(max_length=100, help_text='Username for the SSH connection.')
    password    = models.TextField(max_length=100, help_text='Password to that machine.')
    interface   = models.TextField(max_length=15, help_text='Network adapter to use.')
    creds_valid = models.BooleanField(default=True, help_text='Are the credentials valid.')


class HoneyPots(models.Model):
    name        = models.TextField(max_length=127, help_text='The name of the honeypot.')
    relHost     = models.ForeignKey(AvailableHosts, help_text='Relevant host.')
    ip          = models.TextField(max_length=100, help_text='IP address to take.')
    pid         = models.IntegerField(help_text='PID of the honeyd instance.')
    honey_id    = models.IntegerField(help_text='Configuration ID and log ID.')
    start_time  = models.DateTimeField(auto_now=True, help_text='Date and time the instance was initiated.')
    end_time    = models.DateTimeField(null=True, blank=True, help_text='Date and time the instance was killed.')
    state       = models.BooleanField(default=True, help_text='Is the honeypot active.')
    personality = models.TextField(max_length=255, default='', help_text='The personality of that machine.')


class Services(models.Model):
    relHoneypot = models.ForeignKey(HoneyPots, help_text="Relevant honeypot object.")
    name        = models.TextField(max_length=256, help_text="The script address.")


class Events(models.Model):
    PROTOCOLS = (
        (0, 'TCP'),
        (1, 'UDP'),
        (2, 'ICMP')
    )

    relHoneyPot     = models.ForeignKey(HoneyPots)
    time_stamp      = models.DateTimeField(help_text='Date and time of event.')
    protocol_type   = models.IntegerField(choices=PROTOCOLS, help_text='Protocol.')
    protocol_code   = models.IntegerField(help_text='Code of protocol.')
    src_ip          = models.TextField(max_length=100, help_text='Source IP address.')
    src_port        = models.IntegerField(help_text='Source Port.')
    dst_ip          = models.TextField(max_length=100, help_text='Destination IP address.')
    dst_port        = models.IntegerField(help_text='Destination Port.')
    size            = models.IntegerField(help_text='Size of packet.')
    flags           = models.TextField(max_length=5, help_text='Flags.')
    crunched        = models.BooleanField(default=False, help_text='Was this analyzed.')


class Evaluation(models.Model):

    relHoneyPot     = models.ForeignKey(HoneyPots)
    time_stamp      = models.DateTimeField(help_text='Date and time of event.')
    title           = models.TextField(max_length=128, help_text='Title of event.')
    description     = models.TextField(max_length=1024, help_text='Description of event.')
    source          = models.TextField(max_length=55, help_text='Source of the event.')
