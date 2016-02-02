# 5	       10       30
# 40a00000 41200000 41f00000

# 2        4        6
# 40000000 40800000 40c00000

# 2        100      0
# 40000000 42c80000 00000000

# https://en.wikipedia.org/w/index.php?title=Single-precision_floating-point_format&section=5#Converting_from_single-precision_binary_to_decimal

import math

def test():

    #s = '40a00000'  # 5
    #s = '41c80000' # 25
    # 1000 0001 0100 0000 0000 0000 0000 000
    s = '41f00000'  # 30
    s = '40c00000'  # 6

    f = format(int(s, 16), '032b')
    print f
    print len(f)

    # sign part
    s = f[0:1]
    print "sign bit: 0b%s" % s
    ss = math.pow(-1, int(s, 2))
    print ss

    # exponent part
    x = f[1:9]
    print "exponent bin: 0b%s" % x
    print "exponent dec: %s" % int(x, 2)
    exp = int(x, 2) - 127
    print "exp - 127   : %s" % exp
    xx = math.pow(2, (int(x, 2) - 127))
    print xx

    # significand part
    m = f[9:]
    print "significand bin: 0b%s" % m
    iplus24b = '1' + m
    print "sign plus 1 bin: 0b%s" % iplus24b
    mm = (1 + int(m, 2)*math.pow(2, -23))
    print mm

    # https://en.wikipedia.org/w/index.php?title=Single-precision_floating-point_format&section=5#Converting_from_single-precision_binary_to_decimal
    # s = sign bit
    # x = exponent
    # m = significand
    # n = (-1)^s   x  (1+m*2^-23)  x 2^x-127
    print ss * xx * mm

# spfb2dec = single point float binary to decimal
def spfb2dec(hex8):
    if hex8 == '00000000':
        # kweenie waarom maar de nul gaat niet goed... wordt 5.877471754111438e-39
        return float(0)
    else:
        b = format(int(hex8, 16), '032b')
        return math.pow(-1, int(b[0:1], 2)) * math.pow(2, (int(b[1:9], 2) - 127)) * (1 + int(b[9:], 2)*math.pow(2, -23))

# bytea2dec = bytearray to decimal
def bytea2dec(hex24):
    return [spfb2dec(hex24[:8]), spfb2dec(hex24[8:16]), spfb2dec(hex24[16:])]


#test()

print spfb2dec('40a00000')  # 5
print spfb2dec('41c80000') # 25
print spfb2dec('41f00000')  # 30
print spfb2dec('40c00000')  # 6

# 5	       10       30
# 40a00000 41200000 41f00000
print bytea2dec('40a000004120000041f00000')

# 2        100      0
# 40000000 42c80000 00000000
print bytea2dec('4000000042c8000000000000')

# 2        4        6
# 40000000 40800000 40c00000
print bytea2dec('400000004080000040c00000')


