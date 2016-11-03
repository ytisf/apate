

def GetGlobalVars(glob): # glob is simply a dict.
    glob["active_honeypots"] = []
    glob["notifications"] = []
    glob["puppies"] = {}
    glob["retriever_threads"] = {}
    glob["existingSSH"] = {}
