#!/usr/bin/env python3
'''
 Michael Hirsch 2014
 http://blogs.bu.edu/mhirsch
 GPL v3+ License
 Reads a .tex file (say, your PhD dissertation) and plots the counts vs time
 TeXcount, then optionally can post that png to an HTML server.
 tested with Python 2.7 and 3.4 on Linux
 '''
import shutil
from glob import glob
from os.path import dirname, splitext, basename,isfile, getmtime,expanduser, join
import numpy as np
from datetime import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as md
import subprocess
import re
from paramiko import SSHClient, AutoAddPolicy
import getpass

def main(texFN,imgExt,upload,dbglvl):
    texFN = expanduser(texFN)
#--- handle filenames ------
    texPath = dirname(texFN)
    texStem = splitext(basename(texFN))[0]

    logFN = join(texPath,texStem + '.progressLog')
    imgName = texStem + imgExt
    imgFN = join(texPath, imgName)

    if not isfile(texFN): raise RuntimeError('file does not exist: ' + texFN)

# detect and store detected modification statistics
    (data,texChanged) = TexModDet(texFN,texPath,logFN,dbglvl)

#%% plot the results, incorporating earlier logged results
    plotTexStats(data,logFN,texStem,imgFN,dbglvl,texChanged)
#%% upload to server
    if texChanged and upload[0] is not None:
        uploadSFTP(upload[0],upload[1],upload[2],imgFN,imgName)
#%%
def TexModDet(texFN,texPath,logFN,debugon):
	#usually the main file hasnt been modified. Find the most recently modified .tex in this directory
    texModTime=max([getmtime(f) for f in glob(join(texPath,'*.tex'))])
#%% use texcount to count words
    sysCall = ('texcount','-dir','-inc','-brief','-total',texFN)
    print(sysCall)
    procout = subprocess.Popen(sysCall,stdout=subprocess.PIPE,shell=False)
    tclin = procout.stdout.read().decode('utf-8')
    print(tclin)
    #parse the line (regexp) #note if terminal text has colors imposed, regex can
    # trip up on this (e.g. red error text). I have mitigated this by using more
    # specific regex terms for each term sought.
    wordRE = '\d+(?=\+\d+\+\d+)'
    wordREC = re.compile(wordRE)
    wordc = int(wordREC.findall(tclin)[0])

    tabfigRE = '\d+(?=\/\d+\/\d+\)\ Total)'
    tabfigREC = re.compile(tabfigRE)
    tabfigc = int(tabfigREC.findall(tclin)[0])

    eqnRE = '\d+(?=\)\ Total)'
    eqnREC = re.compile(eqnRE)
    eqnc = int(eqnREC.findall(tclin)[0])

    currNumData = np.array([texModTime,wordc,tabfigc,eqnc])
    '''
     one-line texcount output format:
     Words in text
     Words in headers
     Words in float captions
     Number of headers
     Number of floats
     Number of math inlines
     Number of math displayed
    '''

    #load previous data
    try:
        data = np.atleast_2d(np.loadtxt(logFN,delimiter=','))

        dataChanged = currNumData[1:] != data[-1,1:] #don't directly compare time, float precision issue!
        mtimeDiff = currNumData[0] - data[-1,0]
        mtimeChanged = mtimeDiff < -0.01 #precision limit of strftime
        texChanged = dataChanged.any() or mtimeChanged
        if debugon:
            print(data)
            print('--------')
            print(data[-1,:])
            print(currNumData)
            print(dataChanged)
            print(mtimeChanged)
            print(texChanged)
            print(mtimeDiff)
    except FileNotFoundError:
        print('first time run')
        data = None
        texChanged = True
#%% store line for log
    #has data changed (compare with last log line)
    # note this would fail to detect if number of words deleted and added were equal and the like
    # but to me that's a corner case I don't care about WONTFIX


    if texChanged:
        currLogLine = (','.join((str(texModTime),str(wordc),str(tabfigc),str(eqnc) + '\n')))
        print('writing ' + currLogLine.rstrip() + ' to ' + logFN)
        with open(logFN, "a") as myfile:
            myfile.write(currLogLine)
        if data is not None:
            data = np.vstack( (data,currNumData) )
        else: #first time run
            data = currNumData

        if debugon: print(data.shape)
    else:
        print('no modifications to ' + texFN + ' detected, not appending to log or posting')
    return data,texChanged
#%%
def plotTexStats(data,logFN,texStem,imgFN,debugon,texChanged):
    if not isfile(logFN): raise RuntimeError('file does not exist: ' + logFN)

    #print(data)

    if (data.ndim==1): #this is a corner case
       nRows=1
       nCols=len(data)
       data=np.array(data).reshape(1,nCols) #make (1,nCols) 2D array for plt code reuse
       daten = dt.fromtimestamp(data[0,0])
       print(texStem + ' lastModTime ' + daten.strftime('%Y-%m-%dT%H:%M:%S'))
    else:  #ndim==2
       nRows,nCols = data.shape
       daten=[dt.fromtimestamp(ts) for ts in data[:,0]]
       #if debugon: print(daten)
       print(texStem + ' first / last mod time ' + daten[0].strftime('%Y-%m-%dT%H:%M:%S') + ' / '
               + daten[-1].strftime('%Y-%m-%dT%H:%M:%S'))
    if debugon: print(str(nRows) + ' / ' + str(nCols) + ' row /col of data to process ')

    daten=md.date2num(daten)

    fg = plt.figure()
    ax1 = fg.gca()
    ax2 = ax1.twinx()


    ax1.set_xlabel("Date")
    ax1.set_ylabel('Word Count')
    ax2.set_ylabel('Equation, Figure, Table Count')

    ax1.plot(daten,data[:,1], linestyle='-', marker='.', color='b',label='Words')

    ax2.plot(daten,data[:,3], linestyle='-', marker='.', color='r',label='Equations')
    ax2.plot(daten,data[:,2], linestyle='-', marker='.', color='g', label='Figures + Tables')
    xLo = data[0,0]-86400 #set lower xlim to be 1 day prior to earliest data (fixes one data point corner case)
    xHi = data[-1,0]+86400 #set lower xlim to be 1 day after earliest data (fixes one data point corner case)
    ax1.set_xlim( dt.fromtimestamp(xLo), dt.fromtimestamp(xHi))

    if (xHi-xLo < 3*86400): xFmt = '%Y-%m-%dT%H'
    else: xFmt = '%Y-%m-%d'

    ax1.xaxis.set_major_formatter(md.DateFormatter(xFmt))

    for tl in ax1.get_yticklabels(): tl.set_color('b')

    for tl in ax2.get_yticklabels(): tl.set_color('r')

    #ax1.legend()
    ax2.legend(loc=2)
    ax1.set_title("Dissertation Progress")
    fg.autofmt_xdate()

    if texChanged:
        if isfile(imgFN): #data file already exists
            imgModTime = dt.fromtimestamp(getmtime(imgFN)).strftime('%Y-%m-%dT%H-%M-%S')
            oldFN = imgFN + '-' + imgModTime + '.png'
            if debugon: print("Moving " + imgFN + " to " + oldFN)
            shutil.move(imgFN,oldFN )

        if debugon: print('saving updated figure ' + imgFN)
        fg.savefig(imgFN,bbox_inches='tight')
    plt.show()
#%%
def uploadSFTP(username,serverAddress,serverDir,imgFN,imgName):
    print('Uploading ' + imgFN + ' to ' + serverAddress + ' ' + serverDir)

    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.load_host_keys(expanduser(join("~", ".ssh", "known_hosts")))
    ssh.connect(serverAddress, username=username,password=getpass.getpass(prompt='password: '))
    sftp = ssh.open_sftp()
    sftp.put(imgFN, serverDir+imgName,confirm=True) #note that destination filename MUST be included!
    sftp.close()
    ssh.close()
    #NOTE: I didn't enable a return code from paramiko, if any is available

if __name__ == "__main__":
    from argparse import ArgumentParser
    p = ArgumentParser(description='Computes statistics of your Latex document')
    p.add_argument('texfn',help='filename of master .tex file to analyze',type=str)
    p.add_argument('-i','--iext',help='extension e.g. .png of images',type=str,default='.png')
    p.add_argument('-d','--debug',help='debug messages',action='store_true')
    p.add_argument('-u','--upload',help='upload result to server with (username serverurl serverdirectory)',nargs=3,type=str,default=(None,None,None))
    ar = p.parse_args()

    main(ar.texfn,ar.iext,ar.upload,ar.debug)
