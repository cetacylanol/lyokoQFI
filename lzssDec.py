import os
from tkinter import filedialog as fd
import tempfile
#Decompresses code lyoko: quest for infinity wii .pc and .GCN files
#the actual LZSS algo was taken from a quickBMS script


def readUlong(fileN):
    num = fileN.read(4)
    return int(bytes.hex(num), 16)
def readUByte(fileN):
    num = fileN.read(1)
    return int(bytes.hex(num), 16)

def decompLzssPcGCN():
    try:
        ft = ''
        #open tin file, loops until valid file extention. Doesn't check contents and the file needs to be unpacked.
        while (not(ft == 'pc' or ft == 'GCN')):
            fileName = fd.askopenfilename(title='open .TIN file', initialdir=os.getcwd())
            fn, ft = fileName.split('.')

    except ValueError:
        print('you quit :(')
        raise SystemExit()

    #get compressed size, decompressed size and the data from a .pc file
    with open(fileName, 'rb') as f_comp:
        #size of compressed data
        c_size = readUlong(f_comp)
        #size of uncompressed data
        dc_size = readUlong(f_comp)

        t_bytes = f_comp.read()
        
    with tempfile.TemporaryFile() as temp_comp:
        temp_comp.write(t_bytes)
        temp_comp.seek(0)

        with tempfile.TemporaryFile() as t_dec:
            with tempfile.TemporaryFile() as stor:
                ei = 12
                ej = 4
                p = 2
                rless = p
                
                n = 1
                n = n << ei
                f = 1
                f = f << ej
                
                #make the storage file size n filled with zeroes (hopefully)
                stor.truncate(n)

                r = n
                r -= f
                r -= rless
                n -= 1
                f -= 1

                srcend = c_size
                dstend = dc_size

                flags = 0x00
                while (temp_comp.tell() < srcend):
                    if (not (flags & 0x100)):
                        flags = readUByte(temp_comp)
                        flags = flags | 0xff00
                    if (flags & 1):
                        c = temp_comp.read(1)
                        t_dec.write(c)
                        stor.seek(r)
                        stor.write(c)
                        r += 1
                        r = r & n
                    else:
                        i = readUByte(temp_comp)
                        j = readUByte(temp_comp)
                        tmp = j
                        tmp = tmp >> ej
                        tmp = tmp << 8
                        i = i | tmp
                        j = j & f
                        j += p
                        for k in range(j + 1):
                            tmp = i
                            tmp += k
                            tmp = tmp & n
                            stor.seek(tmp)
                            c = stor.read(1)
                            t_dec.write(c)
                            stor.seek(r)
                            stor.write(c)
                            r += 1
                            r = r & n
                    flags = flags >> 1
            
            if (ft == 'pc'):
                out_name = fn[:-3] + '.' + fn[-3:]
            else:
                out_name = fn + '.mwld'

            with open(out_name, 'wb') as out_file:
                t_dec.seek(0)
                out_file.write(t_dec.read())



def main():
    decompLzssPcGCN()



if __name__ == "__main__":
    main()