from django.core import serializers
from django.shortcuts import render, redirect

from threading import Thread

from apate.models import *
from apate.core.globals import *
from apate.core.retrival_agent import GoldenRetriver
from apate.core.honeyd_wrapper import HoneyDWrapper
from apate.core.dynamic_globals import GetGlobalVars
from apate.core.snitch import LogMe, INFORMATION, SUCCESS, WARNING, ERROR
from apate.core.aux import _get_os_list, _build_honeyd_configuration_file, _analyzeLogFile
# Create your views here.


GetGlobalVars(globals())



def __init():
    """
    This is a preparation for a function that will run once the program starts.
    """
    LogMe(caller=__name__, m_type=INFORMATION, message="Completed initiating %s." % APPNAME)
    return True

def Dashboard(request):
    a = {}
    a['page'] = "Dashboard"
    a['title'] = "%s | Dashboard" % APPNAME

    a['devices'] = AvailableHosts.objects.all()
    a['honeypots'] = HoneyPots.objects.all()
    a['events'] = Events.objects.all()

    a['tcp_count'] = len(Events.objects.filter(protocol_type=0))
    a['udp_count'] = len(Events.objects.filter(protocol_type=1))
    a['icmp_count'] = len(Events.objects.filter(protocol_type=2))

    total = a['tcp_count'] + a['udp_count'] + a['icmp_count']

    if a['tcp_count'] is 0:
        a['rel_tcp'] = 0
    else:
        a['rel_tcp'] = a['tcp_count']/total

    if a['udp_count'] is 0:
        a['rel_udp'] = 0
    else:
        a['rel_udp'] = a['udp_count']/total

    if a['icmp_count'] is 0:
        a['rel_icmp'] = 0
    else:
        a['rel_icmp'] = a['icmp_count']/total

    return render(request, "Dashboard.html", a)

### Completed Functions

def AddNewServer(request):
    a = {}
    a['page'] = "AddNewServer"
    a['title'] = "Add A New Server"

    # info_message

    if request.method == "POST":
        try:
            name = request.POST.get('name')
            ip = request.POST.get('hostname')
            username = request.POST.get('username')
            password = request.POST.get('password')
            port = request.POST.get('port')
            interface = request.POST.get('interface')
        except KeyError, e:
            a['info_message'] = "The field %s is not okay." % e
            return render(request, "AddNewServer.html", a)

        j = AvailableHosts.objects.filter(host=ip)

        if len(j) is not 0:
            a['info_message'] = "Such host already exists in the system."
            return render(request, "AddNewServer.html", a)

        else:
            j = AvailableHosts(     name=name,
                                    host=ip,
                                    username=username,
                                    ssh_port=int(port),
                                    password=password,
                                    interface=interface,
                                    creds_valid=True

            )
            j.save()
            a['info_message'] = "Host %s was created." % ip
            notifications.append("Host %s was created." % ip)
    else:
        pass
    return render(request, "AddNewServer.html", a)

def RemoveMachine(request):
    if request.method != "POST":
        return redirect("/")
    else:
        temp = AvailableHosts.objects.get(id=int(request.POST.get('key_id')))
        temp.delete()
    return redirect("/ViewHosts")

def ViewHosts(request):
    a = {}
    a['page'] = "ViewHosts"
    a['title'] = "Active Hosts"
    a['devices'] = AvailableHosts.objects.all()
    return render(request, "ViewHosts.html", a)

def AddNewHoneypot(request):
    a = {}
    a['page'] = "AddNewHoneypot"
    a['title'] = "Add A New Honeypot"
    a['alloss'] = _get_os_list()
    a['devices'] = AvailableHosts.objects.all()
    a['services'] = HONEYD_SCRIPTS

    if request.method == "POST":
        # Do POST Here
        if str(request.POST.get('name')) == 'Honeypot Name':
            a['info_message'] = "You need to choose a name."
            return render(request, "AddNewHoneypot.html", a)

        myDict = dict(request.POST.iterlists())

        scripts = []

        for item in myDict.iteritems():
            if item[0] == 'name':
                name = item[1][0]
            elif item[0] == 'hostname':
                hostname = item[1][0]
            elif item[0] == 'device':
                device_id = int(item[1][0])
            elif item[0] == 'csrfmiddlewaretoken':
                pass
            elif item[1][0] == 'on':
                scripts.append(item[0])
            elif item[0] == 'imitation':
                imitation = item[1][0]

        # Check that there is no honeypot with that name
        try:
            temp = HoneyPots.objects.filter(name=name)
            if len(temp) is not 0:
                a['info_message'] = "The name you have chosen already exists."
                return render(request, "AddNewHoneypot.html", a)
        except:
            pass

        # Check that the host exists
        try:
            relativeHost = AvailableHosts.objects.get(id=device_id)
        except:
            a['info_message'] = "Could not obtain host device!"
            return render(request, "AddNewHoneypot.html", a)

        # Create the Honeypot Object
        try:
            newHoneyPot = HoneyPots(name=name, personality=imitation, ip=hostname, state=False, relHost=relativeHost, pid=0, honey_id=0)
            newHoneyPot.save()

        except:
            a['info_message'] = "An unknown error occured when creating your honeypot."
            return render(request, "AddNewHoneypot.html", a)

        # Create Services
        newHoneyPot = HoneyPots.objects.get(name=name)

        if len(scripts) is 0:
            a['notifications'] = notifications
            return redirect("/ViewHoneyPots")

        else:
            for service in scripts:
                tempService = Services(relHoneypot=newHoneyPot, name=service)
                tempService.save()
            notifications.append("Honeypot %s created." % name)
            a['notifications'] = notifications
            return redirect("/ViewHoneyPots")
        a['notifications'] = notifications
        return render(request, "AddNewHoneypot.html", a)
    else:
        return render(request, "AddNewHoneypot.html", a)

def RemoveHoneypot(request):
    a = {}
    if request.method != "POST":
        a['notifications'] = notifications
        return redirect("/")
    else:
        temp = HoneyPots.objects.get(id=int(request.POST.get('key_id')))
        temp.delete()
    a['notifications'] = notifications
    return redirect("/ViewHoneyPots")

def ViewHoneypots(request):
    a = {}
    a['page'] = "ViewHoneypots"
    a['title'] = "View Honeypots"
    a['honeypots'] = HoneyPots.objects.all()
    a['notifications'] = notifications
    return render(request, "ViewHoneypots.html", a)

def DownloadConfigurations(request):
    if "POST" not in str(request.method):
        return redirect("/")
    # Verify we got a 'key_id' parameter
    try:
        this_id = int(request.POST["key_id"])
    except:
        return redirect("/")

    # Get Honeypot Matching ID
    try:
        hpObj = HoneyPots.objects.get(id=this_id)
    except:
        return redirect("/")

    GetGlobalVars(globals())

    # Build Configuration file
    scripts = []
    temp = Services.objects.filter(relHoneypot=hpObj)
    if len(temp) is not 0:
        for script in temp:
            scripts.append(script.name)
    conf_string = _build_honeyd_configuration_file(     machine_name=hpObj.name,
                                                        personality=hpObj.personality,
                                                        ip=hpObj.ip,
                                                        ping_response=True,
                                                        services=scripts)
    a={}
    a['hp'] = hpObj
    a['conf_string'] = conf_string
    return render(request, "DownloadConfiguration.html", a)

def StartHoneypot(request):
    a = {}
    a['title'] = "Start the Honeypot"
    a['page'] = "StartHoneypot"
    a['info_message'] = ""
    a['honeypots'] = HoneyPots.objects.all()
    a['notifications'] = notifications

    if "POST" not in str(request.method):
        return redirect("/")

    # Verify we got a 'key_id' parameter
    try:
        this_id = int(request.POST["key_id"])
    except:
        a['info_message'] = "Could not get the 'key_id' parameter."
        return render(request, "ViewHoneypots.html", a)

    # Get Honeypot Matching ID
    try:
        hpObj = HoneyPots.objects.get(id=this_id)
    except:
        a['info_message'] = "Could not find that honeypot ID."
        return render(request, "ViewHoneypots.html", a)

    GetGlobalVars(globals())

    # Build Configuration file
    scripts = []
    temp = Services.objects.filter(relHoneypot=hpObj)
    if len(temp) is not 0:
        for script in temp:
            scripts.append(script.name)
    conf_string = _build_honeyd_configuration_file(     machine_name=hpObj.name,
                                                        personality=hpObj.personality,
                                                        ip=hpObj.ip,
                                                        ping_response=True,
                                                        services=scripts)


    # Create the HoneyDWrapper
    try:
        newWrapper = HoneyDWrapper(
                            host=hpObj.relHost.host,
                            port=hpObj.relHost.ssh_port,
                            network_interface=hpObj.relHost.interface,
                            creds=[hpObj.relHost.username, hpObj.relHost.password],
                            configurations=conf_string,
                            machines_ip=hpObj.ip
        )
    except:
        hpObj.relHost.creds_valid = False
        notifications.append("Credentials for host %s are not valid."%hpObj.relHost.host)
        a['notifications'] = notifications
        return render(request, "ViewHoneypots.html", a)

    newWrapper._WriteConfigurationFile()
    pid = newWrapper._StartHoneyd()

    # Starting a listener to accept output
    retrieverObj = GoldenRetriver(honey_id=newWrapper.conf_id,port=newWrapper.conf_id)
    thread = Thread(target=retrieverObj.StartListening, args=())
    thread.start()
    retriever_threads[newWrapper.conf_id] = thread
    puppies[newWrapper.conf_id] = retrieverObj

    # Starting Retriver in Client:
    newWrapper._CreateAndUploadRetriever()

    if pid is ERR:
        a['info_message'] = "Error starting the honeypot."
        return render(request, "ViewHoneypots.html", a)

    else:
        hpObj.state = True
        hpObj.honey_id = newWrapper.conf_id
        hpObj.save()
        active_honeypots.append([hpObj.honey_id, newWrapper])
        a['info_message'] = "Honeypot Started!."
        notifications.append("Honeypot %s was started." % hpObj.name)
        a['notifications'] = notifications

        return render(request, "ViewHoneypots.html", a)

def StopHoneypot(request):
    a = {}
    a['title'] = "Stop the Honeypot"
    a['page'] = "StopHoneypot"
    a['info_message'] = ""
    a['honeypots'] = HoneyPots.objects.all()
    a['notifications'] = notifications

    if "POST" not in str(request.method):
        return redirect("/")

    # Verify we got a 'key_id' parameter
    try:
        this_id = int(request.POST["key_id"])
    except:
        a['info_message'] = "Could not get the 'key_id' parameter."
        return render(request, "ViewHoneypots.html", a)

    # Get Honeypot Matching ID
    try:
        hpObj = HoneyPots.objects.get(id=this_id)
    except:
        a['info_message'] = "Could not find that honeypot ID."
        return render(request, "ViewHoneypots.html", a)

    # Kill retrieverObj
    try:
        puppies[this_id].KillItDeadJohnny()
        del puppies[this_id]
        retriever_threads[this_id].join()
        del retriever_threads[this_id]
    except:
        pass

    try:
        for key, val in active_honeypots:
            if key == this_id:
                val._KillItDead()
        a['info_message'] = "Honeypot stopped."
        hpObj.state = False
        hpObj.honey_id = 0
        hpObj.save()
        notifications.append("Honeypot %s was killed." % hpObj.name)
        a['notifications'] = notifications
        return render(request, "ViewHoneypots.html", a)

    except KeyError:
        a['info_message'] = "Could not find and kill the connection."
        hpObj.state = False
        hpObj.honey_id = 0
        hpObj.save()
        notifications.append("Honeypot %s was killed." % hpObj.name)
        a['notifications'] = notifications
        return render(request, "ViewHoneypots.html", a)

def RefreshLogs(request):
    a = {}
    a['title'] = "Refresh Logs"
    a['page'] = "ViewHosts"
    a['info_message'] = ""
    a['honeypots'] = HoneyPots.objects.all()

    activehoneypots = HoneyPots.objects.filter(state=True)
    if len(activehoneypots) is 0:
        a['info_message'] = "There are no active honeypots."
        return render(request, "ViewHoneyPots.html", a)

    for id, connection in active_honeypots:
        temp = connection._GetLogFile()
        if temp is ERR:
            a['info_message'] += "Could not get log for %s. " % connection.conf_id
            return render(request, "ViewHosts.html", a)
        else:
            # Here we analyze log file and put it into DB:
            _analyzeLogFile(logdata=''.join(temp),conf_id=connection.conf_id)
            a['info_message'] = "Completed analysis."
            notifications.append("Refreshed log files.")

    a['notifications'] = notifications
    return redirect("/ViewLogEvents")

def ViewLogEvents(request):
    a = {}
    a['page'] = "ViewLogs"
    a['title'] = "View All Logs"
    a['events'] = Events.objects.all()
    a['notifications'] = notifications
    return render(request, "HoneyPotsLogs.html", a)

def ClearLogs(request):
    events = Events.objects.all()
    for ev in events:
        ev.delete()
    notifications.append("Logs cleared.")
    return redirect("/ViewLogEvents")

def ClearNotifications(request):
    notifications = []
    return redirect("/")

def PopNotification(notification_text):
    notifications.append(notification_text)

def ViewEvents(request):
    a = {}
    a['page'] = "ViewEvents"
    a['subtitle'] = "View all evaluations and analysis of events in the log"
    a['title'] = "View Events"
    a['evals'] = Evaluation.objects.all()
    a['notifications'] = notifications
    return render(request, "ViewEvents.html", a)

def ClearEvals(request):
    events = Evaluation.objects.all()
    for ev in events:
        ev.delete()
    notifications.append("Evaluations cleared.")
    return redirect("/ViewEvents")

def _apiGetLogs(request):
    a = {}
    a['api_data'] = serializers.serialize('json', Events.objects.all())
    return render(request, 'api.html', a)

def _apiGetEvals(request):
    a = {}
    a['api_data'] = serializers.serialize('json', Evaluation.objects.all())
    return render(request, 'api.html', a)

def _apiGetHoneypots(request):
    a = {}
    a['api_data'] = serializers.serialize('json', HoneyPots.objects.all())
    return render(request, 'api.html', a)

def _apiGetDevices(request):
    a = {}
    a['api_data'] = serializers.serialize('json', AvailableHosts.objects.all())
    return render(request, 'api.html', a)
