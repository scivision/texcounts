#!/usr/bin/env python
'''
 Michael Hirsch 2014
 Reads a .tex file (say, your PhD dissertation) and plots the counts vs time
 TeXcount, then optionally can post that png to an HTML server.
 '''
from texcounts import moddet
from texcounts.plots import plotTexStats
from texcounts.ssh import uploadSFTP

def main(texfn,upload,verbose):
#%% detect and store detected modification statistics
    counts,change = moddet(texfn,verbose)
#%% plot the results, incorporating earlier logged results
    plotTexStats(counts,texfn,verbose,change)
#%% upload to server
    if counts[0,0] and upload[0] is not None:
        uploadSFTP(upload[0],upload[1],upload[2],texfn)


if __name__ == "__main__":
    from argparse import ArgumentParser
    p = ArgumentParser(description='Computes statistics of your Latex document')
    p.add_argument('texfn',help='filename of master .tex file to analyze')
    p.add_argument('-v','--debug',help='debug messages',action='store_true')
    p.add_argument('-u','--upload',help='upload result to server with (username serverurl serverdirectory)',nargs=3,default=(None,)*3)
    ar = p.parse_args()

    main(ar.texfn,ar.upload,ar.debug)
