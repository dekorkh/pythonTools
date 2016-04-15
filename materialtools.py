'''
Created on Mar 13, 2014

@author: dkorkh
'''


import fileTools
import parsertools

SPECIFICVALUE   = 'specificvalue'
SVALUE          = 'svalue'
TEXTURE         = 'texture'
NORMALMAP       = 'normalmap'

def getTextures(material_f_path):
    r"""Return a list of texture names used by a material file."""
    ret_ls = []
    lines = fileTools.readFile(material_f_path)
    b_intex = 0
    for l in lines:
        l = parsertools.str_tokenize_clean(l)
        if (len(l) == 0): continue
        if (l[0] == SPECIFICVALUE and (l[1] == TEXTURE or l[1] == NORMALMAP)):
            b_intex = 1
        if (l[0] == SVALUE and b_intex):
            ret_ls.append(l[1])
            b_intex = 0
    return ret_ls

def getShaderGraph(shader_path):
    r"""Return a dictionary of shader operations and their inputs shader_graph[operation] = {'inputs'}"""
    shader_graph = {} 
    shader_content = fileTools.readFile(shader_path)
    in_op = 0
    for l in shader_content:
        l = l.lower().strip()
        if not len(l):
            continue
        l_tk = l.split()
        if l_tk[0] == 'operation':
            in_op = l_tk[1]
            shader_graph[l_tk[1]] = {'inputs':{},'outputs':{}}
        if in_op:
            if l_tk[0] == 'input':
                if in_op == 'myoutput':
                    shader_graph[in_op]['outputs'][l_tk[1]] = l_tk[2]
                else:
                    shader_graph[in_op]['inputs'][l_tk[2]] = 1
            if l_tk[0] == 'endoperation':
                in_op = 0
    return shader_graph

def getOpInputs(shader_graph, op):
    if not op in shader_graph:
        return {}
    inputs = {}
    for input in shader_graph[op]['inputs'].keys():
        inputs[input] = getOpInputs(shader_graph, input)
    return inputs

def getShaderOutputPath(shader_graph, output):
    if not 'myoutput' in shader_graph:
        return
    if not output in shader_graph['myoutput']['outputs']:
        return
    return {shader_graph['myoutput']['outputs'][output]:getOpInputs(shader_graph, shader_graph['myoutput']['outputs'][output])}
 
def printNodePath(node_path, depth = 0):
    if node_path:
        for node in node_path.keys():
            print "{}{}".format('\t'*depth,node)
            printNodePath(node_path[node], depth+1)

if __name__ == '__main__':
    ls = getTextures('c:/night/data/materials/Costumes/Avatar_Simple_Alpha_DS_01.Material')
    for tex in ls:
        print tex