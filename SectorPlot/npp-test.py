from npp import NppSet
import time

t0 = time.time()

infn = r'data/tabel-npp-export.txt'
npps = NppSet(infn)

print(npps)
print(npps[0])
print(npps[0]['inventory'])

print('Tijd: %f sec' % (time.time() - t0))
