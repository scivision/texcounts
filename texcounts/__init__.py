from pathlib import Path
from subprocess import check_output
from numpy import array
from numpy import loadtxt,vstack,atleast_2d

def getcounts(fn):
    fn = Path(fn).expanduser()
    #usually the main file hasnt been modified. Find the most recently modified .tex in this directory
    modtime=max([f.stat().st_mtime for f in fn.parent.glob('*.tex')])
#%% use texcount to count words
    cmd = ('texcount','-dir','-inc','-brief','-total',str(fn))

    stdout = check_output(cmd)
    line = stdout.decode('utf-8')

    cword  = int(line.split('+')[0]) + int(line.split('+')[2].split(' ')[0])
    cfloat = int(line.split('/')[1].split('/')[0])
    ceqn   = int(line.split('/')[2]) + int(line.split('/')[3].split(')')[0])

    counts = array([modtime, cword, cfloat, ceqn])
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

    return counts,modtime

if __name__ == '__main__':
    """
    what is an AGU Publication Unit?
    Each pub unit is equal to either 500 words, one figure, or one table.
    By “words,” AGU is only counting the abstract, main article, and captions,
    not the title, authors, affiliations, or references.
    The new “length limit” for JGR-Space of 25 pub units (before extra fees kick in)
    is roughly equal to the old limit of 10 double-column pages.
    """
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument('fn')
    p = p.parse_args()

    counts = getcounts(p.fn)

def TexModDet(texfn,verbose):

    counts,modtime = getcounts(texfn)


    logfn = texfn.with_siffix('.progressLog')
    #load previous data
    try:
        data = loadtxt(logfn,delimiter=',')

        dataChanged = counts[1:] != data[-1,1:] #don't directly compare time, float precision issue!
        mtimeDiff = counts[0] - data[-1,0]
        mtimeChanged = mtimeDiff < -0.01 #precision limit of strftime
        texChanged = dataChanged.any() or mtimeChanged
        if verbose:
            print(data)
            print('--------')
            print(data[-1,:])
            print(counts)
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
        currLogLine = (','.join((str(modtime),str(counts[1]),str(counts[2]),str(counts[3]) + '\n')))
        print('writing {} to {}'.format(currLogLine.rstrip(), logfn))

        with logfn.open("a") as myfile:
            myfile.write(currLogLine)

        if data is not None:
            data = vstack( (data, counts) )
        else: #first time run
            data = counts

        if verbose:
            print(data.shape)
    else:
        print('no modifications to {} detected, not appending to log or posting'.format(texfn))
    return atleast_2d(data),texChanged
