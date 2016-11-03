

# Globals
OKAY                    = "OKAY"
ERR                     = "SHIT"

APPNAME             = "Apate"
APPVERS             = 0.9
AUTHOR              = "Yuval tisf Nativ"


# Honeyd Settings
HONEYD_LOGS_DIRECTORY   = "/var/logs/apate"
HONEYD_CONFS_DIRECTORY  = "/tmp/apate"
RETRIVER_NAME           = "retriver.py"

# REGEXES
TCPUDP_LOG_REGEX        = r'([\d\-\:\.]+)\s(tcp|udp)\((\d+)\)\s\-\s([\d\.]+)\s(\d+)\s([\d\.]+)\s(\d+)\:\s(\d+)\s([A-Z]+)'
ICMP_LOG_REGEX          = r'([\d\-\:\.]+)\s(icmp)\((\d+)\)\s\-\s([\d\.]+)\s([\d\.]+):\s(\d+)'

# Honeyd Scripts:
HONEYD_SCRIPTS = [
                    'embedded/router-telnet.pl',
                    'embedded/snmp/fake-snmp.pl',
                    'linux/smtp.pl',
                    'linux/mysql.py',
                    'linux/cyrus-imapd.sh',
                    'linux/echo.sh',
                    'linux/fingerd.sh',
                    'linux/ftp.sh',
                    'linux/ident.sh',
                    'linux/lpd.sh',
                    'linux/qpop.sh',
                    'linux/sendmail.sh',
                    'linux/squid.sh',
                    'linux/syslogd.sh',
                    'linux/ssh.sh',
                    'linux/telnetd.sh',
                    'unix/general/smtp.sh',
                    'unix/general/telnet/faketelnet.pl',
                    'unix/general/snmp/fake-snmp.pl',
                    'unix/general/pop/pop3.sh',
                    'win32/web.sh',
                    'win32/nbns.py',
                    'win32/mssql.py',
                    'win32/win2k/vnc.sh',
                    'win32/win2k/msftp.sh',
                    'win32/win2k/ldap.sh',
                    'win32/win2k/iis.sh',
                    'win32/win2k/exchange-smtp.sh',
                    'win32/win2k/exchange-pop3.sh',
                    'win32/win2k/exchange-nntp.sh',
                    'win32/win2k/exchange-imap.sh'
]

COMMON_PORTS = [ 23, 25, 22, 139, 445, 443, 110, 465, 137, 80, 993,
                 8080, 7, 20, 115, 156, 1, 3, 5, 8000, 12345, 11,
                 81, 21, 568]
