# Michael Hirsch 2014
# http://blogs.bu.edu/mhirsch
# GPL v3+ License
# Reads a .tex file (say, your PhD dissertation) and plots the counts vs time 
#   TeXcount, then optionally can post that png to an HTML server.

# tested with Python 2.7.5 and 3.3.2 on Linux
import sys,os,shutil
import numpy as np
from datetime import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as md
import subprocess
import re
import paramiko
import getpass

def main(argv):
    nargin = len(sys.argv)
    debugon = False #verbose messages to console
    imgExt = '.png'

    if not ((nargin==2) or (nargin==5)):
        sys.exit('example: python texwcpost.py diss.tex')
    texFN = sys.argv[1]
    # nargin=5, user wants upload 
    if (nargin == 5): 
        doUpload = True
        serverAddress = sys.argv[2]
        username = sys.argv[3]
        serverDir = sys.argv[4]
    else: doUpload = False
#--- handle filenames ------
    texPath = os.path.dirname(texFN) + '/'
    texStem = os.path.splitext(os.path.basename(texFN))[0]

    logFN = texPath + texStem + '.progressLog'
    imgFN = texPath + texStem + imgExt

    if not os.path.isfile(texFN): sys.exit('file does not exist: ' + texFN)

# detect and store detected modification statistics
    (data,texChanged) = TexModDet(texFN,logFN,debugon)  
       
# plot the results, incorporating earlier logged results
    plotTexStats(data,logFN,texStem,imgFN,debugon)

# upload to server
    if doUpload and texChanged:
        uploadSFTP(username,serverAddress,serverDir,imgFN)
######### END OF MAIN #######################
def TexModDet(texFN,logFN,debugon):
    texModTime = str(os.path.getmtime(texFN))

### use texcount to count words
    sysCall = ['texcount','-dir','-inc','-brief','-total',texFN]
    if debugon: print(sysCall)
    procout = subprocess.Popen(sysCall,stdout=subprocess.PIPE,shell=False)
    tclin = str(procout.stdout.read())#.rstrip()
    print('TeXcount output:  ' + tclin)
    #parse the line (regexp) #note if terminal text has colors imposed, regex can 
    # trip up on this (e.g. red error text). I have mitigated this by using more
    # specific regex terms for each term sought.
    wordRE = '\d+(?=\+\d+\+\d+)'
    wordREC = re.compile(wordRE)
    wordc = wordREC.findall(tclin)[0]
    #
    tabfigRE = '\d+(?=\/\d+\/\d+\)\ Total)'
    tabfigREC = re.compile(tabfigRE)
    tabfigc = tabfigREC.findall(tclin)[0]
    #
    eqnRE = '\d+(?=\)\ Total)'
    eqnREC = re.compile(eqnRE)
    eqnc = eqnREC.findall(tclin)[0]
    
    # one-line texcount output format
    # Words in text
    # Words in headers
    # Words in float captions
    # Number of headers
    # Number of floats 
    # Number of math inlines
    # Number of math displayed
    
    #load previous data
    data = np.loadtxt(logFN,delimiter=',')
    if debugon: print(data)
    
#store line for log
    #has data changed (compare with last log line)
    # note this would fail to detect if number of words deleted and added were equal and the like
    # but to me that's a corner case I don't care about WONTFIX
    texChanged = (np.array([texModTime,wordc,tabfigc,eqnc]) == data[-1,:])
    
    if texChanged:
        currLogLine = texModTime + ',' +wordc + ',' + tabfigc + ',' + eqnc + '\n'
        print('writing ' + currLogLine.rstrip() + ' to ' + logFN)
        with open(logFN, "a") as myfile:
            myfile.write(currLogLine)
    else: #maybe user wants to try uploading again due to mistyped password or server outage
        print('no modifications to ' + texFN + ' detected, not appending to log or posting')
    return data,texChanged
#########################

def plotTexStats(data,logFN,texStem,imgFN,debugon):
    if not os.path.isfile(logFN): sys.exit('file does not exist: ' + logFN)
   
    #print(data)

    if (data.ndim==1): #this is a corner case
       nRows=1
       nCols=len(data)
       data=np.array(data).reshape(1,nCols) #make (1,nCols) 2D array for plt code reuse
       daten = dt.fromtimestamp(data[0,0])
       print(texStem + ' lastModTime ' + daten.strftime('%Y-%m-%dT%H:%M:%S'))
    else:  #ndim==2
       daten=[dt.fromtimestamp(ts) for ts in data[:,0]]
       if debugon: print(daten)
       print(texStem + ' first / last mod time ' + daten[0].strftime('%Y-%m-%dT%H:%M:%S') + ' / ' 
               + daten[-1].strftime('%Y-%m-%dT%H:%M:%S'))
    if debugon: print(str(nRows) + ' / ' + str(nCols) + ' row /col of data to process ')
    
    daten=md.date2num(daten)
    
    fig = plt.figure()
    ax1 = plt.gca() 
    ax2 = ax1.twinx()
    
    
    ax1.set_xlabel("Date")
    ax1.set_ylabel('Word Count')
    ax2.set_ylabel('Equation Count')
    
    ax1.plot(daten,data[:,1], linestyle='-', marker='o', color='b',label='Words')
    ax2.plot(daten,data[:,3], linestyle='-', marker='o', color='r',label='Equations')
    xLo = data[0,0]-86400 #set lower xlim to be 1 day prior to earliest data (fixes one data point corner case)
    xHi = data[-1,0]+86400 #set lower xlim to be 1 day after earliest data (fixes one data point corner case)
    ax1.set_xlim( dt.fromtimestamp(xLo), dt.fromtimestamp(xHi)) 
    
    if (xHi-xLo < 3*86400): xFmt = '%Y-%m-%dT%H'
    else: xFmt = '%Y-%m-%d'
    
    ax1.xaxis.set_major_formatter(md.DateFormatter(xFmt))
    
    for tl in ax1.get_yticklabels(): tl.set_color('b')
    
    for tl in ax2.get_yticklabels(): tl.set_color('r')
    
    #ax1.legend()
    #ax2.legend()
    plt.title("Dissertation Progress")
    fig.autofmt_xdate()
    
    if os.path.isfile(imgFN): #data file already exists
        imgModTime = dt.fromtimestamp(os.path.getmtime(imgFN)).strftime('%Y-%m-%dT%H-%M-%S')
        oldFN = imgFN + '-' + imgModTime + '.png'
        if debugon: print("Moving " + imgFN + " to " + oldFN)
        shutil.move(imgFN,oldFN )
    
    if debugon: print('saving updated figure ' + imgFN)
    plt.savefig(imgFN,bbox_inches='tight')
    plt.show()
    
def uploadSFTP(username,serverAddress,serverDir,imgFN):
    print('Uploading ' + imgFN + ' to ' + serverAddress + ' ' + serverDir)
    imgName = os.path.splitext(os.path.basename(imgFN))[0]
     
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
    ssh.connect(serverAddress, username=username,password=getpass.getpass(prompt='password: '))
    sftp = ssh.open_sftp()
    sftp.put(imgFN, serverDir+imgName,confirm=True) #note that destination filename MUST be included!
    sftp.close()
    ssh.close()  
    #NOTE: I didn't enable a return code from paramiko, if any is available   

if __name__ == "__main__":
    sys.exit(main(sys.argv))
