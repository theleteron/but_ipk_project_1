#!/usr/bin/env python
"""Simple GET request implementation (FSP)

Author: Roman Janiczek (xjanic25@vutbr.cz)

"""
import argparse
import socket
import re

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
    reqsip.sendto("WHEREIS "+LOOKUP.encode('UTF-8'), NSP)
    # Check result from server
    ressip = reqsip.recv(1024)
    result = re.match(r"(OK) ((.*):(.*))", ressip)
    if result is None:
        result = re.match(r"(ERR) (.*)", ressip)
    return result.groups()

def getFileFromServer(NSP, PATH):
    """Download file from the server

    Args:
        NSP: Nameserver address saved as tupple (IP, PORT)
        PATH: File SURL containing server and path to file ('FSP://SERVER/PATH')
    
    Returns:
        Request result
    """
    # Get DOMAIN and PATH
    dompath = re.match(r"fsp:\/\/(.*)\/(.*)", PATH.lower())
    # Setup variables used in requests
    COMMAND = "GET"
    VERSION = "FSP/1.0"
    OWNER = "xjanic25"  
    DOMAIN = dompath.groups()[0]
    PATH = dompath.groups()[1]
    # Form a request on server
    REQI = COMMAND + " " + PATH + " " + VERSION + "\r\n" +  \
         "Hostname: " + DOMAIN + "\r\n" + "Agent: " + OWNER + "\r\n\r\n"
    # Get server IP and PORT
    SERVER = getServerIP(NSP, DOMAIN)
    if(SERVER[0] != 'OK'):
        # Something went wrong (Server not found, ...)
        print(SERVER[0] + " " + SERVER[1])
        exit(0)
    else:
        reqfil = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Estabilish connection with server
        reqfil.connect((SERVER[2], int(SERVER[3])))
        # Send request
        reqfil.sendall(REQI.encode('UTF-8'))
        # Check success
        resfil = reqfil.recv(32)
        answer = re.match(r"(FSP/1.0 Success)\r\nLength:(.*)\r", resfil).groups()
        if answer[0] == 'FSP/1.0 Success':
            resfil = reqfil.recv(int(answer[1]))
        print(resfil)
        reqfil.close()

if __name__ == "__main__":
    # Parse program arguments
    args = arguments()
    # Get nameserver IP and PORT as tupple
    nsmatch = re.match(r"(.*):(.*)", args.nameserver).groups()
    NAMESERVER = (nsmatch[0], int(nsmatch[1]))
    # Get SURL - PATH to the file
    SURL = args.surl
    # Proccess request
    getFileFromServer(NAMESERVER, SURL)