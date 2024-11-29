import argparse
import hexdump
import xml.etree.ElementTree as et
import crcmod

DEBUG = False


crcFun = crcmod.mkCrcFun( poly=0x1A001, initCrc=0, rev=True, xorOut=0 )


parser = argparse.ArgumentParser()
parser.add_argument(
    "-f",
    "--file",
    required=False,
    default=None,
    help="process binary flash file name. if ommitted only check is performed",
)

parser.add_argument(
    "-u",
    "--odx1",
    required=True,
    default=None,
    help="odx that patched binary",
)

parser.add_argument(
    "-o",
    "--odx2",
    required=True,
    default=None,
    help="odx of orignal binary",
)


def find_block_data(root, address_orig, size_orig):
    flash = root.find("FLASH")
    ecumems = flash.find("ECU-MEMS")
    ecumem = ecumems.find("ECU-MEM")
    mem = ecumem.find("MEM")
    datablocks = mem.find("DATABLOCKS")
    flashdatas = mem.find("FLASHDATAS")
    # process each data block and find referenced flashdata
    for datablock in datablocks.iter("DATABLOCK"):
        block_id_ref = datablock.find("FLASHDATA-REF").get("ID-REF")                    
        segments = datablock.find("SEGMENTS")
        for segment in segments.iter("SEGMENT"):
            address = int(segment.find("SOURCE-START-ADDRESS").text, 16)
            uncompr_size = int(segment.find("UNCOMPRESSED-SIZE").text, 10)
            if address == address_orig:
                if uncompr_size != size_orig:
                    print("Size not matched %x!=%x" % (uncompr_size, size_orig))
                    return None
                for flashdata in flashdatas.iter("FLASHDATA"):
                    szID = flashdata.get("ID")
                    if szID == block_id_ref:
                        encr = flashdata.find("ENCRYPT-COMPRESS-METHOD")
                        encrmethod = 0
                        if encr != None:
                            encrmethod = int(encr.text)
                        if encrmethod > 0:
                            print("Can't work - encrypted")
                        data = flashdata.find("DATA").text
                        return bytearray.fromhex(data)
    return None

# replaces binary sequence
# @param bindata - the data where to find sequence
# @param find_data - the data to be found
# @param replace_data - the data to be replaced
# @return new (updated) bindata
def replace_binary(bin_data, find_data, replace_data):
    out_data = b''
    assert len(find_data) == len(replace_data)
    f1 = bin_data.find(find_data)
    if (f1==-1):
        print("Sequence size (0x%X) not found in binary (crc=0x%0X). It will be skipped..."%(len(find_data) , crcFun(find_data)))
        return bin_data
    print("Pattern found at [0x%X] - Performing REPLACEMENT!"%f1)
    out_data = bin_data[0:f1] + replace_data + bin_data[f1+len(replace_data):]
    f1 = out_data.find(find_data)
    if (f1==-1):
        return out_data
    print("Warning! Pattern found several times! Replacement ambigous, skipping...")
    print()
    return bin_data


args = parser.parse_args()
# crc32_adlatus = crcmod.mkCrcFun(0x104C11DB7, initCrc=0, xorOut=0, rev=True)
bin_data=None
if (args.file):
    print("Openning binary patched file: %s"%args.file)
    binf = open(args.file, "rb")
    bin_name_mod = args.file + ".mod"
    bin_data = binf.read()
    binf.close()

tree_patched = et.parse(args.odx1)
tree_orig = et.parse(args.odx2)
root_orig = tree_orig.getroot()
flash_orig = root_orig.find("FLASH")
root_patched = tree_patched.getroot()
flash = root_patched.find("FLASH")
print("Processing patched '%s'"%args.odx1)
print("Found FLASH ID %s" % flash.get("ID"))
print()
print("Processing original '%s'"%args.odx2)
print("Found FLASH ID %s" % flash_orig.get("ID"))
print()
ecumems = flash.find("ECU-MEMS")
ecumem = ecumems.find("ECU-MEM")
mem = ecumem.find("MEM")
datablocks = mem.find("DATABLOCKS")
flashdatas = mem.find("FLASHDATAS")
# process each data block and find referenced flashdata
for datablock in datablocks.iter("DATABLOCK"):
    print("processing block : %s" % datablock.find("SHORT-NAME").text)
    block_id_ref = datablock.find("FLASHDATA-REF").get("ID-REF")
    segments = datablock.find("SEGMENTS")
    for segment in segments.iter("SEGMENT"):
        address = int(segment.find("SOURCE-START-ADDRESS").text, 16)
        uncompr_size = int(segment.find("UNCOMPRESSED-SIZE").text, 10)
        print("Address: 0x%X, Size: 0x%X"% (address,uncompr_size))
    for flashdata in flashdatas.iter("FLASHDATA"):
        szID = flashdata.get("ID")
        if szID == block_id_ref:
            encr = flashdata.find("ENCRYPT-COMPRESS-METHOD")
            encrmethod = 0
            if encr != None:
                encrmethod = int(encr.text)
            if encrmethod > 0:
                print("Can't work - encrypted")
            data = flashdata.find("DATA").text
            byte_data = bytearray.fromhex(data)
            print("Realsize data: 0x%X"% len(byte_data))
            byte_data_orig = find_block_data(
                root_orig, address, uncompr_size
            )
            if byte_data_orig == None:
                print("Block not found in original file. Repair procedure impossible!")
                exit(0)
            if byte_data == byte_data_orig:
                print("Matched, no need to replace, skipping...")
            else:
                print("Not matched! Need to replace!")
                if DEBUG:
                    if (len(byte_data)<0x40): 
                        max_dump_len = len(byte_data)
                    else:
                        max_dump_len = 0x40
                    print("Patched:")
                    hexdump.hexdump(byte_data[:max_dump_len])
                    # debug    :
                    # binf = open("uuuu", "wb")    
                    # binf.write(byte_data)
                    # binf.close()
                    print("Orig:")
                    hexdump.hexdump(byte_data_orig[:max_dump_len])
                if (bin_data):
                    bin_data = replace_binary(bin_data, byte_data, byte_data_orig)


if (args.file):
    print("Writing modified file into '%s'"%bin_name_mod)
    binf = open(bin_name_mod, "wb")    
    binf.write(bin_data)
    binf.close()

