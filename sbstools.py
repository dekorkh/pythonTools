'''
A collection of tools to assist with substance designer.

Classes:

Functions:
getDependencies(sbs_path) -- Return a list of dependencies.

Exceptions:

Notes:
commandline to render using sbsrender.exe:
"C:\Program Files\Allegorithmic\Substance\Designer\4.x\sbsrender.exe" render --inputs "C:\Leviathan\src\texture_library\Test\check5_terrain\check5_color_x0_y3.sbsar" --output-path "C:\Leviathan\src\texture_library\Test\check5_terrain" --output-name "check5_color_x0_y3" --engine "d3d10pc" --set-value "$outputsize"@"10,10" --output-format tga

@author: dkorkh
'''
#===============================================================================
# IMPORTS
#===============================================================================
import fileTools as ft
import xml.etree.ElementTree as et
import uuid
from getpass import getuser
import subprocess
import printtools as pt
#===============================================================================
# CONSTANTS
#===============================================================================
SBSTEMPLATE_EMPTY = r"C:\Leviathan\src\substance_library\Cryptic\Cryptic_Empty.sbs"

#Load the Substance working environment paths (used for relative addresses specified by URL e.g. sbs://)
SBSRENDER = r"C:\Program Files\Allegorithmic\Substance\Designer\4.x\sbsrender.exe"
SBSALIASES = {'sbs':r"C:\Program Files\Allegorithmic\Substance\Designer\4.x\resources\packages"} 
config_dir = 'c:/users/{username}/AppData/Local/Allegorithmic/'.format(username = getuser())
config_fpn = ft.searchFiles(config_dir, 'xml', 'user_preferences')
config_fpn = [x for x in config_fpn if x.lower().find('substance-designer') != -1][0]
tree = et.parse(config_fpn)
root = tree.getroot()
SBSALIASES['sbs'] = root.findtext('.//packagesdir')
tree = None
root = None

#===============================================================================
# CLASSES
#===============================================================================


class SBSElement(object):
    r"""An SBS file element."""
    def __init__(self, elem, depth = None):
        self.tag = elem.tag
        self.attrs = [SBSElement(x) for x in elem.attrs] 
        self.value = elem.get('v')
        self.depth = depth
        self.et_elem = elem
            

class Graph(object):
    r"""A basic graph object."""
    def __init__(self, graph_elem):
        self.graph_elem = graph_elem
        self.uid = 0
        

class Asset(object):
    r"""A texture map class"""
    def __init__(self, fp, atype = "OTHER"):
        self.fp = fp
        self.atype = atype 

class SBS(object):
    FORMAT_FULL     = 0
    FORMAT_PARAM    = 0
    FORMAT_SFFX     = 1
    FORMAT_SWAP     = 2
    
    
    MAPTYPE_NORMAL    = ['normal', 'n', 'tex_n']
    MAPTYPE_HEIGHT    = ['height', 'h', 'tex_h']
    MAPTYPE_POSITION  = ['position', 'p', 'tex_p']
    MAPTYPE_NORMALWS  = ['normal_world_space', 'wsn', 'tex_wsn']
    MAPTYPE_AO        = ['ambient_occlusion', 'ao', 'tex_ao'] 
    MAPTYPE_MATERIAL  = ['material', 'm', 'tex_m']
    MAPTYPE_LIST = [MAPTYPE_NORMAL,
                    MAPTYPE_HEIGHT,
                    MAPTYPE_POSITION,
                    MAPTYPE_NORMALWS,
                    MAPTYPE_AO,
                    MAPTYPE_MATERIAL]  
    
    GEO_L         = 'geometry_low'
    GEO_H         = 'geometry_high'
    
    SBSTAG_UID          = "uid"
    SBSTAG_GRAPH        = "graph"
    
    def __init__(self,
                 tex_m_fpn,
                 tex_n_fpn,
                 tex_h_fpn,
                 tex_ao_fpn,
                 tex_wsn_fpn,
                 tex_p_fpn,
                 geo_l_fpn,
                 package_template = r'C:\Leviathan\src\substance_library\Cryptic\Cryptic_Package.sbs'):
        self.package_path   = package_template
        
        self.tex_m_fpn      = tex_m_fpn
        self.tex_h_fpn      = tex_h_fpn
        self.tex_n_fpn      = tex_n_fpn
        self.tex_ao_fpn     = tex_ao_fpn
        self.tex_wsn_fpn    = tex_wsn_fpn
        self.tex_p_fpn      = tex_p_fpn
        self.geo_l_fpn      = geo_l_fpn
        self.package_template = package_template
        self.package_tree = et.parse(self.package_template)
        self.package_root = self.package_tree.getroot()
        self.UID = None
        self.__getDepUID()
        self.uid_ls = []
        self.__updateuid_ls
        
    def __updateuid_ls(self):
        self.uid_ls = [int(x.get("v")) for x in self.package_root.iter(SBS.SBSTAG_UID)]
    
    def __getDepUID(self):
        r"""Each package has a UID for self.  Find it."""
        rsrc = self.package_root.findall(".//*[@v='?himself']/../uid")[0]
        self.UID = rsrc.get('v')
        
    def setMap(self, maptype, new_path, res):
        r"""Sets the respective placeholder of maptype to the new map in the *.sbs file."""
        new_path = new_path.replace('\\', '/')
        for MAPTYPE in SBS.MAPTYPE_LIST:
            if maptype == MAPTYPE[SBS.FORMAT_FULL]:
                maptype = MAPTYPE[SBS.FORMAT_SWAP]
        rel_path = ft.getRelativePathFrom(ft.getDirectory(self.package_path), new_path)
        map_name = new_path.split('/')[-1]
        map_name = map_name.split('.')[0]
        #correct rel_path filename capitalization to original
        rel_path = '/'.join(rel_path.split('/')[:-1] + [new_path.split('/')[-1]])
        
        #set new file-path for resource
        rsrc = self.package_root.findall(".//*[@v='{}']/../filepath".format(maptype))
        if len(rsrc) == 0: raise SBS_SetMapError(maptype, "template may be corrupt.")
        rsrc = rsrc[0]
        rsrc.set('v',rel_path)
        
        #set new file-name for resource
        rsrc = self.package_root.findall(".//*[@v='{}']/../identifier".format(maptype))
        if len(rsrc) == 0: raise SBS_SetMapError(maptype, "template may be corrupt.")
        rsrc = rsrc[0]
        rsrc.set('v','{}'.format(map_name))
        
        #update graph node that references the resource
        rsrc_node = self.package_root.findall(".//*[@v='pkg://Resources/{}?dependency={}']/../../../../../../".format(maptype, self.UID))
        if len(rsrc_node) == 0: raise SBS_SetMapError(maptype, "template may be corrupt.")
        rsrc_node = rsrc_node[0]
        #set the output node resolution
        rsrc_node.findall('.//constantValueInt2/value')[0].set('v', res)
                        
        #update graph node that references the resource
        rsrc = self.package_root.findall(".//*[@v='pkg://Resources/{}?dependency={}']".format(maptype, self.UID))
        if len(rsrc) == 0: raise SBS_SetMapError(maptype, "template may be corrupt.")
        rsrc = rsrc[0]
        rsrc.set('v','pkg://Resources/{}?dependency={}'.format(map_name, self.UID))
    
    def report(self, sbs_elem = None, depth = 0, file_path = None):
        r"""Dump the SBS node tree to console and if filepath is provided to file."""
        if sbs_elem == None:
            sbs_elem = self.package_root
        ret_str = '{}tag:{:.<30}attrib:{:40}'.format(('\t' * depth), sbs_elem.tag, sbs_elem.attrib, sbs_elem.text, sbs_elem.tail) 
        for child in sbs_elem:
            ret_str += "\n" + self.report(sbs_elem = child, depth = (depth + 1))
        if depth == 0:
            print ret_str
            if file_path:
                ft.writeFile(file_path, [ret_str])
        else:
            return ret_str
    
    def setModel(self, model_path):
        #update graph node that references the resource
        rsrc = self.package_root.findall(".//*[@v='{}']/../filepath".format('geo_low'))
        if len(rsrc) == 0: raise SBS_SetModelError("template may be corrupt.")
        rsrc = rsrc[0]
        rsrc.set('v','{}'.format(ft.getRelativePathFrom(ft.getDirectory(self.package_path), model_path)))
        rsrc = self.package_root.findall(".//*[@v='{}']/../identifier".format('geo_low'))
        if len(rsrc) == 0: raise SBS_SetModelError("template may be corrupt.")
        rsrc = rsrc[0]
        rsrc.set('v','{}'.format(ft.fileKey(model_path)))
        
    
    def makePackage(self, path, res = '11 11'):
        r"""Make a package from files in directory."""
        self.package_path = path
        self.setMap(SBS.MAPTYPE_MATERIAL[SBS.FORMAT_PARAM], self.tex_m_fpn, res)
        self.setMap(SBS.MAPTYPE_NORMAL[SBS.FORMAT_PARAM], self.tex_n_fpn, res)
        self.setMap(SBS.MAPTYPE_HEIGHT[SBS.FORMAT_PARAM], self.tex_h_fpn, res)
        self.setMap(SBS.MAPTYPE_AO[SBS.FORMAT_PARAM], self.tex_ao_fpn, res)
        self.setMap(SBS.MAPTYPE_NORMALWS[SBS.FORMAT_PARAM], self.tex_wsn_fpn, res)
        self.setMap(SBS.MAPTYPE_POSITION[SBS.FORMAT_PARAM], self.tex_p_fpn, res)
        
        
        self.setModel(self.geo_l_fpn)
        self.package_tree.write(path)        


#===============================================================================
# FUNCTIONS
#===============================================================================
def openSBS(sbs_fpn):
    r"""Return the (tree, root) of sbs_fpn."""
    tree = et.parse(sbs_fpn)
    root = tree.getroot()
    return (tree, root)

def getDependencies(sbs_fpn):
    r"""Return a list of elements for dependencies in an sbs."""
    try:
        sbs_tree = et.parse(sbs_fpn)
    except:
        raise SBS_CorruptFileError(sbs_fpn)
    sbs_root = sbs_tree.getroot()
    return sbs_root.findall(".//dependency")

def changeDependencyPath(sbs_fpn, dep_fpn_old, dep_fpn_new):
    r"""Change the path of a dependency."""
    if not ft.os.access(sbs_fpn, ft.os.W_OK):
        raise SBS_IOError(sbs_fpn)
    tree, root = openSBS(sbs_fpn)
    dep_relfpn_old = ft.getRelativePathFrom(sbs_fpn, dep_fpn_old)
    dep_relfpn_new = ft.getRelativePathFrom(sbs_fpn, dep_fpn_new)
    dep_dct = dict([(x.find('./filename').get('v').lower(), x) for x in root.findall('.//dependency')])
    dep = dep_dct[dep_relfpn_old]
    dep.find('filename').set('v', dep_relfpn_new)
    tree.write(sbs_fpn,
               encoding="UTF-8",
               xml_declaration=True,
               method="xml")

def getDependentFiles(root, sbs_fpn):
    r"""Return a list of sbs files dependenent on sbs_fpn."""
    sbs_fpn_ls = ft.searchFiles(root, 'sbs')
    pbar = pt.PBar2("Checking SBS files for dependency to {}".format(sbs_fpn.replace("\\","/").split("/")[-1]), len(sbs_fpn_ls), chr(135), 80)
    sbs_fpn_ls = [x for x in sbs_fpn_ls if x.lower().find('_macos') == -1]
    sbs_fpn_ls = [x for x in sbs_fpn_ls if x.lower().find('.autosave') == -1]
    return [x for x in sbs_fpn_ls if hasDependency(x, sbs_fpn, pbar)]

def hasDependency(sbs_fpn, dep_fpn, pbar = None):
    r"""Return True if the sbs_fpn has dep_fpn in its dependencies, False otherwise."""
    dep_fpn_rel = ft.getRelativePathFrom(sbs_fpn, dep_fpn)
    sbs_dep_fpn_ls = [x.find('filename').get('v').lower() for x in getDependencies(sbs_fpn)]
    if pbar:
        pbar.update()
    return (dep_fpn_rel in sbs_dep_fpn_ls)    

def getDependenciesByGraph(sbs_fpn, dep_fpn, graph_nm):
    r"""Return a dct of graph elements that are dependent on graph_nm from dep_fpn."""
    ret_dct = dict()
    tree, root = openSBS(sbs_fpn)
    graph_elem_ls = root.findall('.//graph')
    for graph_elem in graph_elem_ls:
        instNode_elem_ls = graph_elem.findall('.//compInstance/../..')
        instNode_v_ls = [x.find('.//compInstance/path/value').get('v') for x in instNode_elem_ls]
        instNode_graphname_ls = [x.split('//')[-1].split('?')[0].lower() for x in instNode_v_ls]
        if graph_nm.lower() in instNode_graphname_ls:
            graph_elem_id = graph_elem.find('./uid').get('v')
            if not graph_elem_id in ret_dct:
                ret_dct[graph_elem_id] = graph_elem
    return ret_dct

def formatSBSElement(sbs_elem, depth = 0):
    r"""Return the SBS element node tree as a pretty formatted string."""
    ret_str = '{}tag:{:.<30}attrib:{:40}'.format(('\t' * depth), sbs_elem.tag, sbs_elem.attrib) 
    for child in sbs_elem:
        ret_str += "\n" + formatSBSElement(sbs_elem = child, depth = (depth + 1))
    return ret_str

def formatSBSFile(sbs_path, file_path = None):
    r"""Dump the SBS node tree to console and if filepath is provided to file."""
    sbs_tree = et.parse(sbs_path)
    sbs_root = sbs_tree.getroot()
    ret_str = formatSBSElement(sbs_root, depth = 0) 
    print ret_str
    if file_path:
        ft.writeFile(file_path, [ret_str])

def cookSBS(sbs_path):
    r"""Cook an SBS into an SBSAR file."""
    pass

#--------------------------------------------

def moveGraph(sbs_fpn_from, sbs_fpn_to, old_graph_name, new_graph_name, root_path):
    r"""Move a graph from one sbs to another and fix up dependencies in all directories in dep_path_ls.
    If the target sbs path doesn't exist, a new file will be made for it.
    Arguments:
    sbs_fpn_from  -- Path to the graph's current sbs file. 
    sbs_fpn_to    -- Path to the graph's target sbs file.
    old_graph_name -- The name of the graph as is
    new_graph_name -- The new name for the graph
    dep_fpn_ls    -- Path to root directory within which to check and fix dependencies.
    """
    dep_fpn_ls = getDependentFiles(root_path, sbs_fpn_from)
    ft.checkOutMany(dep_fpn_ls, batch_size = 50)
    for fpn in dep_fpn_ls:
        allrdy = 1
        if not ft.os.access(fpn, ft.os.W_OK):
            print "Couldn't check out {}".format(fpn)
            allrdy = 0
        if not allrdy:
            raise
    ft.checkOutFile(sbs_fpn_from)
    
    copyGraph(sbs_fpn_from, sbs_fpn_to, old_graph_name)
    removeGraph(sbs_fpn_from, old_graph_name)
    renameGraph(sbs_fpn_to, old_graph_name, new_graph_name)
    
    for fpn in dep_fpn_ls:
        reconnectSBSDep(sbs_fpn_from, sbs_fpn_to, fpn)
        renameGraphReferences(fpn, old_graph_name, new_graph_name)    

def findBrokenSBS_FileDependencies(root_path):
    r"""Return a list of files with broken file dependencies."""
    ret_ls = []
    sbs_fp_ls = ft.searchFiles(root_path, 'sbs')
    for sbs_fp in sbs_fp_ls:
        dep_ls = getDependencies(sbs_fp)
        for dep in dep_ls:
            dep_fp = dep.find('filename').get('v')
            dep_fp_abs = (ft.getDirectory(sbs_fp) + '/' + dep_fp)
            if not ft.os.access(dep_fp_abs, ft.os.F_OK) and not sbs_fp in ret_ls:
                ret_ls.append(sbs_fp)
    return ret_ls

def reconnectSBSDep(sbs_fpn_old, sbs_fpn_new, sbs_fpn):
    r"""Fix-up a dependency path in dep_sbs. Return number of dependencies fixed"""
    num_fixed = 0
    if not ft.canWrite(sbs_fpn):
        raise SBS_IOError(sbs_fpn) 
    sbs_fpn_old = ft.getRelativePathFrom(sbs_fpn, sbs_fpn_old).lower().replace('\\','/')
    sbs_fpn_new = ft.getRelativePathFrom(sbs_fpn, sbs_fpn_new).lower().replace('\\','/')
    tree = et.parse(sbs_fpn)
    root = tree.getroot()
    dep_ls = root.findall(".//dependency")
    for dep in dep_ls:
        dep_fpn_elem = dep.find('filename') 
        dep_fpn = dep_fpn_elem.get('v').lower()
        if dep_fpn == sbs_fpn_old:
            dep_fpn_elem.set('v', sbs_fpn_new)
            num_fixed += 1
    tree.write(sbs_fpn)

def findSBSUsage(sbs_path, graph_name):
    r"""Return a list of SBS files (paths) and graphs that reference a given SBS and graph."""
    #collect sbs files
    #go through each sbs file
        #go through each sbs file's graph
        #Check if has reference to sbs_path and graph_name 

def collectSBS(root_path):
    r"""Return a dictionary of {SBS_File1:[Graph1, Graph2, ...], SBS_File2:[Graph1, Graph2, ...], ...} under root_path"""
    ret_dct = {}
    sbs_fp_ls = ft.searchFiles('c:/Denis_Korkh', 'sbs')
    for sbs_fp in sbs_fp_ls:
        sbs_fp_lower = sbs_fp.lower()
        ret_dct[sbs_fp_lower] = getGraphs(sbs_fp_lower)
    return ret_dct
    
def getGraphs(sbs_fpn):
    r"""Return a list of et elements for sbs graphs within sbs_fpn."""
    #Read the sbs and collect graph names
    sbs_tree = et.parse(sbs_fpn)
    sbs_root = sbs_tree.getroot()
    return sbs_root.findall(".//graph")

def getGraphOutputs(sbs_fpn, graph_nm):
    r"""Return a list of et elements for sbs outputs for a graph within sbs_fpn."""
    #Read the sbs
    sbs_tree = et.parse(sbs_fpn)
    sbs_root = sbs_tree.getroot()
    
    return sbs_root.findall(".//graph/identifier[@v='{}']/../graphOutputs/graphoutput".format(graph_nm))

def makeSBSFile(sbs_path, template = SBSTEMPLATE_EMPTY, overwrite = 0):
    r"""Make a new sbs file at sbs_path.
    Will raise SBS_IOError if there is a file and overwrite is 0
    
    Arguments:
    sbs_path      -- The path at which to make the file.
    overwrite     -- Allow to overwrite if a file exists and is writable."""
    if ft.os.path.exists(sbs_path) and not overwrite:
        raise SBS_IOError(sbs_path)
    if ft.os.path.exists(sbs_path) and not ft.os.access(sbs_path, ft.os.W_OK):
        raise SBS_IOError(sbs_path)
    tree = et.parse(template)
    root = tree.getroot()
    fileUID = root.find('fileUID')
    fileUID.set('v', str(uuid.uuid4()))
    tree.write(sbs_path, encoding="UTF-8", xml_declaration=True, method="xml")
    
def copyGraph(sbs_fpn_src, sbs_fpn_trg, sbs_graph_nm):
    r"""Copy a graph from sbs_fpn_src to sbs_fpn_trg. 
    Will create a new target file if one doesn't exists.
    
    Arguments:
    sbs_fpn_src   -- the source sbs file
    sbs_fpn_trg   -- the target sbs file
    sbs_graph_nm  -- graph name
    """
    #Assert target path is not locked if exists
    if ft.os.path.exists(sbs_fpn_trg):
        if not ft.os.access(sbs_fpn_trg, ft.os.W_OK):
            raise SBS_IOError(sbs_fpn_trg)
    else: #Create target path if it doesn't exist
        makeSBSFile(sbs_fpn_trg)
        
    #Assert source path exists
    if not ft.os.path.exists(sbs_fpn_src):
        raise SBS_MissingFileError(sbs_fpn_src)
        
    #check target file for a graph by the same name
    tree_trg = et.parse(sbs_fpn_trg)
    root_trg = tree_trg.getroot()
    graph_elem_trg = root_trg.find(".//graph/identifier[@v='{}']/..".format(sbs_graph_nm))
    if graph_elem_trg != None:
        raise SBS_CopyGraphError(sbs_fpn_src, sbs_fpn_trg, sbs_graph_nm)
    
    #check the source file for the wanted graph
    tree_src = et.parse(sbs_fpn_src)
    root_src = tree_src.getroot()
    graph_elem_src = root_src.find(".//graph/identifier[@v='{}']/..".format(sbs_graph_nm))
    if graph_elem_src == None:
        raise SBS_CopyGraphError(sbs_fpn_src, sbs_fpn_trg, sbs_graph_nm)
    
    #check the target file for the content element
    content_trg = root_trg.find('content')
    if content_trg == None:
        raise SBS_CopyGraphError(sbs_graph_nm, sbs_fpn_src, sbs_fpn_trg)
    
    #check the target file for the dependencies element
    dependencies_trg = root_trg.find('dependencies')
    if dependencies_trg == None:
        raise SBS_CopyGraphError(sbs_graph_nm, sbs_fpn_src, sbs_fpn_trg)
    
    #Check/find/compare/copy dependencies.
    graph_dep_dct_src = getGraphDependencies(sbs_fpn_src, sbs_graph_nm)
    for graph_dep_src in graph_dep_dct_src.itervalues():
        himself = 0
        graph_dep_src_relfpn = graph_dep_src.find('filename').get('v')
        if graph_dep_src_relfpn == '?himself':
            himself = 1
        graph_dep_fpn_src = ft.os.path.split(sbs_fpn_src)[0] + "/" + graph_dep_src_relfpn
        alias = graph_dep_src_relfpn.split(':')[0]
        if alias in SBSALIASES:
            graph_dep_fpn_src = graph_dep_src_relfpn
        if himself:
            graph_dep_fpn_src = ft.getRelativePathFrom(sbs_fpn_trg, sbs_fpn_src)
        if not hasDependency(sbs_fpn_trg, graph_dep_fpn_src):
            graph_dep_fpn_src_abs = ft.os.path.normpath(graph_dep_fpn_src).replace('\\', '/')
            alias = graph_dep_src_relfpn.split(':')[0]
            if alias in SBSALIASES:
                graph_dep_fpn_src_abs = ft.os.path.normpath(graph_dep_src_relfpn.replace(alias + ':', SBSALIASES[alias])).replace('\\', '/')
            if graph_dep_fpn_src_abs.lower() != sbs_fpn_trg.replace('\\','/').lower():
                if alias in SBSALIASES:
                    graph_dep_src.find('filename').set('v', graph_dep_src_relfpn)
                if himself:
                    graph_dep_src.find('filename').set('v', graph_dep_fpn_src)
                else:
                    graph_dep_src.find('filename').set('v', ft.getRelativePathFrom(sbs_fpn_trg, graph_dep_fpn_src_abs))
                dependencies_trg.append(graph_dep_src)
    
    #Copy the graph
    content_trg.append(graph_elem_src)
    
    #write the file
    tree_trg.write(sbs_fpn_trg, 
                   encoding = "UTF-8", 
                   xml_declaration = True, 
                   method = "xml")
    
def getGraphDependencies(sbs_fpn, graph_nm):
    r"""Return a dict of dependencies in sbs_fpn referenced by graph_nm."""
    tree, root = openSBS(sbs_fpn)
    find_str = ".//graph/identifier[@v='{}']/..".format(graph_nm)
    graph_elem = root.find(find_str)
    if graph_elem == None:
        raise SBS_MissingElementError(find_str, root)
    ret_dep_dct = {}
    sbs_dep_dct = dict([(x.find("uid").get("v"), x) for x in root.findall(".//dependency")])
    
    graph_elem_deps = graph_elem.findall('.//compInstance')
    for graph_elem_dep in graph_elem_deps:
        graph_dep_id = graph_elem_dep.find('.//path/value').get('v')
        graph_dep_id = graph_dep_id.split('=')[-1]
        if graph_dep_id in sbs_dep_dct and not graph_dep_id in ret_dep_dct:
            ret_dep_dct[graph_dep_id] = sbs_dep_dct[graph_dep_id]
    return ret_dep_dct
    
def getDependencyGraphs(sbs_fpn, dep_fpn):
    r"""Return a dictionary of graph elements in sbs_fpn using a dep_fpn."""
    ret_dct = dict()
    sbs_tree, sbs_root = openSBS(sbs_fpn)
    dep_relfpn = ft.getRelativePathFrom(sbs_fpn, dep_fpn)
    if dep_fpn.split(':')[0] in SBSALIASES:
        dep_relfpn = dep_fpn
    dep_dct = dict([(x.find('./filename').get('v').lower(), x) for x in sbs_root.findall('.//dependency')])
    dep_uid = dep_dct[dep_relfpn].find('uid').get('v')
    #dep_uid = sbs_root.find('.//dependency/filename[@v=\'{}\']/../uid'.format(dep_relfpn)).get('v')
    dep_graph_ls = getGraphs(sbs_fpn)
    for dep_graph in dep_graph_ls:
        dep_graph_uid = dep_graph.find('.//uid').get('v')
        graph_dep_uid_ls = getGraphDependencies(sbs_fpn, dep_graph.find('identifier').get('v')).keys()
        if dep_uid in graph_dep_uid_ls and not dep_graph_uid in ret_dct:
            ret_dct[dep_graph_uid] = dep_graph
    return ret_dct
        
        #if hasDendency()
    
    #sbs_dep_dct = getGraphDendencies

def removeGraph(sbs_fpn, graph_nm):
    r"""Remove graph_nm from sbs_fpn.
    Removes any of its dependencies if they're not used after removal.
    Stupidly writes before checking whether to remove dependencies because this whole thing is stupidly written."""
    if not ft.os.access(sbs_fpn, ft.os.W_OK):
        raise SBS_IOError(sbs_fpn)
    tree, root = openSBS(sbs_fpn)
    
    #find graph and remove it from content
    content = root.find('./content')
    graph = content.find('./graph/identifier[@v=\'{}\']/..'.format(graph_nm))
    graph_dep_id_ls_dirty = getGraphDependencies(sbs_fpn, graph_nm).keys()
    if graph != None:
        content.remove(graph)
    tree.write(sbs_fpn,
               encoding = "UTF-8",
               xml_declaration = True,
               method = "xml")
    
    #check if that graphs dependencies are still necessary
        
    tree, root = openSBS(sbs_fpn)
    for graph_dep_id in graph_dep_id_ls_dirty:
        find_str = './/dependency/uid[@v=\'{}\']/..'.format(graph_dep_id)
        graph_dep = root.find(find_str)
        if graph_dep == None:
            raise SBS_MissingElementError(find_str, root)
        graph_dep_fpn = graph_dep.find('filename').get('v')
        graph_dep_alias = graph_dep_fpn.split(':')[0]
        if not graph_dep_alias in SBSALIASES:
            graph_dep_fpn = ft.os.path.normpath(ft.os.path.dirname(sbs_fpn) + '/' + graph_dep_fpn)
        dep_graphs = getDependencyGraphs(sbs_fpn, graph_dep_fpn)
        if len(dep_graphs) == 0:
            find_str = './/dependencies'
            deps_elem = root.find(find_str)
            if deps_elem == None:
                raise SBS_MissingElementError(find_str, deps_elem)
            deps_elem.remove(graph_dep)
            tree.write(sbs_fpn,
               encoding = "UTF-8",
               xml_declaration = True,
               method = "xml")    

def renameGraphReferences(sbs_fpn, old_graph_nm, new_graph_nm):
    r"""Rename graph references within the sbs_fpn."""
    if not ft.os.access(sbs_fpn, ft.os.W_OK):
        raise SBS_IOError(sbs_fpn)
    tree, root = openSBS(sbs_fpn)
    graph_refs = root.findall('.//compInstance/path/value')
    for graph_ref in graph_refs:
        graph_ref_graphname = graph_ref.get('v').split('?')[0].split('/')[-1]
        graph_ref_depinfo = graph_ref.get('v').split('?')[-1]
        if old_graph_nm.lower() == graph_ref_graphname.lower():
            graph_ref.set('v', 'pkg://{}?{}'.format(new_graph_nm, graph_ref_depinfo))
    tree.write(sbs_fpn,
               encoding = "UTF-8",
               xml_declaration = True,
               method = "xml")
    
def renameGraph(sbs_fpn, old_graph_nm, new_graph_nm):
    if not ft.os.access(sbs_fpn, ft.os.W_OK):
        raise SBS_IOError(sbs_fpn)
    tree, root = openSBS(sbs_fpn)
    renameGraphReferences(sbs_fpn, old_graph_nm, new_graph_nm)
    graph_ls = root.findall('.//graph/identifier')
    for graph_ref in graph_ls:
        graph_ref_graphname = graph_ref.get('v')
        if old_graph_nm.lower() == graph_ref_graphname.lower():
            graph_ref.set('v', new_graph_nm)
    tree.write(sbs_fpn,
               encoding = "UTF-8",
               xml_declaration = True,
               method = "xml")
    
def moveSourceTexture(dep_sbs, tex_path_old, tex_path_new):
    r"""Move a source texture and update a dependent sbs with new path"""


def renderSBSAR(sbsar_path, output, out_path, width, height):
    renderpipe = subprocess.check_output('{renderer} render \
                                            --inputs {inputs} \
                                            --input-graph-output {output} \
                                            --output-path {out_path} \
                                            --output-name {out_name} \
                                            --engine "d3d10pc" \
                                            --set-value "$outputsize"@"{width},{height}" \
                                            --output-format tga'.format(renderer = SBSRENDER,
                                                                        inputs = sbsar_path,
                                                                        output = output,
                                                                        out_path = out_path,
                                                                        out_name = '{inputGraphUrl}_{outputNodeName}',
                                                                        width = width,
                                                                        height = height))
    for line in renderpipe.split('\n'):
        print line,

def renderSBSAR_NativeDim(sbsar_path, output, out_path):
    renderpipe = subprocess.check_output('{renderer} render \
                                            --inputs {inputs} \
                                            --input-graph-output {output} \
                                            --output-path {out_path} \
                                            --output-name {out_name} \
                                            --engine "d3d10pc" \
                                            --output-format tga'.format(renderer = SBSRENDER,
                                                                        inputs = sbsar_path,
                                                                        output = output,
                                                                        out_path = out_path,
                                                                        out_name = '{inputGraphUrl}_{outputNodeName}'))
    for line in renderpipe.split('\n'):
        print line,

#===============================================================================
# EXCEPTIONS
#===============================================================================
class SBSToolsError(Exception):
    r"""Base class for exceptions for objlibtools."""
    pass

class SBS_MissingElementError(SBSToolsError):
    r"""Failed to find some element in an sbs file."""
    def __init__(self, find_str, elem):
        self.find_str = find_str
        self.elem = elem
                   
    def __str__(self):
        return "Failed to find {} in {}.".format(self.find_str, self.elem.tag)
    

class SBS_CorruptFileError(SBSToolsError):
    r"""Could not find file."""
    def __init__(self, fpn):
        self.fpn = fpn
                   
    def __str__(self):
        return "Corrupt file- {}.".format(self.fpn)

class SBS_CopyGraphError(SBSToolsError):
    r"""Could not copy graph."""
    def __init__(self, fpn_src, fpn_trg, graph_nm):
        self.fpn_src = fpn_src
        self.fpn_trg = fpn_trg
        self.graph_nm = graph_nm
                   
    def __str__(self):
        return "Could not copy graph, {graph_nm}, from {fpn_src} to {fpn_trg}.  "\
                "Graph might already exist in target file or be missing from source file".format(graph_nm = self.graph_nm,
                                                                                                 fpn_src = self.fpn_src,
                                                                                                 fpn_trg = self.fpn_trg)

class SBS_MissingFileError(SBSToolsError):
    r"""Could not find file."""
    def __init__(self, fpn):
        self.fpn = fpn
                   
    def __str__(self):
        return "Could find file - {}.".format(self.fpn)

class SBS_IOError(SBSToolsError):
    r"""Could not write to file (locked?)."""
    def __init__(self, fpn):
        self.fpn = fpn
                   
    def __str__(self):
        return "Could not write to file - {} - (locked?).".format(self.fpn)


class SBS_SetMapError(SBSToolsError):
    r"""Could not set map."""
    def __init__(self, maptype, msg):
        self.maptype = maptype
        self.msg = msg
            
    def __str__(self):
        return "Failed to set {maptype} - {msg}".format(self.maptype, self.msg)

class SBS_SetModelError(SBSToolsError):
    r"""Could not set model."""
    def __init__(self, msg):
        self.msg = msg
            
    def __str__(self):
        return "Failed to set model - {msg}".format(self.msg)

class SBS_MissingAssetError(SBSToolsError):
    r"""An asset is missing."""
    def __init__(self, atype, dir):
        self.atype = atype
        self.dir = dir
    
    def __str__(self):
        return "Missing {atype} in {dir}".format(self.atype, self.dir)

class SBS_DuplicateAssetError(SBSToolsError):
    r"""Multiple assets of same type."""
    def __init__(self, atype, a_ls):
        self.atype = atype
        self.a_ls = a_ls
    
    def __str__(self):
        return "Multiple assets of {} found: \n\t{}".format(self.atype, '\n\t'.join(self.a_ls))

#===============================================================================
# DRIVER
#===============================================================================

if __name__ == '__main__':
    """
    import printtools as pt
    outputs = ['D','Nx','RMAE','colorchoices']
    collections = [r"C:\Leviathan\src\texture_library\costumes\StarIndustries\Assault\Energy\Star_Aslt_Enrg_MWaveCannon\_SBS\Star_Aslt_Enrg_MWaveCannon_Body_Taiga_Collection.sbsar",
                   r"C:\Leviathan\src\texture_library\costumes\StarIndustries\Assault\Mech\Star_Aslt_Mech_Gryphon\_SBS\Star_Aslt_Mech_Gryphon_lower_Taiga_collection.sbsar",
                   r"C:\Leviathan\src\texture_library\costumes\StarIndustries\Assault\Mech\Star_Aslt_Mech_Gryphon\_SBS\Star_Aslt_Mech_Gryphon_upper_Taiga_collection.sbsar",
                   r"C:\Leviathan\src\texture_library\costumes\StarIndustries\Assault\Missile\Star_Aslt_Msl_KilotonSalvo\_SBS\Star_Aslt_Msl_KilotonSalvo_Body_Taiga_Collection.sbsar",
                   r"C:\Leviathan\src\texture_library\costumes\StarIndustries\Scout\Mech\Star_Scout_Mech_Satyr\_SBS\star_scout_mech_satyr_lower_taiga_collection.sbsar",
                   r"C:\Leviathan\src\texture_library\costumes\StarIndustries\Scout\Mech\Star_Scout_Mech_Satyr\_SBS\star_scout_mech_satyr_upper_taiga_collection.sbsar",
                   r"C:\Leviathan\src\texture_library\costumes\Sforza\Gnr\Tank\_SBS\sfrz_gnr_tank_beatrice_body_taiga_collection.sbsar",
                   r"C:\Leviathan\src\texture_library\costumes\StarIndustries\Assault\Ballistic\Star_Aslt_Blst_MachineGun\_SBS\Star_Aslt_Blst_MachineGun_Body_Taiga_Collection.sbsar",
                   r"C:\Leviathan\src\texture_library\costumes\StarIndustries\Assault\Energy\Star_Aslt_Enrg_Blaster\_SBS\Star_Aslt_Enrg_Blaster_Body_Taiga_Collection.sbsar"]
    for sbsar_path in collections:
        out_path = '\\'.join(sbsar_path.split('\\')[:-2])
        for output in outputs: 
            renderSBSAR_NativeDim(sbsar_path, output, out_path)
    """
    sbs_fpn_from = r"C:\Leviathan\src\texture_library\costumes\StarIndustries\Skins\Mil_Galaxy_Skin.sbs"
    sbs_fpn_to = r"C:\Leviathan\src\texture_library\costumes\military\Skins\Mil_Galaxy_Skin.sbs"
    old_graph_name = "Star_Taiga_Skin"
    new_graph_name = "Mil_Galaxy_Skin"
    root_path = "C:/Leviathan/Src/"
    moveGraph(sbs_fpn_from, sbs_fpn_to, old_graph_name, new_graph_name, root_path)
    