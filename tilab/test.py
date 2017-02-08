import laspy

class TILAS:
    def __init__(self):
        self.findIndex = [0, 4982980, 5468051, 6876499, 7498705, 8367447, 8981569, 10364437, 10570691, 12288331, 15000000]
        self.AlgoOffset = [ [4982979, 0.47, 0.69, -0.3, 0, 0, 0],
                            [485071, 0.39, 0.68, -0.33, 0.47, 0.69, -0.3], 
                            [1408448, 0.38, 0.46, -0.4, 0.39, 0.68, -0.33],
                            [622206, 0.34, 0.45, -0.42, 0.38, 0.46, -0.4],
                            [868742, 0.35, 0.38, -0.45, 0.34, 0.45, -0.42],
                            [614122, 0.38, 0.31, -0.46, 0.35, 0.38, -0.45],
                            [1382868, -1.97, 15.23, -7.48, 0.38, 0.31, -0.46],
                            [206254, 0.43, 0.24, -0.5, -1.97, 15.23, -7.48],
                            [1717640, 0.65, 0.29, -0.57, 0.43, 0.24, -0.5],
                            [2711670, 0, 0, 0, 0.65, 0.29, -0.57]]
        self.AlgoCount = 5
        self.k = 0
    
    def calcPoint(self, point, scale, offset):
        return round((point * scale + offset),2)

    def func1(self, index, oridata):
        
        if self.findIndex[self.AlgoCount + 1] < index :
            print "[func1] change interval (index: %d)" % (index)
            print self.AlgoOffset[self.AlgoCount + 1][1:7]
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

    def Run(self):
        f = laspy.file.File("test_modi2.las", mode="rw")
        logf = open("testt.log","w")
        hdr = f.header
        #loop
        for i, data in enumerate(f.points[self.findIndex[6]:self.findIndex[-1]]):
            cur_point = data['point']
            ori_point = (self.calcPoint(cur_point['X'], hdr.scale[0], hdr.offset[0]),
                            self.calcPoint(cur_point['Y'], hdr.scale[1], hdr.offset[1]),
                            self.calcPoint(cur_point['Z'], hdr.scale[2], hdr.offset[2]))

            modv = self.func1(i + self.findIndex[6], ori_point)

            data['point']['X'] = (modv[0] - hdr.offset[0]) / hdr.scale[0]
            data['point']['Y'] = (modv[1] - hdr.offset[1]) / hdr.scale[1]
            data['point']['Z'] = (modv[2] - hdr.offset[2]) / hdr.scale[2]

            # logging start
            """
            ldata = "[{0}] ({1},{2},{3}) -> ({4},{5},{6})\n".format(data['point']['gps_time'],
                                                                    ori_point[0],
                                                                    ori_point[1],
                                                                    ori_point[2],
                                                                    self.calcPoint(cur_point['X'], hdr.scale[0], hdr.offset[0]),
                                                                    self.calcPoint(cur_point['Y'], hdr.scale[1], hdr.offset[1]),
                                                                    self.calcPoint(cur_point['Z'], hdr.scale[2], hdr.offset[2]))
            """
            ldata = "%.2f  %.2f  %.2f\n" % (self.calcPoint(cur_point['X'], hdr.scale[0], hdr.offset[0]), self.calcPoint(cur_point['Y'], hdr.scale[1], hdr.offset[1]), self.calcPoint(cur_point['Z'], hdr.scale[2], hdr.offset[2]))
            logf.write(ldata)
                
        f.close()
        logf.close()


if __name__ == "__main__":
    a = TILAS()
    a.Run()

