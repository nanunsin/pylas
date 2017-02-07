"""
to use LAS library
 cmd> "pip install laspy"

""" 
import laspy
import sys, getopt
import os, shutil

class FilterReader:
    def __init__(self, filename):
        self.filename = filename
        self.fstarttime = 0.0
        self.fendtime = 0.0
        self.fdata = []

    def readfile(self):
        ff = open(self.filename, "r")
        times = ff.readline().split(" ")
        #time
        self.fstarttime = float(times[0])
        self.fendtime = float(times[1])
        #points
        readdata = ff.readline()
        while( readdata != '' ):
            points = readdata.strip('\n').split("\t")
            if len(points) != 6:
                print "invalid filter file"
                return False
            self.fdata.append(self.getData(points))
            readdata = ff.readline()
        ff.close()

        print len(self.fdata)
        return True

    def getData(self, points):
        retdata = []
        for point in points:
            retdata.append(round(float(point),2))
        return retdata
        
    def getFilterData(self):
        return self.fdata

    def getTimeInfo(self):
        return (self.fstarttime, self.fendtime)

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
        # listup
        self.findIndex = []
        self.AlgoOffset = []
        self.AlgoCount = 0

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
        
        self.filterReader = FilterReader(self.filterfile)
        if not self.filterReader.readfile():
            print "Filter file is invaild file"
            return False
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
        return round((point * scale + offset),2)

    def func1(self, index, oridata):
        if self.findIndex[self.AlgoCount] < index :
            self.AlgoCount += 1
        k = self.findIndex[self.AlgoCount] - index + 1
        num = self.AlgoOffset[self.AlgoCount][0]
        delta_xyz = self.AlgoOffset[self.AlgoCount][1:4]
        shift_xyz = self.AlgoOffset[self.AlgoCount][4:7]

        ret_x = oridata[0] + shift_xyz[0] + ((delta_xyz[0] - shift_xyz[0])/num) *k
        ret_y = oridata[1] + shift_xyz[1] + ((delta_xyz[1] - shift_xyz[1])/num) *k
        ret_z = oridata[2] + shift_xyz[2] + ((delta_xyz[2] - shift_xyz[2])/num) *k

        return (ret_x, ret_y, ret_z)

    def Search(self):
        # file read, write obj
        lasfile = laspy.file.File(self.inputfile, mode='r') # for read/write(modify file)
        # set time
        self.fstarttime, self.fendtime = self.filterReader.getTimeInfo()

        modify_start = False
        modify_end = False

        hdr = lasfile.header

        # loop
        print "start loop"
        logic_count = 0
        for i, data in enumerate(lasfile.points):
        #for data in lasfile.points:
            # filter find
            gps_time = data['point']['gps_time']
            find = self.isTarget(modify_start, gps_time)

            if find:
                if not modify_start:
                    modify_start = True
                    self.findIndex.append(i)
                    print "[Find start point]"
                    cur_point = data['point']
                    ori_point = (self.calcPoint(cur_point['X'], hdr.scale[0], hdr.offset[0]),
                                 self.calcPoint(cur_point['Y'], hdr.scale[1], hdr.offset[1]),
                                 self.calcPoint(cur_point['Z'], hdr.scale[2], hdr.offset[2]))
                    print "find! (%d)[%f, %f, %f]" %(i, ori_point[0], ori_point[1], ori_point[2])

                #get original data(for log)
                cur_point = data['point']
                
                ori_point = (self.calcPoint(cur_point['X'], hdr.scale[0], hdr.offset[0]),
                             self.calcPoint(cur_point['Y'], hdr.scale[1], hdr.offset[1]),
                             self.calcPoint(cur_point['Z'], hdr.scale[2], hdr.offset[2]))

                if logic_count < len(self.filterReader.fdata):
                    logic = self.filterReader.fdata[logic_count]
                
                if ori_point[0] == logic[0] and ori_point[1] == logic[1] and ori_point[2] == logic[2]:
                #if ori_point[0] == logic[0] and ori_point[1] == logic[1]:
                    print "find! (%d)[%f, %f, %f]" %(i+1, ori_point[0], ori_point[1], ori_point[2])
                    logic_count += 1
                    self.findIndex.append(i+1)

            else: # not find
                if (modify_start) and (not modify_end):
                    modify_end = True
                    self.findIndex.append(i)
                    print "[Find end point]"
                    cur_point = data['point']
                    ori_point = (self.calcPoint(cur_point['X'], hdr.scale[0], hdr.offset[0]),
                                 self.calcPoint(cur_point['Y'], hdr.scale[1], hdr.offset[1]),
                                 self.calcPoint(cur_point['Z'], hdr.scale[2], hdr.offset[2]))
                    print "find! (%d)[%f, %f, %f]" %(i, ori_point[0], ori_point[1], ori_point[2])

        lasfile.close()

        print "[search] %d" % len(self.findIndex)
        
        print "Finish"
        return True

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

    def makeAlgorithm(self):
        if len(self.findIndex) != len(self.filterReader.fdata) + 2:
            print "error( %d != %d )" % (len(self.findIndex), len(self.filterReader.fdata)+2)
            return
        print "[offset]"
        shift_xyz = [0, 0, 0]
        logic_count = len(self.findIndex)   # points
        for i in range(0, logic_count-1):   # interval count
            if i == logic_count - 2: # last interval
                delta_xyz = [0, 0, 0]
            else:
                filterdata = self.filterReader.fdata[i] # filter datas
                delta_x = round(filterdata[3] - filterdata[0], 2)   # calc X
                delta_y = round(filterdata[4] - filterdata[1], 2)   # calc Y
                delta_z = round(filterdata[5] - filterdata[2], 2)   # calc Z
                delta_xyz = [delta_x, delta_y, delta_z]
            
            num = self.findIndex[i+1] - self.findIndex[i]   #point : 11 
            
            offset = [num] + delta_xyz + shift_xyz
            self.AlgoOffset.append(offset)

            print offset

            shift_xyz = delta_xyz
        print self.AlgoOffset
    
    def Run2(self):
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
        
        hdr = lasfile.header

        # loop
        print "start loop"
        #for i, data in enumerate(lasfile.points):
        for i, data in enumerate(lasfile.points[self.findIndex[0]:self.findIndex[-1]]):
            cur_point = data['point']
            ori_point = (self.calcPoint(cur_point['X'], hdr.scale[0], hdr.offset[0]),
                         self.calcPoint(cur_point['Y'], hdr.scale[1], hdr.offset[1]),
                         self.calcPoint(cur_point['Z'], hdr.scale[2], hdr.offset[2]))

            #todo.
            point = (ori_point[0], ori_point[1], ori_point[2])
            modv = self.func1(i, point)

            # reset X, Y, Z
            data['point']['X'] = (modv[0] - hdr.offset[0]) / hdr.scale[0]
            data['point']['Y'] = (modv[1] - hdr.offset[1]) / hdr.scale[1]
            data['point']['Z'] = (modv[2] - hdr.offset[2]) / hdr.scale[2]

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
        lasfile.close()
        lfile.close()

        print "Finish"
        return True

if __name__ == "__main__":
    print sys.argv[1:]
    tilas = TILAS(sys.argv[1:])
    if tilas.IsUsable():
        tilas.Search()
        tilas.makeAlgorithm()
        tilas.Run2()

