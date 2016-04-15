'''
Created on Jan 14, 2013

A collection of utilities used for parsing strings and files.

Classes:
TokenStyle           -- A set of rules for parsing a token as passed to parsetokens().
Node                 -- Simple node that has one parent, children, key, depth.
Node_Acyc            -- Simple node that has parents and children.

Functions:
str_tokenize_clean() -- Tokenize a string for parsing.
parselines()         -- Parse a list of lines containing block definitions and return a node tree.
parsetoken()         -- Parse a list of lines for token values and return a list of values.
parsetokens()        -- Parse a list of lines for token value pairs and return a {'token':['value',..],..}
parsetokens_nested() -- Parse for tokens nested within other tokens and return a dictionary.
parsetoken_file()    -- Parse file and return a list of token values that follow token using token_style rules.
parsetoken_files()   -- Parse files and return a {filename : [values,..],..}
parseblocks()        -- Parse blocks from lines, and return lines
stripblocks()        -- Strip blocks from lines, and return lines

Exceptions:
ParserToolsError     -- Base class for exceptions in parsertools module.
QuoteMismatchError   -- Exception raised for methods parsing lines with quotes encountering a mismatch.

@author: dkorkh
'''
import lowtils as lt
import fileTools as ft

#===============================================================================
# CLASSES
#===============================================================================
class TokenStyle(object):
    r"""A set of rules for parsing a token as passed to parsetokens().
    
    Arguments:
    token      -- If line starts with this token it's searched for a value.
    valindex   -- The order of the value in the tokenized string. (default 1)
                  e.g. A valueindex 2 would return "othervalue" from line
                  "token somevalue othervalue".
    sep        -- Any character in sep is used to split the line into tokens.
                  Consequitive splits are considered as one. (default ' \t\n')
    splits     -- At most this many splits will be made.  -1 will make every
                  possible split. (default -1)
    """
    def __init__(self,
                 token,
                 valindex=1,
                 sep=' \t\n',
                 splits= -1):
        self.token = token
        self.valindex = valindex
        self.sep = sep if sep else ' \t\n' #protect from none
        self.splits = splits
    
    def __str__(self):
        return '{!r}:{!r},{!r},{!r}'.format(self.token, self.valindex, self.sep, self.splits)
    
    def __repr__(self):
        return '{!r}:{!r},{!r},{!r}'.format(self.token, self.valindex, self.sep, self.splits)
    
class Node(object):
    r"""Simple node that has one parent, children, key, depth."""
    def __init__(self, key):
        self.parent = None
        self.children = []
        self.key = key
        self.depth = 0
        self.parseDepth = 0
        
    def addChild(self, node_object):
        '''Add a child node and set it's parent to self.'''
        self.children.append(node_object)
        node_object.setParent(self)
    
    def setParent(self, node_object):
        '''Set the parent node to node.'''
        self.parent = node_object
        self.depth = self.parent.depth + 1
    
    def getDescendants(self):
        '''Return all nodes below this one.'''
        retlist = []
        for child in self.children:
            retlist += [child] + child.getDescendants()
        return retlist
    
    def getAncestors(self):
        '''Return all nodes above this one.'''
        retlist = []
        if self.parent:
            retlist += [self.parent] + self.parent.getAncestors()
    
    def __str__(self):
        return '{}{}\n{}'.format('\t' * self.depth,
                                self.key,
                                '\n'.join([str(child) for child in self.children]))

class Node_Acyc(object):
    '''Simple node that can have some parents and some children.'''
    def __init__(self, key):
        self.parents = []
        self.children = []
        self.key = key
        self.depth = 0
        self.parseDepth = 0
        
    def addChild(self, node_object):
        '''Add a child node and set it's parent to self.'''
        self.children.append(node_object)
        node_object.addParent(self)
    
    def addParent(self, node_object):
        '''Set the parent node to node.'''
        self.parents.append(node_object)
        self.depth = max([x.depth for x in self.parents]) + 1
    
    def getDescendants(self):
        '''Return all nodes below this one.'''
        retlist = []
        for child in self.children:
            retlist += [child] + child.getDescendants()
        return retlist
    
    def getAncestors(self):
        '''Return all nodes above this one.'''
        retlist = []
        for parent in self.parents:
            retlist += [parent] + parent.getAncestors()
        return retlist

#===============================================================================
# FUNCTIONS
#===============================================================================
def str_tokenize_clean(s, sep=' \t\n', splits= -1, splitquotes=False, preservecase=False, stripquotes=True):
    r"""Split line and return a list[str,..] of tokens, lowercase, stripped of ws and quotes.
    
    Keyword arguments:
    sep          -- Any character in sep will be used to split the line.  Consecutive splits
                    are treated as one split so no empty tokens are returned. (default ' \t\n')
    splits       -- The string will be split at most this many times.  If -1, all possible
                    splits are made. (default -1)
    splitquotes  -- If True, parts will be split even if parts are in quotes.  If False,
                    parts in quotes will not be split. (default False)
    preservecase -- If True, the token capitalization is as found.  Not recommended.
    stripquotes  -- If True, quotes are stripped from the tokens returned. (default True)
    
    If splitquotes is False and the string has an odd number of quotes, a QuoteMismatchError
    is raised.
    """
    WORD, TOKENS, SPLITSMADE, INDEX, STRING, SEP, SPLITS, QUOTE, COMMENT = 1, 2, 3, 4, 5, 6, 7, 8, 9
    r = {WORD        : '',
         TOKENS      : [],
         SPLITSMADE  : 0,
         INDEX       : 0,
         STRING      : s,
         SEP         : sep if sep else ' \t\n', #protect from None
         SPLITS      : splits,
         QUOTE       : '\"' if not splitquotes else ''}
    def enterWord():
        while r[INDEX] < len(r[STRING])        \
        and r[STRING][r[INDEX]] != r[QUOTE]    \
        and not r[STRING][r[INDEX]] in r[SEP]:
            r[WORD] += r[STRING][r[INDEX]]
            r[INDEX] += 1
        r[TOKENS].append(r[WORD])
        r[WORD] = ''
        r[SPLITSMADE] += 1
        enterSpace()
    def enterQuote():
        r[WORD] += r[STRING][r[INDEX]]
        r[INDEX] += 1
        if r[INDEX] == len(r[STRING]):
                raise QuoteMismatchError(r[STRING])
        while r[STRING][r[INDEX]] != r[QUOTE]:
            r[WORD] += r[STRING][r[INDEX]]
            r[INDEX] += 1
            if r[INDEX] == len(r[STRING]):
                raise QuoteMismatchError(r[STRING])
        r[WORD] += r[STRING][r[INDEX]]
        r[INDEX] += 1
        r[TOKENS].append(r[WORD])
        r[WORD] = ''
        r[SPLITSMADE] += 1
        enterSpace()
    def enterSpace():
        while r[INDEX] < len(r[STRING]) \
        and r[STRING][r[INDEX]] in r[SEP]:
            r[INDEX] += 1

    while r[INDEX] < len(r[STRING]) \
    and r[STRING][r[INDEX]]         \
    and r[SPLITSMADE] != r[SPLITS]:            
        if r[STRING][r[INDEX]] in r[SEP]:
            enterSpace()
            continue
        if r[STRING][r[INDEX]] == r[QUOTE]:
            enterQuote()
            continue
        else:
            enterWord()
            continue
    if r[INDEX] < len(r[STRING]):
        while r[INDEX] < len(r[STRING]):
            r[WORD] += r[STRING][r[INDEX]]
            r[INDEX] += 1
        r[TOKENS].append(r[WORD])
        r[WORD] = ''
        r[SPLITSMADE] += 1
    return lt.list_str_clean(r[TOKENS], preservecase=preservecase, stripquotes=stripquotes)

def parsetoken(lines, token_style, preservecase=False, stripquotes=True):
    """Parse a list of lines for token value pairs and return a list of values.
    
    Keyword arguments:
    token        -- the token to parse
    valindex     -- the index of the target value from the split, default 1
    sep          -- character to use for splitting the line
    splits       -- number of splits to make, default -1 is every possible split
    preservecase -- False returns lowercase tokens, default is False
    stripquotes  -- If True, quotes are stripped from tokens. (default True)"""
    quote = '\"' if stripquotes else ''
    retlist = []
    for line in lines:
        if len(line.strip()) == 0:
            continue
        line_tk = str_tokenize_clean(line,
                                     token_style.sep,
                                     token_style.splits,
                                     preservecase=preservecase,
                                     stripquotes=stripquotes)
        if line_tk[0].lower() == token_style.token.lower():
            retlist.append(line_tk[token_style.valindex].strip(' \t\n' + quote))
    return retlist

def parsetokens(lines, token_styles, preservecase=False):
    r"""Parse a list of lines for token value pairs and return a {'token':['value',..],..}
    
    Arguments:
    lines -- A list of strings to parse.
        
    Keyword arguments:
    token_styles   -- A list of TokenStyle objects to use for parsing tokens.
    preserve_case  -- If False, the tokens returned are lowercase, False by default.
    """
    retdict = {}
    firstletters = map(lambda x: x.token[0], token_styles) #get the first character of each token to speed things up
    for token_style in token_styles:
        retdict[token_style.token] = []
    for line in lines:
        line = line.strip()
        comment_i = line.find('#')
        comment_i = comment_i if comment_i != -1 else len(line)
        line = line[:comment_i]
        if len(line) == 0 or not line[0].lower() in firstletters:
            continue
        for token_style in token_styles:
            line_tk = str_tokenize_clean(line,
                                         token_style.sep,
                                         token_style.splits,
                                         preservecase=preservecase)
            if line_tk[0].lower() == token_style.token.lower():
                retdict[token_style.token].append(line_tk[token_style.valindex])
                break
    if not preservecase:
        for k in retdict.keys():
            retdict[k] = map(lambda x: x.lower(), retdict[k])
    return retdict

def parsetokens_nested(lines, def_token, attr_tokens, mode=0):
    '''Return nested token values as detected sequentially from the tokentree built using token keys.
    mode: 0 - defs get unique id's from the value following the def token
    mode: 1 - defs get uniqe id's from the first attr_tokens value'''
    attr_tokens = lt.list_str_tolower(attr_tokens)
    def_token = def_token.lower()
    def flush_attr_buffer(attr_buffer):
        for attr in attr_buffer.keys():
            attr_buffer[attr] = []
    retdict = {}
    def_buffer = None
    attr_buffer = dict().fromkeys(attr_tokens)
    flush_attr_buffer(attr_buffer)
    for line in lines:
        tk_line = str_tokenize_clean(line, splits=1)
        if len(tk_line) == 0:
            continue
        if tk_line[0] == def_token:
            if mode == 0:
                if def_buffer:
                    if def_buffer in retdict:   #add to existing defs values
                        for k, v in attr_buffer.items():
                            if not k in retdict[def_buffer]:
                                retdict[def_buffer] = []
                            retdict[def_buffer][k] += v
                    else:    
                        retdict[def_buffer] = dict(attr_buffer.items())
                flush_attr_buffer(attr_buffer)
                def_buffer = tk_line[1]
            elif mode == 1:
                if len(attr_buffer[attr_tokens[0]]):
                    retdict[attr_buffer[attr_tokens[0]][0]] = dict(attr_buffer.items())
                flush_attr_buffer(attr_buffer)
            continue
        if tk_line[0] in attr_buffer.keys():
            attr_buffer[tk_line[0]].append(tk_line[1])
    if mode == 0:
        retdict[def_buffer] = dict(attr_buffer.items())
    elif mode == 1:
        if len(attr_buffer[attr_tokens[0]]):
                    retdict[attr_buffer[attr_tokens[0]][0]] = dict(attr_buffer.items())
    return retdict

def parsetoken_file(file_path, token_style, preservecase=False):
    '''Parse file and return a list of token values that follow token using token_style rules.'''
    f_lines = ft.readFile(file_path)
    return parsetoken(f_lines, token_style, preservecase)

def parsetoken_files(file_list, token_style, preservecase=False):
    '''Parse files and return a {filename : [values,..],..}'''
    file_dict = ft.groupFilesByNameFlat(file_list)
    for path in file_dict.values():
        file_dict[path] = parsetoken_file(path, token_style, preservecase)
    return file_dict

def parsetokens_files(file_list, token_styles, preservecase=False, progress_object=None):
    r"""Return a nested {file:{token_key:[value,..]},..} dictionary for tokens from files.
    
    Arguments:
    file_list    -- A list of files to parse.
    token_styles -- TokenStyle objects to use for parsing rules.
    
    Keyword arguments:
    preservecase    -- If True, will return values as found otherwise lowercase. (default False) 
    progress_object -- An optional object to display progress. Must have a reset(maxcount)
                       method thats run before the loop and an update() method that gets called
                       every iteration."""
    retdict = {}
    if progress_object:
        progress_object.reset('parsetokens_files', len(file_list))
    for path in file_list:
        lines = ft.readFile(path)
        token_dict = parsetokens(lines, token_styles=token_styles, preservecase=preservecase)
        retdict[path] = token_dict
        if progress_object:
            progress_object.update()
    return retdict

def parselines(lines,
              rootNode,
              f_onExit=lambda line, inNode, blockDepth: None,
              f_onEnter=lambda line, inNode, blockDepth: None,
              f_stepIn=lambda line, inNode, blockDepth: None,
              f_stepOut=lambda line, inNode, blockDepth: None,
              f_enterBlock=lambda line, inNode, blockDepth: 0,
              f_exitBlock=lambda line, inNode, blockDepth: 0,
              f_enterKeyBlock=lambda line, inNode, blockDepth: None,
              f_exitKeyBlock=lambda line, inNode, blockDepth: None,
              f_update=lambda line, inNode, blockDepth: None,
              f_other=lambda line, inNode, blockDepth: None):
    '''Parse a list of lines containing block definitions and return a node tree.
    all functions should accept (line, currentNode, blockdepth) as parameters. Lines with only white
    space get ignored except for the call to f_update.
        lines            : a list of strings to parse
        rootNode         : root tree node, must have key<str>, parent<node>, children<node list>
        f_onExit         : function called on exiting any block
        f_onEnter        : function called on entering any block
        f_stepIn         : function called on entering a key block - returned node will become inNode
        f_stepOut        : function called on exiting a key block - returned node will become inNode
        f_enterBlock     : function takes a line and current node and returns 1 if entering new block, 0 otherwise
        f_exitBlock      : function takes a line and current node and returns -1 if exiting a block, 0 otherwise
        f_enterKeyBlock  : function called on entering new block and returns True/False if the block is a key block
        f_exitKeyBlock   : function called on exiting a new block and returns True/False if the block is a key block
        f_update         : function called at the beginning of every cycle with the line as is.
        f_other          : function called at the end of the cycle if it's neither block start or end.
    '''
    blockDepth = 0  #blockDepth is incremented/decremented by enter/exit block.
    inBlock = 0  #inBlock is the last block depth level, > depth means exited, < depth means entered
    inNode = rootNode
    line_num = 0
    for line in lines:
        line_num += 1
        f_update(line, inNode, blockDepth)
        if not line.strip():
            continue
        blockDepth += f_enterBlock(line, inNode, blockDepth)
        if inBlock < blockDepth:
            inBlock = blockDepth
            f_onEnter(line, inNode, blockDepth)
            if f_enterKeyBlock(line, inNode, blockDepth):
                inNode = f_stepIn(line, inNode, blockDepth)
            continue
        blockDepth += f_exitBlock(line, inNode, blockDepth)
        if inBlock > blockDepth:
            inBlock = blockDepth
            f_onExit(line, inNode, blockDepth)
            if f_exitKeyBlock(line, inNode, blockDepth):
                inNode = f_stepOut(line, inNode, blockDepth)
                if inNode == None:
                    break
            continue
        f_other(line, inNode, blockDepth)
    return rootNode

def stripblocks(lines, fn_blockid, fn_blockenter, fn_blockexit):
    '''Return lines stripped from blocks identified by fn_blockid, from line
    where fn_blockenter increments an integer to where fn_blockexit decrements it
    to 0.'''
    new_lines = []
    inblock = 0
    lookforentry = 0
    for line in lines:
        if fn_blockid(line):
            lookforentry = 1
        if lookforentry:
            inblock += fn_blockenter(line)
            lookforentry = 0
            continue
        if inblock:
            inblock += fn_blockexit(line)
            continue
        new_lines.append(line)
    return new_lines

def parseblocks(lines, fn_blockid, fn_blockenter, fn_blockexit, rootNode):
    '''Parse block style tokens from lines.'''
    new_lines = []
    inblock = 0
    lookforentry = 0
    for line in lines:
        if fn_blockid(line):
            lookforentry = 1
        if lookforentry:
            inblock += fn_blockenter(line)
            lookforentry = 0
            continue
        if inblock:
            inblock += fn_blockexit(line)
            continue
        new_lines.append(line)
    return new_lines

def asyncNodeDict_walkBranch(d, k):
    '''return a list of all children in a node dictionary'''
    retlist = []
    ch_keys = d[k]['children']
    retlist += ch_keys
    for k in ch_keys:      
        retlist += asyncNodeDict_walkBranch(d, k)
    return list(set(retlist))

def asyncNodeDict_climbBranch(d, k):
    '''return a list of all parents in a node dictionary'''
    retlist = []
    ch_keys = d[k]['parents']
    retlist += ch_keys
    for k in ch_keys:      
        retlist += asyncNodeDict_climbBranch(d, k)
    return list(set(retlist))

def asyncNodeDict_map(main_dict, add_dict):
    '''map the associations in add_dict to main_dict'''
    for k, v in add_dict.items():
        if not k in main_dict:
            main_dict[k] = {'children' : [],
                             'parents' : [],
                             'model' : None,
                             'path'  : None,
                             'key'  : k}
        main_dict[k]['children'] += v['children']
        main_dict[k]['children'] = list(set(main_dict[k]['children']))
        main_dict[k]['parents'] += v['parents']
        main_dict[k]['parents'] = list(set(main_dict[k]['parents']))
        if v['model']:
            main_dict[k]['model'] = v['model']
        if v['path']:
            main_dict[k]['path'] = v['path']
            
def collecttoken_set(token_ls, f_istoken):
    r"""Return a set of tokens in token_ls for which f_istoken(s) returns true."""
    ret_set = set()
    for token in ret_set:
        if f_istoken(token):
            ret_set.add(token)
    return ret_set
#===============================================================================
# EXCEPTIONS
#===============================================================================
class ParserToolsError(Exception):
    r"""Base class for exceptions in parsertools module."""
    pass

class QuoteMismatchError(ParserToolsError):
    r"""Exception raised for methods parsing lines with quotes encountering a mismatch.
    
    Arguments:
    line  -- The string in which the quotes are mismatched.
    """
    def __init__(self, line):
        self.line = line

    def __str__(self):
        return "Expected matching quotes in line: {}".format(self.line)
    
