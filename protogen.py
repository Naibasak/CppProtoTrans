# -*- coding: utf-8-*-
import os, sys, string, re

# TYPE_MAPS = ("byte", "int", "word", "dword", "score", "string", "bool", "double", "float", "short")
TYPE_MAPS = {
"byte":"byte",
"int":"int",
"word":"word",
"dword":"dword",
"score":"score",
"longlong":"score",
"int64":"score",
"tchar":"string",
"bool":"bool",
"double":"double",
"float":"float",
"short":"short",
"long":"int",
}

#remove comments
def read_file_del_ex(file_name):
    exfile = os.path.join(sys.path[0],file_name)
    read_object = open(exfile,"r")
    read_text = read_object.read()

    # read_text = re.sub('//[^\r\n]*|/\*.*?\*/', "", read_text)
    read_text = re.sub(r'//[^\r\n]*', "", read_text)
    m = re.compile(r'/\*.*?\*/', re.S)
    read_text = re.sub(m, "", read_text)
    read_text = re.sub(';', "", read_text)

    read_object.close()
    return read_text

def safe2Int(string):
    try:
        return int(string)
    except Exception, e:
        return None

def get_define_table(text):
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
    result = re.findall(r"(struct +.*?{.*?,.*?})", ctx, re.S)
    if len(result)>0:
        print("Not support unfold grammer yet!!======================")
        return True

    result = re.findall(r'typedef.*?struct.*?{.*?}.*', ctx, re.S)
    if len(result) > 0:
        print("Not support typedef grammer yet!!======================")
        return True

def main(cppfile, savefile):
    ctx = read_file_del_ex(cppfile)
    defines,luastr = get_define_table(ctx)

    if checkGrammer(ctx) != None:
        return

    struct_it = re.finditer('struct +.*?{.*?}', ctx, re.S)

    def packArray(customStruct, varName, varType, size):
        if customStruct:
            line = '%4s{ k = "%s", t = "%s", d = %s, l = {%s} },\n' %(' ', varName, varType, customStruct, size)
        else:
            if varType == "string":
                line = '%4s{ k = "%s", t = "%s", s = %s },\n' %(' ', varName, varType, size)
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
            if TYPE_MAPS.has_key(key.lower()):
                key = TYPE_MAPS[key.lower()]
            else:
                enhance = "cmd." + key
                key = "table"

            valueType = re.sub('\[(.*?)\]', '', value)
            params = re.findall('\[(.*?)\]', value)
            dimension = len(params)

            if dimension > 0:
                assert dimension <= 2, "Error need a too larger dimension!"
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
                if not enhance:
                    line = '%4s{ k = "%s", t = "%s" },\n' %(' ', valueType, key)
                    luastr = luastr + line
                else:
                    line = '%4s{ k = "%s", t = "%s", d = %s },\n' %(' ', valueType, key, enhance)
                    luastr = luastr + line

        luastr = luastr + "}\n\n"

    luastr = luastr + "return cmd\n"
    fd = open(savefile, "w")
    fd.write(luastr)
    fd.close()

if __name__ == '__main__':
    cppfile = "test.txt"
    if len(sys.argv)>=2:
        cppfile = sys.argv[1]

    if os.path.isfile(cppfile):
        main(cppfile, cppfile + ".lua")
    else:
        print(cppfile  + " not found!")
