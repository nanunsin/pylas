import sys
import getopt
import laspy
import os

def progressBar(value, endvalue, bar_length=20):
    percent = float(value) / endvalue
    arrow = '-' * int(round(percent * bar_length)-1) + '>'
    spaces = ' ' * (bar_length - len(arrow))

    sys.stdout.write("\rPercent: [{0}] {1}%".format(arrow + spaces, int(round(percent * 100))))
    sys.stdout.flush()

def main():
    lasfile = ''
    txtfile = ''
    rawformat = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:o:", ["input=","output=","raw="])
    except getopt.GetoptError:
        print "las.py -i <las file> -o <txt file> [--raw]"
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-i", "--input"):
            lasfile = arg
        elif opt in ("-o", "--output"):
            txtfile = arg
        elif opt in "--raw":
            rawformat = True
        else:
            print 'unknown option:', opt, arg
    # Check las file
    if not os.path.exists(lasfile):
        print lasfile + " is not found."
        sys.exit(2)

    if not txtfile:
        txtfile = os.path.splitext(lasfile)[0] + ".txt"

    #las file open
    lasf = laspy.file.File(lasfile, mode="r")
    hdr = lasf.header

    scales = hdr.scale
    offsets = hdr.offset
    num_of_points = len(lasf.points)

    #txt file
    txtf = open(txtfile, mode="w")

    txtf.write("[Header Info]\n")
    txtf.write("[scale]\n{0},{1},{2}\n".format(scales[0], scales[1], scales[2]))
    txtf.write("[offset]\n{0},{1},{2}\n".format(offsets[0], offsets[1], offsets[2]))
    txtf.write("[Points]\n")

    for i, data in enumerate(lasf.points):
        progressBar(i, num_of_points)
        gpstime = data['point']['gps_time']
        point_x = (data['point']['X'] * scales[0]) + offsets[0]
        point_y = (data['point']['Y'] * scales[1]) + offsets[1]
        point_z = (data['point']['Z'] * scales[2]) + offsets[2]
        if not rawformat:
            txtf.write("{0}|{1}|{2}|{3}\n".format(gpstime, point_x, point_y, point_z))
        else:
            txtf.write("{0}|{1}|{2}|{3}|{4}|{5}|{6}\n".format(gpstime, data['point']['X'], data['point']['Y'], data['point']['Z'], point_x, point_y, point_z))

    txtf.close()
    lasf.close()


if __name__ == "__main__":
    main()