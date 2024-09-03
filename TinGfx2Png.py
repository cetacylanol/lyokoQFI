from PIL import Image
import re
import os
from tkinter import filedialog as fd

#takes as input tin and gfx file, outputs images
#need to make a tool to decompress files
def readUlong(fileN):
    num = fileN.read(4)
    return int(bytes.hex(num), 16)

def readUshort(fileN):
    num = fileN.read(2)
    print(num)

#convert a 2 byte hex string from RGB565 colour space to RGB
def rgb565_to_rgb(in565):
    bin_conv = ''
    
    #convert the 2 bytes to binary
    for byte_section in in565:
        byte_section = int(byte_section, 16)
        bin_conv += "{0:04b}".format(byte_section) #keep leading 0s

    #make sure the binary sequence has 16 bits
    bin_conv = "{0:<016}".format(bin_conv)

    #this isn't very accurate in terms of colour space!
    #change if this actually starts geting images
    red = int(bin_conv[0: 5], 2) * 8
    green = int(bin_conv[5: 11], 2) * 4
    blue = int(bin_conv[11: 16], 2) * 8

    return red, green, blue

#convert a 64 byte 4x4 pixel block from rgba32 to rgba
#outputs a list of tuples representing colours
def rgba32_to_rgb(inrgba32, block_size = 4):
    #init pixel list
    #each pixel is a 4 item list
    empty_px = [0,0,0,0]
    px_colours_temp = [[0,0,0,0], [0,0,0,0], [0,0,0,0], [0,0,0,0], 
                        [0,0,0,0], [0,0,0,0], [0,0,0,0], [0,0,0,0], 
                        [0,0,0,0], [0,0,0,0], [0,0,0,0], [0,0,0,0], 
                        [0,0,0,0], [0,0,0,0], [0,0,0,0], [0,0,0,0]]
    alpha = True
    green = True
    px_iter = 0
    #convert 64 bytes input to list of individual bytes
    px_vals =  re.findall('..', bytes.hex(inrgba32))

    for i in range(64):
        if(px_iter == 16):
            px_iter = 0
        if(i < 32):
            
            if(alpha):
                #alpha
                px_colours_temp[px_iter][3] = int(px_vals[i], 16)
            else:
                #red
                px_colours_temp[px_iter][0] = int(px_vals[i], 16)
                px_iter += 1
            alpha = not alpha
        else:
            if(green):
                #green
                px_colours_temp[px_iter][1] = int(px_vals[i], 16)
            else:
                #blue
                px_colours_temp[px_iter][2] = int(px_vals[i], 16)
                px_iter += 1
            green = not green

    px_colours = [(0,0,0,0)] * (block_size * block_size)
    px_iter = 0
    for px_col in px_colours_temp:
        px_colours[px_iter] = (px_col[0], px_col[1], px_col[2], px_col[3])
        px_iter += 1

    return px_colours

def draw_rgba32_block_image(bin_bytes, out_file, size, block_size = 4):  
    #block offsets
    bp_x = 0
    bp_y = 0
    #top left corner of current block
    px_x = 0
    px_y = 0
    #should x or y be incremented (for weird block placement patterns)

    img = Image.new('RGBA', (size, size * 2))

    #read 2 bytes at a time
    step = 64
    for i in range(0,len(bin_bytes), step):  
        chunk = bin_bytes[i: i + step]
        px_colours = rgba32_to_rgb(chunk)
        # draw all pixels in a block
        for x in range(block_size * block_size):

            img.putpixel((px_x * block_size + bp_x, px_y * block_size + bp_y), px_colours[x])
            
            #draw linear
            #increment block position + offset
            bp_x += 1
            if(bp_x == block_size):
                bp_x = 0
                bp_y += 1
                if(bp_y == block_size):
                    bp_y = 0               
                    px_x += 1
                    if(px_x * block_size == size):
                        px_x = 0
                        px_y += 1

    img.save(out_file)
    return img

def draw_sub_CMPR_image(bin_bytes, img, size, offset_x= 0, offset_y = 0, block_size = 4):
    #block offsets
    bp_x = 0
    bp_y = 0
    #top left corner of current block
    px_x = 0
    px_y = 0
    #should x or y be incremented (for weird block placement patterns)
    inc_x = False
    inc_y = False

    step = 8
    for i in range(0,len(bin_bytes), step):   
        chunk = bin_bytes[i: i + step]
        #format chunk
        chunk_temp = "{0:016}".format(bytes.hex(chunk))
        
        #get colours stored in first 4 bytes of chunk
        palette_temp = [chunk_temp[0:4], chunk_temp[4:8]]
        #get list of pixel palette indices
        #format is 32 bits, if the chunk is too short 0s are added at the end
        px_indices =  re.findall('..', "{0:032b}".format(int(chunk_temp[8:16], 16)))
        palette = [(0,0,0),(64,64,64),(128,128,128),(255,255,255)]

        #store colours to palette
        palette[0] = rgb565_to_rgb(palette_temp[0])
        palette[1] = rgb565_to_rgb(palette_temp[1])

        #fill remaining palette colours
        if(int(palette_temp[0], 16) > int(palette_temp[1], 16)):
            #new colour that is 2/3 palette[0], 1/3 palette[1]
            p_temp2 =   (int(palette[0][0] * 2/3 + palette[1][0] * 1/3),
                        int(palette[0][1] * 2/3 + palette[1][1] * 1/3), 
                        int(palette[0][2] * 2/3 + palette[1][2] * 1/3))
            #new colour that is 1/3 palette[0], 2/3 palette[1]
            p_temp3 =   (int(palette[0][0] * 1/3 + palette[1][0] * 2/3),
                        int(palette[0][1] * 1/3 + palette[1][1] * 2/3), 
                        int(palette[0][2] * 1/3 + palette[1][2] * 2/3))
            palette[2] = p_temp2
            palette[3] = p_temp3

        else:
            #new colour that is 1/2 palette[0], 1/2 palette[1]
            p_temp2 =   (int(palette[0][0] * 1/2 + palette[1][0] * 1/2),
                        int(palette[0][1] * 1/2 + palette[1][1] * 1/2), 
                        int(palette[0][2] * 1/2 + palette[1][2] * 1/2))
            palette[2] = p_temp2


        for x in range(block_size * block_size):
            img.putpixel((px_x * block_size + bp_x + offset_x, px_y * block_size + bp_y + offset_y), palette[int(px_indices[x], 2)])

            #draw in 4 block pattern
            #increment block position + offset
            bp_x += 1
            if(bp_x == block_size):
                bp_x = 0
                bp_y += 1
                if (bp_y == block_size):
                    bp_y = 0
                    #if at last block go to start
                    if(inc_x and inc_y and px_x * block_size == size - block_size):                    
                        px_x = 0
                        px_y += 1
                        inc_x = not inc_x
                        inc_y = not inc_y
                    elif(inc_x and inc_y ):
                        px_x += 1
                        px_y -= 1
                        inc_x = not inc_x
                        inc_y = not inc_y
                    elif(inc_x):
                        px_x -= 1
                        px_y += 1
                        inc_x = not inc_x
                        inc_y = not inc_y
                    elif(inc_y):
                        px_x += 1
                        inc_x = not inc_x
                    else:
                        px_x += 1
                        inc_x = not inc_x
    return img

#takes byte sequence, returns image
#bin_bytes = image bytes, out_file file to save to, size = image width, block_size = image block width in pixels 
def draw_CMPR_image(bin_bytes, out_file, size, alpha = False, block_size = 4):
    height = int(size * 1.5)

    img = Image.new('RGB', (size, height))
    tsize = size

    byte_offset = 0
    block_amt = int(size/block_size) 
    c_sz = block_amt * block_amt * 8 
    x_off = 0
    y_off = 0
    draw_sub_CMPR_image(bin_bytes[byte_offset: byte_offset + c_sz], img, tsize, x_off, y_off)
    byte_offset += c_sz
    y_off += tsize
    tsize = tsize//2
    c_sz = c_sz//4
    while(c_sz != 8): 
        img  = draw_sub_CMPR_image(bin_bytes[byte_offset: byte_offset + c_sz], img, tsize, x_off, y_off)
        byte_offset += c_sz
        x_off += tsize
        tsize = tsize//2
        c_sz = c_sz//4
    
    if(alpha):
        img2 = Image.new('RGB', (size, height))
        tsize = size
        c_sz = block_amt * block_amt * 8 
        x_off = 0
        y_off = 0
        draw_sub_CMPR_image(bin_bytes[byte_offset: byte_offset + c_sz], img2, tsize, x_off, y_off)
        byte_offset += c_sz
        y_off += tsize
        tsize = tsize//2
        c_sz = c_sz//4
        while(c_sz != 8): 
            img2  = draw_sub_CMPR_image(bin_bytes[byte_offset: byte_offset + c_sz], img2, tsize, x_off, y_off)
            byte_offset += c_sz
            x_off += tsize
            tsize = tsize//2
            c_sz = c_sz//4

        a = img2.getchannel('G')
        r, g, b = img.split()
        img = Image.merge('RGBA', (r,g,b,a))
        
    
    img.save(out_file)
    return img

def main():
    try:
        ft = ''
        #open tin file, loops until valid file extention. Doesn't check contents and the file needs to be unpacked.
        while (ft != 'tin'):
            fileName = fd.askopenfilename(title='open .TIN file', initialdir=os.getcwd())
            fn, ft = fileName.split('.')

    except ValueError:
        print('you quit :(')
        raise SystemExit()
    
    tInfos = []
    if (os.path.isfile(fn + '.gfx')):
        #number of textures
        txNum = 0
        b8ListNum = 0
        b16ListNum = 0
        #parse texture info
        with open(fileName, 'rb') as fTin:
            fTin.seek(8, 0)
            #number of indices in some unknown lists
            b8ListNum = readUlong(fTin)
            b16ListNum = readUlong(fTin)
            txNum = readUlong(fTin)
            sTo = b8ListNum * 8 + b16ListNum * 16
            #seek to start of textures info 
            fTin.seek(sTo + 12, 1)
   
            for i in range(txNum):
                tType = readUlong(fTin)
                sz = readUlong(fTin)
                pxWidth = readUlong(fTin)
                offset = readUlong(fTin)
                tInfos.append([tType,sz,pxWidth,offset])

        with open(fn + '.gfx', 'rb') as fGfx:
            for i, inf in enumerate(tInfos):                
                tx = fGfx.read(inf[1])
                txFn = fn + "tex" + "{0:>02}".format(i) + ".png"
                
                #check image flags to see how to interpret the data
                if (inf[0] == 1 ):
                    draw_CMPR_image(tx, txFn, inf[2])
                elif (inf[0] == 225 or inf[0] == 193 or inf[0] == 161):
                    draw_CMPR_image(tx, txFn, inf[2], alpha = True)
                elif (inf[0] == 101 ):
                    draw_rgba32_block_image(tx, txFn, inf[2])
                else:
                    print('Unsupported file type at pos ' + str(i))
                    print('File type ID: ' + str(inf[0]))
                
                if (inf[3] == 4294967295):
                    print('Weird file')
                    fGfx.seek(-inf[1], 1)
    else:
        print('There is no gfx in this folder sorry :(')




if __name__ == "__main__":
    main()