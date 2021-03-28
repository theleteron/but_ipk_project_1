#!/usr/bin/env python
"""Simple GET request implementation (FSP)

Author: Roman Janiczek (xjanic25@vutbr.cz)

"""
import argparse
import socket
import re
import os

def arguments():
    """Parses arguments and checks if all are provided
    """
    parser = argparse.ArgumentParser(description="Simple GET request implementation (FSP/1.0)")
    parser.add_argument('-n', dest='nameserver', type=str, help='Nameserver IP address and port number [IP:PORT]', required=True)
    parser.add_argument('-f', dest='surl', type=str, help="File SURL [only FSP protocol][PROTOCOL://DOMAIN/PATH]", required=True)   
    args = parser.parse_args()
    return args

def getServerIP(NSP, LOOKUP):
    """Get IP of the server from NAMESERVER

    Args:
        NSP: Nameserver address saved as tupple (IP, PORT)  
        LOOKUP: Server we are looking for

    Returns:
        Group that corresponds to matched regex
        For OK response
        ('OK', IP, PORT)
        For ERR respons
        ('ERR', DETAILS)
    """
    reqsip = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Request DOMAIN to IP translation
    reqsip.sendto("WHEREIS " + LOOKUP.encode('UTF-8'), NSP)
    # Check result from server (timeout in casse server is not responding)
    try:
        reqsip.settimeout(30)
        ressip = reqsip.recv(1024)
        result = re.match(r"(OK) ((.*):(.*))", ressip)
        if result is None:
            result = re.match(r"(ERR) (.*)", ressip)
        return result.groups()
    except socket.timeout:
        print("[ERROR][TIMEOUT] Nameserver haven't responded in time!")
        exit(0)

def getFileFromServer(NSP, PATH):
    """Download file from the server

    Args:
        NSP: Nameserver address saved as tupple (IP, PORT)
        PATH: File SURL containing server and path to file ('FSP://SERVER/PATH')
    
    Returns:
        Nothing or index 
    """
    # Get DOMAIN and PATH
    dompath = re.match(r"fsp:\/\/(.*)\/(.*)", PATH.lower())
    if dompath is None:
        print("[ERROR] Invalid path syntax!")
        exit(0)

    # Setup variables used in requests
    COMMAND = "GET"
    VERSION = "FSP/1.0"
    AGENT = "xjanic25"  
    DOMAIN = dompath.groups()[0]
    PATH = dompath.groups()[1]
    FILENAME = re.match(r".*\/(.*)", "/"+PATH).groups()[0]
    # Form a request on server
    REQI = COMMAND + " " + PATH + " " + VERSION + "\r\n" +  \
         "Hostname: " + DOMAIN + "\r\n" + "Agent: " + AGENT + "\r\n\r\n"

    # Get server IP and PORT
    SERVER = getServerIP(NSP, DOMAIN)
    if(SERVER[0] != 'OK'):
        # Something went wrong (Server not found, ...)
        print("[ERROR] " + SERVER[1])
        exit(0)
    else:
        reqfil = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Estabilish connection with server
        try:
            reqfil.connect((SERVER[2], int(SERVER[3])))
        except:
            print("[ERROR] Connection to " + DOMAIN + " failed")
            exit(0)

        print("[INFO] Connected to " + DOMAIN)
        # Send request
        print("[INFO] Sending request")
        reqfil.sendall(REQI.encode('UTF-8'))
        # Receive header
        resfil = reqfil.recv(32)
        answer = re.match(r"FSP/1.0 Success\r\nLength:(.*)\r(.*)", resfil)
        if answer is not None:
            print("[INFO] Downloading file " + FILENAME)
            with open(FILENAME, "wb") as f:
                f.write(answer.groups()[1])
                while True:
                    # Receive 1024 bytes
                    bytes_read = reqfil.recv(1024)
                    if not bytes_read:    
                        # Nothing received (end of transmission)
                        break
                    f.write(bytes_read)
            print("[INFO] File '" + FILENAME + "' received")
        else:
            print("[ERROR] File '" + PATH + "' could not be received!")
        reqfil.close()

def getAllFilesFromServer(NSP, PATH):
    """Download all files saved in index from server

    Args:
        NSP: Nameserver address saved as tupple (IP, PORT)
        PATH: File SURL containing server and path to file ('FSP://SERVER/PATH')
    
    Returns:
        Nothing
    """
    # Download index as a temporary file  
    getFileFromServer(NSP, PATH + "/index")
    # Go through file and download every indexed file
    with open("index", "r") as f:
        names = f.readlines()
        for name in names:
            getFileFromServer(NSP, PATH + "/" + name.strip())
    # Delete temporary index file
    os.remove("index")

if __name__ == "__main__":
    # Parse program arguments
    args = arguments()
    # Get nameserver IP and PORT as tupple
    nsmatch = re.match(r"(.*):(.*)", args.nameserver).groups()
    NAMESERVER = (nsmatch[0], int(nsmatch[1]))
    # Get SURL - PATH to the file
    SURL = args.surl
    # Proccess request
    getAll = re.match(r"(.*)\/\*", SURL)
    if getAll is None:
        getFileFromServer(NAMESERVER, SURL)
    else:
        getAllFilesFromServer(NAMESERVER, getAll.groups()[0])