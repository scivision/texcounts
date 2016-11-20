from pathlib import Path
from datetime import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as md
import shutil

def plotTexStats(data,texfn,debugon,texChanged):
    texfn = Path(texfn).expanduser()

    imgfn = texfn.with_suffix('.png')

    daten=[dt.fromtimestamp(ts) for ts in data[:,0]]
    #if debugon: print(daten)
    print(texfn,'first / last mod time',daten[0].strftime('%Y-%m-%dT%H:%M:%S'),' / ',
           daten[-1].strftime('%Y-%m-%dT%H:%M:%S'))


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
        if imgfn.is_file(): #data file already exists
            imgModTime = dt.fromtimestamp(imgfn.stat().st_mtime).strftime('%Y-%m-%dT%H-%M-%S')
            oldFN = imgfn + '-' + imgModTime + '.png'
            if debugon:
                print("Moving {} to {}".format(imgfn, oldFN))
            shutil.move(imgfn,oldFN)

        if debugon:
            print('saving updated figure {}'.format(imgfn))
        fg.savefig(imgfn,bbox_inches='tight')
    plt.show()