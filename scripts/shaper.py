#!/usr/bin/env python2


# This Script will do shape analysis on the trajectory
# and produce the polygons of the different cells.
import argparse
import sys
import matplotlib
import os
matplotlib.use('agg')

import matplotlib.pyplot as plt
import numpy as np
from math import ceil
from time import sleep


desc ="""
Creates graphs of an arbitrary number of timestamps relating to cell shape.
This includes voronoi diagrams, and cross-sections.
"""

parser = argparse.ArgumentParser(description=desc)
parser.add_argument("trajPath", nargs=1 ,
                     help="Path to the trajectory file.")
parser.add_argument("timeStamps", nargs='+', type=int,
                     help="Space separated timestamps")

args = parser.parse_args()
#print (args.trajPath)

#minNumArgs = 2
#
#errorMessage = """
#Usage: shaper input timeStep1 timeStep2 ...
#
#input:      Path to the trajectory output by the simulation.
#output:     Path to save a xyz file of the time step requested for viewing in vmd,
#            etc.
#timeStep1, timeStep2, ...:  list of time stemps, use any number of them you like
#                            Unknown behaviour if greater than simulation time.
#"""
#
#if len(sys.argv) < minNumArgs:
#    print errorMessage
#    sys.exit(1)
#
#
trajPath = os.path.abspath(args.trajPath[0])
storPath, fileName = os.path.split(trajPath)
fileName = os.path.splitext(fileName)[0]
storPath += "/" + fileName + '/cross_sections/'
doneSeek = False
step = 0

timeStamps = [int(ts) for ts in args.timeStamps]
timeStamps.sort()

# Make directory to store images
try:
    os.makedirs(storPath)
except:
    0




ax=[]



def getNonNans(a):
    nans = np.isnan(a)
    notnans = np.invert(nans)
    return a[notnans]


# First get the maxima

def reverse_readline(filename, buf_size=8192):
    """a generator that returns the lines of a file in reverse order"""
    """http://stackoverflow.com/a/23646049/1186564"""
    with open(filename) as fh:
        segment = None
        offset = 0
        fh.seek(0, os.SEEK_END)
        total_size = remaining_size = fh.tell()
        while remaining_size > 0:
            offset = min(total_size, offset + buf_size)
            fh.seek(-offset, os.SEEK_END)
            buffer = fh.read(min(remaining_size, buf_size))
            remaining_size -= buf_size
            lines = buffer.split('\n')
            # the first line of the buffer is probably not a complete line so
            # we'll save it and append it to the last line of the next buffer
            # we read
            if segment is not None:
                lines[-1] += segment
            segment = lines[0]
            for index in range(len(lines) - 1, 0, -1):
                yield lines[index]
        yield segment



tX = []; tY = []; tZ = [];
tCMx = 0; tCMy = 0; tCMz = 0
for line in reverse_readline(trajPath):
    if "Step" in line:
        break
    if line == '':
        continue

    line = line.split(",  ")

    x = float(line[0])
    y = float(line[1])
    z = float(line[2])

    tCMx += x; tCMy += y; tCMz += z;

    tX.append(x)
    tY.append(y)
    tZ.append(z)


tX = np.array(tX)
tY = np.array(tY)
tZ = np.array(tZ)
num = tX.size
tCMx = tCMx/num
tCMy = tCMy/num
tCMz = tCMz/num

xMax = tX.max() - tCMx; yMax = tY.max() - tCMy; zMax = tZ.max() - tCMz;
xMin = tX.min() - tCMx; yMin = tY.min() - tCMy; zMin = tZ.min() - tCMz;

maxes = {"X":[xMax, xMin], "Y": [yMax, yMin], "Z":[zMax, zMin]}


def Normalize (X, Y, Z, CMx, CMy, CMz):
    """
    Get rid of all bad data, then normalize
    """
    print "Normalizing..."

    # Get rid of zeros
    X = X[X != 0.0]
    Y = Y[Y != 0.0]
    Z = Z[Z != 0.0]

    X = getNonNans(X)
    Y = getNonNans(Y)
    Z = getNonNans(Z)

    CMx = getNonNans(CMx)
    CMy = getNonNans(CMy)
    CMz = getNonNans(CMz)

    # Normalize
    CMX = CMx.sum() / CMx.size
    CMY = CMy.sum() / CMy.size
    CMZ = CMz.sum() / CMz.size

    X = X - CMX
    Y = Y - CMY
    Z = Z - CMZ

    CMx = CMx - CMX
    CMy = CMy - CMY
    CMz = CMz - CMZ

    return X, Y, Z, CMx, CMy, CMz




def Voro (X, Y, ts, xstr, ystr):
    """Compute the voronoi diagram for a given set of points"""
    points = np.zeros([X.size, 2])
    for i in xrange(X.size):
        points[i,0] = X[i]
        points[i,1] = Y[i]

    voronoi = Voronoi(points)
    voronoi_plot_2d(voronoi)
    plt.title("CoM Voronoi\ntime stamp = %s" % ts)
    plt.xlabel(xstr)
    plt.ylabel(ystr)
    plt.savefig("%s%s_vor_%s.png" % (ts, xstr, ystr))

def CrossSections(newX, newY, newZ, Xstr, Ystr, Zstr, ts, inc=0.1, thresh=0.1):
    """
    This function generates and saves cross section slices of the system.
    X, Y are the axes of the plane of intersection
    Z is the perpendicular to the name.
    Any combination of cartesian plane and normal may be given.
    e.g. MakeImages(X, Z, Y, "X", "Z", "Y", ts) will generate XZ planes moving
    along the Y axis.
    """
    xMax, xMin = maxes[Xstr]
    yMax, yMin = maxes[Ystr]
    c = 0
    print "Making %s%s cross-sections at %d..." % (Xstr, Ystr, ts)
    for dz in np.arange(newZ.min(), newZ.max(), inc):
        # Get the points within a threshold distance of the plane
        nearMask = np.abs(newZ - dz) < thresh
        nearX = newX[nearMask]
        nearY = newY[nearMask]
        c += 1

        # Start plotting
        plt.plot(nearX, nearY, '.', lw=0.5, color="#AAAAAA")
        # The two lines below stop distortion
        #plt.axis('equal')
        plt.axis('scaled')
        plt.xlim(xMin, xMax)
        plt.ylim(yMin, yMax)
        #plt.axis([X.min(), X.max(),
        #          Y.min(), Y.max()])
        plt.title("%s=%f" % (Zstr, dz))
        plt.xlabel("%s" % Xstr)
        plt.ylabel("%s" % Ystr)
        ax=plt.gca()
        ax.set_axis_bgcolor("#404040")
        name = "%d_shapes_%s%s_%d.jpg" % (ts, Xstr, Ystr, c)
        name = storPath + name
        #print "saving to %s ..." % name
        plt.gcf().set_size_inches(10, 10)
        plt.savefig(name)
        plt.close()




X = []
Y = []
Z = []

CMx = []
CMy = []
CMz = []

CM_x = 0
CM_y = 0
CM_z = 0


with open(trajPath) as trajFile:
    for timeStamp in timeStamps:
        # First seek the time step to begin processing
        print "Moving to time step %d..." % timeStamp
        while True:
            line = trajFile.readline().strip()
            # First line is always no. of atoms
            nAtoms = int(line)
            # Second line is always a comment with the time step no.
            line = trajFile.readline().strip()
            step = int(line[6:])
            if (step >= timeStamp):
                break

            # Start skipping lines with coordinates
            for n in xrange(nAtoms):
                line = trajFile.readline()

        # Should be at the correct time step now
        # Begin processipng
        # For now only do one time step
        nCells = nAtoms/192
        print "We have %d cells at t = %d" % (nCells, timeStamp)
        for n in xrange(nCells):
            for m in xrange(192):
                line = trajFile.readline().strip()
                line = line.split(",  ")

                x = float(line[0])
                y = float(line[1])
                z = float(line[2])

                X.append(x)
                Y.append(y)
                Z.append(z)

                CM_x += x
                CM_y += y
                CM_z += z


            CMx.append(CM_x/192)
            CMy.append(CM_y/192)
            CMz.append(CM_z/192)

            CM_x = 0
            CM_y = 0
            CM_z = 0

        # Done getting coordinates, begin processing
        print "Converting to arrays..."
        X = np.array(X)
        Y = np.array(Y)
        Z = np.array(Z)

        CMx = np.array(CMx)
        CMy = np.array(CMy)
        CMz = np.array(CMz)

        X, Y, Z, CMx, CMy, CMz = Normalize(X, Y, Z, CMx, CMy, CMz)

        # do YZ plane, vary X
        CrossSections(Y, Z, X, "Y", "Z", "X", timeStamp)

        # do XZ plane, vary Y
        CrossSections(X, Z, Y, "X", "Z", "Y", timeStamp)

        # do XY plane, vary Z
        CrossSections(X, Y, Z, "X", "Y", "Z", timeStamp)

        X = []
        Y = []
        Z = []
        CMx = []
        CMy = []
        CMz = []
