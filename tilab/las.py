# -*- coding: utf-8 -*-
"""
to use LAS library
 cmd> "pip install laspy"

""" 
import laspy
import sys, getopt
import os, shutil

class TILogger:
    def __init__(self):
        self.use = False
        self.index = 0
        self.wcount = 10000
        self.interval = 10000
        self.lastlog = ''
        self.logf = None
        self.fileindex = 0

    def SetFileName(self, filename):
        if filename:
            self.basename, self.extname = os.path.splitext(filename)
            self.use = True
    
    def SetInterval(self, interval):
        if interval > 0 :
            self.interval = interval
            self.wcount = interval
    
    def Write(self, data):
        if self.use :
            self.lastlog = data
            if 0 == self.index:
                filename = "%s(%d)%s"%(self.basename, self.fileindex, self.extname)
                self.fileindex += 1
                self.logf = open(filename, "w")
            #endif
            if self.interval == self.wcount:
                
                self.logf.write(data)
                self.index += 1
                self.lastlog = ''

                if self.index > 1000000:
                    self.index = 0
                    self.logf.close()
            
            if self.wcount > 1:
                self.wcount -= 1
            else:
                self.wcount = self.interval

    def Close(self):
        if self.fileindex > 0 and self.use :
            if self.lastlog:
                self.logf.write(self.lastlog)
            self.logf.close()
            self.use = False

    def __del__(self):
        self.Close()

# Filter 파일에 있는 내용을 저장한다
class FilterReader:
    def __init__(self, filename):
        self.filename = filename
        self.fstarttime = 0.0
        self.fendtime = 0.0
        self.fdata = []
    
    # 파일을 읽어서 시작시간, 마지막시간, 보정된 좌표를 저장한다.
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

    # 저장된 시작 시간과 마지막 시간을 얻는다
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
        
        # listup
        self.findIndex = []
        self.AlgoOffset = []
        self.AlgoCount = 0
        
        # logger
        self.logger = TILogger()
        self.loginterval = 0

        # Algorithm
        self.k = 0

        # Set member var
        self.parseArgs(argv)

    # 파라미터를 파싱한다
    def parseArgs(self, argv):
        try:
            opts, args = getopt.getopt(argv, "i:o:f:l:", ["input=","output=","filter=","log=","interval="])
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
            elif opt == "--interval":
                self.loginterval = int(arg)

        print "input file is", self.inputfile
        print "output file is", self.outputfile
        print "filter file is", self.filterfile
        print "log file is %s(%d)" % (self.logfile, self.loginterval)

    def getFilterData(self):
        if not os.path.exists(self.filterfile):
            return False
        
        self.filterReader = FilterReader(self.filterfile)
        if not self.filterReader.readfile():
            print "Filter file is invaild file"
            return False
        return True
    
    # 동작에 필요한 요건들을 확인하여, 정상인 경우 True를 반환한다.
    def IsUsable(self):
        # check filter file
        if not self.getFilterData():
            print "[error] filter file({0}) is not exist.".format(self.filterfile)
            return False
        return os.path.exists(self.inputfile)

    # 시간 정보로 변경해야하는 좌표인지 확인한다
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

    # 각 좌표에 미리 생성한 [num, delta_xyz, shift_xyz] 을 이용하여 
    # 이 함수 호출전에 makeAlgorithm() 함수가 호출되어야 한다
    def func1(self, index, oridata):
        
        if self.findIndex[self.AlgoCount + 1] < index :
            print "[func1] change interval (index: %d)" % (index)
            self.AlgoCount += 1
            self.k = 0

        self.k += 1
        num = self.AlgoOffset[self.AlgoCount][0]
        delta_xyz = self.AlgoOffset[self.AlgoCount][1:4]
        shift_xyz = self.AlgoOffset[self.AlgoCount][4:7]

        ret_x = oridata[0] + shift_xyz[0] + ((delta_xyz[0] - shift_xyz[0])/num) * self.k
        ret_y = oridata[1] + shift_xyz[1] + ((delta_xyz[1] - shift_xyz[1])/num) * self.k
        ret_z = oridata[2] + shift_xyz[2] + ((delta_xyz[2] - shift_xyz[2])/num) * self.k

        return (ret_x, ret_y, ret_z)

    # 시작시간, 마지막 시간, 각 좌표의 정보로 index를 찾는다.
    def Search(self):
        # file read, write obj
        lasfile = laspy.file.File(self.inputfile, mode='r') # for read/write(modify file)
        # set time
        self.fstarttime, self.fendtime = self.filterReader.getTimeInfo()

        modify_start = False
        modify_end = False

        hdr = lasfile.header

        # loop
        print "[Search] start loop"
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
                    cur_point = data['point']
                    ori_point = (self.calcPoint(cur_point['X'], hdr.scale[0], hdr.offset[0]),
                                 self.calcPoint(cur_point['Y'], hdr.scale[1], hdr.offset[1]),
                                 self.calcPoint(cur_point['Z'], hdr.scale[2], hdr.offset[2]))
                    print "find! (%d) [%.3f, %.3f, %.3f]" %(i, ori_point[0], ori_point[1], ori_point[2])

                #get original data(for log)
                cur_point = data['point']

                ori_point = (self.calcPoint(cur_point['X'], hdr.scale[0], hdr.offset[0]),
                             self.calcPoint(cur_point['Y'], hdr.scale[1], hdr.offset[1]),
                             self.calcPoint(cur_point['Z'], hdr.scale[2], hdr.offset[2]))

                if logic_count < len(self.filterReader.fdata):
                    logic = self.filterReader.fdata[logic_count]

                if ori_point[0] == logic[0] and ori_point[1] == logic[1] and ori_point[2] == logic[2]:
                #if ori_point[0] == logic[0] and ori_point[1] == logic[1]:
                    print "find! (%d) [%.3f, %.3f, %.3f]" %(i+1, ori_point[0], ori_point[1], ori_point[2])
                    logic_count += 1
                    self.findIndex.append(i)

            else: # not find
                if (modify_start) and (not modify_end):
                    modify_end = True
                    self.findIndex.append(i)
                    cur_point = data['point']
                    ori_point = (self.calcPoint(cur_point['X'], hdr.scale[0], hdr.offset[0]),
                                 self.calcPoint(cur_point['Y'], hdr.scale[1], hdr.offset[1]),
                                 self.calcPoint(cur_point['Z'], hdr.scale[2], hdr.offset[2]))
                    print "find! (%d) [%.3f, %.3f, %.3f]" %(i, ori_point[0], ori_point[1], ori_point[2])
                    break

        print "[Search] end loop"
        lasfile.close()

        print "search Finish"
        return True

    # num, delta_xyz, shift_xyz 를 생성한다
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

            num = self.findIndex[i+1] - self.findIndex[i]   #points

            offset = [num] + delta_xyz + shift_xyz
            self.AlgoOffset.append(offset)

            print offset

            shift_xyz = delta_xyz

        if len(self.AlgoOffset)+1 != len(self.findIndex):
            print "makeAlgorithm error(len)"
            return False
        return True

    # 알고리즘으로 뽑은 데이터를 적용한다.
    def Run(self):
        #file Copy
        print "[Run]File Copy"
        try:
            shutil.copyfile(self.inputfile, self.outputfile)
        except (IOError, os.error) as why:
            print "src:{0}->dst:{1} error ({2})".format(self.inputfile, self.outputfile, str(why))

        if not os.path.exists(self.outputfile):
            return False

        # file read, write obj
        lasfile = laspy.file.File(self.outputfile, mode='rw') # for read/write(modify file)
        logger = TILogger()
        logger.SetFileName(self.logfile)
        logger.SetInterval(self.loginterval)

        hdr = lasfile.header

        # loop
        print "[Run] start loop (%.3f - %.3f)" % (lasfile.gps_time[self.findIndex[0]], lasfile.gps_time[self.findIndex[-1]])
        # Search 함수를 통하여 찾은 Target만 수행한다
        for i, data in enumerate(lasfile.points[self.findIndex[0]:self.findIndex[-1]]):
            cur_point = data['point']
            ori_point = (self.calcPoint(cur_point['X'], hdr.scale[0], hdr.offset[0]),
                         self.calcPoint(cur_point['Y'], hdr.scale[1], hdr.offset[1]),
                         self.calcPoint(cur_point['Z'], hdr.scale[2], hdr.offset[2]))

            point = (ori_point[0], ori_point[1], ori_point[2])  # 원래 좌표
            modv = self.func1(i + self.findIndex[0], point)     # 새로 받은 좌표

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
            logger.Write(ldata)
            #logging end
        print "[Run] end loop"
        lasfile.close()
        logger.Close()

        print "Finish"
        return True       

if __name__ == "__main__":
    print sys.argv[1:]
    tilas = TILAS(sys.argv[1:])
    if tilas.IsUsable():
        tilas.Search()
        if not tilas.makeAlgorithm():
            print "makeAlgorithm() failed"
        else:
            tilas.Run()

