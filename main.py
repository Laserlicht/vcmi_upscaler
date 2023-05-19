# License: GNU General Public License v2.0 or later

import os
import shutil
from pathlib import Path
import ffmpeg
import multiprocessing

from tools.lodextract.lodextract import unpack_lod
from tools.lodextract.defextract import extract_def
from tools.lodextract.makedef import makedef

SINGLE_CORE = True
CORES = 24
CREATE_DEF = False
ESREGAN = False

def main():
    for file in os.listdir("0_input"):
        filename = os.fsdecode(file)
        if not os.path.exists("1_extracted/" + filename) and filename.lower().endswith(".lod"):
            if not os.path.exists("1_extracted/" + filename): os.makedirs("1_extracted/" + filename, exist_ok=True)
            unpack_lod("0_input/" + filename, "1_extracted/" + filename)
            for file2 in os.listdir("1_extracted/" + filename):
                filename2 = os.fsdecode(file2)
                if filename2.lower().endswith(".def"):
                    if not os.path.exists("2_extracted/" + filename + "/" + filename2): os.makedirs("2_extracted/" + filename + "/" + filename2, exist_ok=True)
                    print("1_extracted/" + filename + "/" + filename2, "2_extracted/" + filename + "/" + filename2)
                    extract_def("1_extracted/" + filename + "/" + filename2, "2_extracted/" + filename + "/" + filename2)

    if SINGLE_CORE: #single core
        for a in list(os.walk("1_extracted")) + list(os.walk("2_extracted")):
            upscaletask(a)
    else: #multi core
        pool = multiprocessing.Pool(CORES)
        for result in pool.map(upscaletask, list(os.walk("1_extracted")) + list(os.walk("2_extracted"))):
            pass

    if CREATE_DEF: #some files are to big for def
        for root, _, files in list(os.walk("4_converted")):
            new_root = str(Path(root.replace("4_converted", "5_backconverted")).parents[0])
            if not os.path.exists(new_root): os.makedirs(new_root, exist_ok=True)
            for file in files:
                if file.lower().endswith(".json"):
                    if not os.path.exists(os.path.join(new_root, file.replace("json", "def"))):
                        makedef(os.path.join(root, file), new_root)


    if not os.path.exists("6_mod"): os.makedirs("6_mod", exist_ok=True)
    if not os.path.exists("6_mod/content/data"): os.makedirs("6_mod/content/data", exist_ok=True)
    if not os.path.exists("6_mod/content/sprites"): os.makedirs("6_mod/content/sprites", exist_ok=True)
    folders = list(os.walk("3_converted"))
    folders = sorted(folders, key=lambda x: x[0], reverse=True)
    for root, _, files in folders:
        for file in files:
            if file.lower().endswith(".png"):
                if os.path.exists(os.path.join("6_mod/content/data", file)): print("already existing!")
                shutil.copyfile(os.path.join(root, file), os.path.join("6_mod/content/data", file))
    folders = list(os.walk("4_converted"))
    folders = sorted(folders, key=lambda x: x[0], reverse=True)
    for root, _, files in folders:
        for file in files:
            if file.lower().endswith(".json"):
                shutil.copytree(root, "6_mod/content/sprites", dirs_exist_ok=True)
                with open(os.path.join("6_mod/content/sprites", file), "rt") as fin:
                    text = fin.read()
                with open(os.path.join("6_mod/content/sprites", file), "wt") as fout:
                    fout.write(text.replace('\\\\', '/'))
    

    with open("6_mod/mod.json", "w") as f:
        f.write('''
{	
	"name" : "HD textures",
	"description" : "HD textures",
	"version" : "1.0.0",
	"author" : "",
	"contact" : "",
	"modType" : "Other",
	"compatibility" :
	{
		"min" : "1.2.0"
	},
	"changelog" : 
	{ 
		"1.0.0" : [ "Initial" ]
	}
}
        '''.strip())


def upscaletask(f):
    root, _, files = f
    new_root = root.replace("1_extracted", "3_converted").replace("2_extracted", "4_converted")
    if not os.path.exists(new_root): os.makedirs(new_root, exist_ok=True)
    for file in files:
        if file.lower().endswith(".png"):
            if not os.path.exists(os.path.join(new_root, file)):
                if ESREGAN:
                    os.system(os.path.join('tools', 'realesrgan', 'realesrgan-ncnn-vulkan') + ' -i ' + os.path.join(root, file) + ' -o ' + os.path.join(new_root, file) + ' -n realesrgan-x4plus')
                else:
                    stream = ffmpeg.input(os.path.join(root, file), pix_fmt='rgba')
                    stream = ffmpeg.filter(stream, 'xbr', n=4)
                    if not "3_converted" in new_root:
                        stream_alpha = ffmpeg.input(os.path.join(root, file), pix_fmt='rgba')
                        stream_alpha = ffmpeg.filter(stream_alpha, 'alphaextract')
                        stream_alpha = ffmpeg.filter(stream_alpha, 'xbr', n=4)
                        stream = ffmpeg.filter([stream, stream_alpha], 'alphamerge')
                    stream = ffmpeg.output(stream, os.path.join(new_root, file), pix_fmt='rgba')
                    ffmpeg.run(stream)
                print(root + "    " + file)
        else:
            shutil.copyfile(os.path.join(root, file), os.path.join(new_root, file))
    return ''

if __name__ == '__main__':
    main()