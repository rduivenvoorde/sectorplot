from npp import NppSet
import time

t0 = time.time()

infn = r'data/tabel-npp-export.txt'
npps = NppSet(infn)

print(npps)
print(len(npps))
print(npps[0])
print(npps[0]['inventory'])
# TODO
print(npps[0].keys())
print(npps[0].values())


print('Tijd: %f sec' % (time.time() - t0))
