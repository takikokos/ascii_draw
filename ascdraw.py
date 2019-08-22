import cv2
import numpy as np
from tqdm import tqdm, trange # nice progress bar
from PIL import Image, ImageDraw, ImageFont # used to draw symbols and then calculate white/all ratio
from sys import argv as args


SYMBOLS_FNAME_0x00ffff = "letters_stat2.txt" # i used different files for experiments, sometimes it's better not to use many symbols (65535) but only 300
SYMBOLS_FNAME_300 = "letters_stat.txt" # these are files generated with create_symbols_pil
HEGIHT_CONST = 400 # image will be resized to this height, saving aspect ratio for width
FONT_PATH = "fonts/DejaVuSansMono.ttf"


def create_symbols_pil(char_range : (int, int), symb_fname : str, verbose=False):
    '''
        Creates table with covered area ratio calculated for 
        each symbol in char_range and writes it in symb_fname.
        Uses FONT_PATH for user defined font.

    '''
    with open(symb_fname, "w") as output:
        if verbose:
            my_range = trange
            print("preparing symbols")
        else:
            my_range = range

        for ch in my_range(*char_range):
            letter = chr(ch)
            # 25x40 found this empirically to fit the symbol in rectangle the best way
            width = 25
            height = 40
            back_ground_color = (0,0,0)
            font_size = 40
            font_color = (255,255,255)

            # draw letter
            im = Image.new("RGB", (width, height), back_ground_color)
            draw = ImageDraw.Draw(im)
            unicode_font = ImageFont.truetype(FONT_PATH, font_size)
            draw.text( (0,0), letter, font=unicode_font, fill=font_color )

            # count ratio
            img = np.array(im)
            a = img.reshape(img.size)
            unique, counts = np.unique(a, return_counts=True)
            res = dict(zip(unique, counts))

            # now res = { 0 : amount of black pixels * 3,
            #             255 : amount of white pixels * 3 }

            # uncomment to see what characters this function draws
            # if verbose:
            #     cv2.imshow('image', img)
            #     cv2.waitKey(0)
            #     cv2.destroyAllWindows 

            # tried to use mean value scaled to 0 - 0.45 (.45 is approximately maximum which i got before scaling)
            # output.write(f"{ch} {float(a.mean()) / (float(255) / 0.45)}\n")
            
            # write to file "area cover ratio" for each symbol, it's possible that res[255] doesn't exist so i subtract res[0]
            output.write(f"{ch} {((width*height*3) - res[0])/(width*height*3)}\n")

        if verbose:
            print("wrote to ", symb_fname)

def create_symbols(verbose=False, symb_fname=SYMBOLS_FNAME_0x00ffff):
    '''
        Almost the same as create_symbols_pil, but using
        cv2 only. I got some troubles with user's fonts, better use
        create_symbols_pil
    '''
    output = open(symb_fname, "w")
    if verbose:
        range = trange
        print("preparing symbols")

    for ch in range(32, 300):
        letter = chr(ch)
        img = np.zeros((40, 23, 3), np.uint8)
        font = cv2.FONT_HERSHEY_SIMPLEX

        # ft = cv2.freetype.createFreeType2()
        # ft.loadFontData(fontFileName='fonts/Ubuntu-R.ttf', id=0)
        try:
            cv2.putText(img, letter, (0, 30), font, 1, (255, 255, 255), 2)
            a = img.reshape(img.size)
            unique, counts = np.unique(a, return_counts=True)
            res = dict(zip(unique, counts))
            output.write(f"{ch} {((40*23*3) - res[0])/(40*23*3)}\n")
        except Exception as e:
            print("error at char ", ch)

    if verbose:
        print("wrote to ", symb_fname)

def get_sorted(symb_fname : str) -> list:
    '''
        Read calculated values for symbols from
        symb_fname, sort and return the array [(int, flaot), (int, float), ...]
    '''
    lines = open(symb_fname).readlines()
    arr = [(int(s.split()[0]), float(s.split()[1])) for s in lines]
    arr.sort(key=lambda x : x[1])
    return arr

def bin_search(arr, val):
    '''
        Find the closest to val in arr,
        returns ord of the best char
    '''
    piv = arr[len(arr)//2][1]
    if len(arr) == 1:
        return arr[0]
    if piv > val:
        return bin_search(arr[:len(arr)//2], val)
    else:
        return bin_search(arr[len(arr)//2:], val)

# i like this method more
def drawtxt_mean(imagename : str, filename : str, symb_fname : str = SYMBOLS_FNAME_300, resize=True):
    '''
        Creates ASCII DRAW for imagename in output file filename,
        uses symb_fname file to find the best char approximation.
        In my opinion 32-300 is the best range of chars for this method.

        - image is turned into greyscale, so max pixel value is 255
        - here i use mean/max scaled to .45 for best fit
        - resize is good not to create too big txt files
        - i guess you can use color from original image to make colored ascii draw
    '''
    letters = get_sorted(symb_fname)
    img = cv2.imread(imagename, cv2.IMREAD_GRAYSCALE)

    # resize to const
    if resize:
        new_width = int(img.shape[1] * (HEGIHT_CONST / img.shape[0])) # save aspect ratio
        img = cv2.resize(img, (new_width, HEGIHT_CONST), interpolation = cv2.INTER_AREA)

    width, height = 2, 4
    with open(filename, "w") as output:
        for i in tqdm(range(0, img.shape[0], height)):
            for j in range(0, img.shape[1], width):
                # get the rectangle which is gonna be replaced with the letter
                ch = img[i:i+height, j:j+width]
                a = ch.reshape(ch.size)

                # find the best char
                val = float(a.mean()) / (float(255) / 0.45)
                char = chr(bin_search(letters, val)[0])

                # don't like these chars, so just use '.'
                if ord(char) == 0x007f or ord(char) == 0x009f or ord(char) == 0x200F or ord(char) == 0x202E:
                    char = '.' 

                output.write(char)
            output.write("\n")

def drawtxt_rel(imagename : str, filename : str, symb_fname : str = SYMBOLS_FNAME_0x00ffff, resize=True):
    '''
        Creates ASCII DRAW for imagename in output file filename,
        uses symb_fname file to find the best char approximation.
        In my opinion 32-65535 is the best range of chars for this method.

        - image is turned into black and white, there are only 0, 255 in pixels values
        - here i use white/(black + white) ratio for best fit
        - resize is good not to create too big txt files
    '''
    letters = get_sorted(symb_fname)
    img = cv2.imread(imagename, cv2.IMREAD_GRAYSCALE)

    # resize to const
    if resize:
        new_width = int(img.shape[1] * (HEGIHT_CONST / img.shape[0])) # save aspect ratio
        img = cv2.resize(img, (new_width, HEGIHT_CONST), interpolation = cv2.INTER_AREA)

    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            # round grey to white or black
            if img[i, j] > 127:
                img[i, j] = 255
            else:
                img[i, j] = 0

    width, height = 2, 4
    with open(filename, "w") as output:
        for i in tqdm(range(0, img.shape[0], height)):
            for j in range(0, img.shape[1], width):
                # get the rectangle which is gonna be replaced with the letter
                ch = img[i:i+height, j:j+width]
                a = ch.reshape(ch.size)

                # count black and white pixels
                unique, counts = np.unique(a, return_counts=True)
                res = dict(zip(unique, counts))

                # here we count white/all ratio
                # if image was originally black and white it's better to change 
                # 255 to 0, to count black/all
                if 255 in res.keys():
                    rat = res[255]
                else:
                    rat = 0
                val = rat / (width*height)

                # find the best char
                if val == 0.0: # don't write invisible symbols
                    char = '.'
                else:
                    char = chr(bin_search(letters, val)[0])

                output.write(char)
            output.write("\n")

if __name__ == "__main__":
    if len(args) < 4 or args[1] == "-h":
        print("Use python3 ascdraw.py [image file] [output file] [mean or rel]\nExample:python3 ascdraw.py ./flower.jpg ./asci_flower.txt mean")
    else:
        if args[3] == "mean":
            drawtxt_mean(args[1], args[2])
        if args[3] == "rel":
            drawtxt_rel(args[1], args[2])
    
