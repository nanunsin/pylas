"""
to use LAS library
 cmd> "pip install laspy"

""" 
import laspy
import sys, getopt
import os, shutil

class FilterData:
    def __init__(self, data):
        self.index = 0
        self.data = data
    def setIndex(self, index):
        self.index = index
    def getData(self):
        return (self.data, self.data)

class FilterReader:
    def __init__(self, filename):
        self.filename = filename
        self.fstarttime = 0.0
        self.fendtime = 0.0

    def readfile(self):
        ff = open(self.filename, "r")
        times = ff.readline().split(" ")
        self.fstarttime = times[0]
        self.fendtime = times[1]
        ff.close()

class TILAS:
    def __init__(self, argv):
        # files
        self.inputfile = ''
        self.outputfile = ''
        self.filterfile = ''
        self.logfile = ''
        # filter
        self.fstarttime = 0.0
        self.fendtime = 0.0
        # Set member var
        self.parseArgs(argv)

    def parseArgs(self, argv):
        try:
            opts, args = getopt.getopt(argv, "i:o:f:l:", ["input=","output=","filter=","log="])
        except getopt.GetoptError:
            print "las.py -i <inputfile> -o <outputfile> -f <filter> -l <logfile>"
            sys.exit(2)
        for opt, arg in opts:
            if opt in ("-i", "--input"):
                self.inputfile = arg
            elif opt in ("-o", "--output"):
                self.outputfile = arg
            elif opt in ("-f", "--filter"):
                self.filterfile = arg
            elif opt in ("-l", "--log"):
                self.logfile = arg

        print "input file is", self.inputfile
        print "output file is", self.outputfile
        print "filter file is", self.filterfile
        print "log file is", self.logfile

    def getFilterData(self):
        if not os.path.exists(self.filterfile):
            return False
        ff = open(self.filterfile, "r")
        #todo: valid check
        self.fstarttime = float(ff.readline())
        self.fendtime = float(ff.readline())
        ff.close()

        print "start:{0}, end: {1}".format(self.fstarttime, self.fendtime)
        return True

    def IsUsable(self):
        # check filter file
        if not self.getFilterData():
            print "[error] filter file({0}) is not exist.".format(self.filterfile)
            return False
        return os.path.exists(self.inputfile)

    def isTarget(self, start, gps_time):
        result = False
        if not start:
            if self.fstarttime <= gps_time:
                result = True
        else:   # already start
            if self.fendtime >= gps_time:
                result = True
        return result

    def calcPoint(self, point, scale, offset):
        return (point * scale + offset)

    def func1(self, val1, val2):
        return (10, 10, 10)

    def Run(self):
        #file Copy
        print "File Copy"
        try:
            shutil.copyfile(self.inputfile, self.outputfile)
        except (IOError, os.error) as why:
            print "src:{0}->dst:{1} error ({2})".format(self.inputfile, self.outputfile, str(why))

        if not os.path.exists(self.outputfile):
            return False

        # file read, write obj
        lasfile = laspy.file.File(self.outputfile, mode='rw') # for read/write(modify file)
        lfile = open(self.logfile, 'w')
        modify_start = False
        modify_end = False

        hdr = lasfile.header

        # loop
        print "start loop"
        #for i, data in enumerate(lasfile.points):
        for data in lasfile.points:

            # filter find
            gps_time = data['point']['gps_time']
            find = self.isTarget(modify_start, gps_time)
            if find:
                if not modify_start:
                    modify_start = True
                    print "[Find start point]"
                    print data['point']

                #get original data(for log)
                cur_point = data['point']
                ori_point = (self.calcPoint(cur_point['X'], hdr.scale[0], hdr.offset[0]),
                             self.calcPoint(cur_point['Y'], hdr.scale[1], hdr.offset[1]),
                             self.calcPoint(cur_point['Z'], hdr.scale[2], hdr.offset[2]))

                #todo.
                val1 = (1, 2, 3)
                val2 = (3, 2, 1)
                modv = self.func1(val1, val2)

                # reset X, Y, Z
                data['point']['X'] = (ori_point[0] + modv[0] - hdr.offset[0]) / hdr.scale[0]
                data['point']['Y'] = (ori_point[1] + modv[1] - hdr.offset[1]) / hdr.scale[1]
                data['point']['Z'] = (ori_point[2] + modv[2] - hdr.offset[2]) / hdr.scale[2]

                # logging start
                ldata = "[{0}] ({1},{2},{3}) -> ({4},{5},{6})\n".format(data['point']['gps_time'],
                                                                        ori_point[0],
                                                                        ori_point[1],
                                                                        ori_point[2],
                                                                        self.calcPoint(cur_point['X'], hdr.scale[0], hdr.offset[0]),
                                                                        self.calcPoint(cur_point['Y'], hdr.scale[1], hdr.offset[1]),
                                                                        self.calcPoint(cur_point['Z'], hdr.scale[2], hdr.offset[2]))
                lfile.write(ldata)
                #logging end
            else: # not find
                if (modify_start) and (not modify_end):
                    modify_end = True
                    print "[Find end point]"
                    print data['point']


        lasfile.close()
        lfile.close()

        print "Finish"
        return True

if __name__ == "__main__":
    print sys.argv[1:]
    tilas = TILAS(sys.argv[1:])
    if tilas.IsUsable():
        tilas.Run()

