# -*- coding: utf-8-*-
import os, sys, string, re

TYPE_MAPS = ("byte", "int", "word", "dword", "score", "string", "bool", "double", "float", "short")

#remove comments
def read_file_del_ex(file_name):
    exfile = os.path.join(sys.path[0],file_name)
    read_object = open(exfile,"r")
    read_text = read_object.read()
    read_text = re.sub('//[^\r\n]*|/\*.*?\*/', "", read_text)
    # read_text = re.sub('/\*.*?\*/', "", read_text)
    read_text = re.sub(';', "", read_text)
    read_object.close( )
    return read_text

def safe2Int(string):
    try:
        return int(string)
    except Exception, e:
        return None

# 宏定义 table
def get_define_table(text):
    # 宏定义表
    luastr = ""
    its = re.finditer('#define([^//\n]*)', text, re.M)
    dic = {}
    luastr = luastr + "local cmd = {\n"
    for match in its:
        m = match.group().split()
        if len(m) >= 3:
            dic[m[1]] = m[2]
            luastr = luastr + "%4s%s = %s,\n" %(' ', m[1], m[2])
    luastr = luastr + "}\n\n"
    return dic,luastr

def checkGrammer(ctx):
    resutl = re.findall(r"(struct +.*?{.*?,.*?})", ctx, re.S)
    if len(resutl)>0:
        print("Not support grammer yet!!======================")
        for m in resutl:
            print (m)
    return len(resutl) <= 0


def main(cppfile, savefile):
    ctx = read_file_del_ex(cppfile)
    defines,luastr = get_define_table(ctx)

    if not checkGrammer(ctx):
        return

    struct_it = re.finditer('struct +.*?{.*?}', ctx, re.S)

    def packArray(customStruct, varName, varType, size):
        if customStruct:
            line = '%4s{ k = "%s", t = "%s", d = %s, l = {%s} },\n' %(' ', varName, varType, customStruct, size)
        else:
            line = '%4s{ k = "%s", t = "%s", l = {%s} },\n' %(' ', varName, varType, size)
        return line

    for match in struct_it:
        array = match.group().split()

        luastr = luastr +  "cmd.%s = {\n" % array[1]

        key_value_pairs = len(array) - 4
        for i in range(1,key_value_pairs/2+1):
            offset = (i-1)*2
            key = array[3+offset]
            value = array[3+offset+1]

            enhance = None
            if key.lower() in TYPE_MAPS:
                key = key.lower()
            else:
                if key.lower() == "long":
                    key = "int"
                else:
                    enhance = "cmd." + key
                    key = "table"

            valueType = re.sub('\[(.*?)\]', '', value)
            params = re.findall('\[(.*?)\]', value)
            dimension = len(params)

            if dimension > 0:
                assert dimension <= 2, "Error need an too larger dimension!"
                line = ''
                if dimension == 1:
                    size = params[0]

                    if safe2Int(size):
                        line = packArray(enhance, valueType, key, size)
                    else:
                        line = packArray(enhance, valueType, key, "cmd."+size)

                else:
                    rep_count = params[0]
                    rep_str = params[1]
                    if safe2Int(rep_count):
                        result = ','.join([rep_str[:len(rep_str)]] * rep_count)

                        line = packArray(enhance, valueType, key, result)

                    elif defines.has_key(rep_count):
                        rep_count = defines[rep_count]
                        rep_count = int(rep_count)

                        if safe2Int(rep_str):
                            result = ','.join([rep_str[:len(rep_str)]] * rep_count)
                        else:
                            rep_str = "cmd." + rep_str
                            result = ','.join([rep_str[:len(rep_str)]] * rep_count)

                        line = packArray(enhance, valueType, key, result)

                luastr = luastr + line
            else:
                line = '%4s{ k = "%s", t = "%s" },\n' %(' ', valueType, key)
                luastr = luastr + line

        luastr = luastr + "}\n\n"

    luastr = luastr + "return cmd\n"
    fd = open(savefile, "w")
    fd.write(luastr)
    fd.close()

if __name__ == '__main__':
    cppfile = "CMD_PlazaServer.h"
    if len(sys.argv)>=2:
        cppfile = sys.argv[1]

    if os.path.isfile(cppfile):
        main(cppfile, cppfile + ".lua")