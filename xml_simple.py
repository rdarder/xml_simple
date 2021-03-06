#!/usr/bin/python2

from xml.sax import handler, make_parser
import logging

class const:
  text=1

class xml_tree(handler.ContentHandler):
  def __init__(self):
    self.stack = [('doc', None, [])]
  @property
  def tree(self):
    rootl = self.stack[0][2]
    if len(rootl) < 1:
      return None
    return rootl[0]
  def startDocument(self):
    pass
  def endDocument(self):
    pass
  def startElement(self, name, attrs):
    d = dict(attrs.items())
    d.setdefault(const.text,'')
    self.stack.append((name, d, []))
  def characters(self, s):
    name, attrs, childs = self.stack.pop()
    attrs[const.text] += s
    self.stack.append((name, attrs, childs))
  def endElement(self, name):
    my = self.stack.pop()
    pname, pattrs, siblings = self.stack.pop()
    siblings.append(my)
    self.stack.append((pname, pattrs, siblings))

class xml_collapser(object):
  default_key_attr_keys=['name', 'key', 'id']
  def __init__(self, force_array=[], content_key='content', keep_root=False,
               key_attr=['name', 'key', 'id'], group_tags={}):
    self.force_array = force_array
    #content_key, reduce_content
    if content_key and content_key[0] == '-':
      self.content_key = content_key[1:]
      self.reduce_content = True
    else:
      self.content_key = content_key
      self.reduce_content = False
    #key_attr
    self.key_attr = key_attr
    #group_tags
    self.group_tags = group_tags
    #keep_root
    self.keep_root = keep_root

  def find_key_attr(self, name, sub_tree):
    logging.debug("find key attr for %s", name)
    if sub_tree is None:
      return None, None
    if isinstance(self.key_attr, list): #xxx allow dict list
      candidates = list(self.key_attr)
    elif isinstance(self.key_attr, dict):
      d = self.key_attr.get(name) or self.key_attr.get('default')
      if d is None:
        return None, None
      candidates = d if isinstance(d,list) else [d]
    for cattrs in sub_tree:
      for c in list(candidates):
        if c.lstrip('+') not in cattrs:
          candidates.remove(c)  #XXX maybe use sets
    if candidates == []:
      return None, None
    else:
      if candidates[0] == '+':
        return '+', candidates[0][1:]
      else:
        return None, candidates[0]
  def collapse(self, tree):
    collapsed = self._collapse(tree)
    if self.keep_root:
      return {tree[0]:collapsed}
    else:
      if collapsed:
        return collapsed
      else:
        return {}
  def _collapse(self, tree):
    name, attrs, childs = tree
    if const.text in attrs and len(attrs) == 1 and len(childs) == 0:
      if self.reduce_content:
        return attrs[const.text].strip()
      else:
        return {self.content_key: attrs[const.text].strip()}
    elif const.text in attrs:
      if len(childs) == 0:
        attrs[self.content_key] = attrs[const.text].strip()
      del attrs[const.text]
    for child in childs:
      cname, cattrs, cchilds = child
      if cname in attrs:
        if isinstance(attrs[cname], list):
          attrs[cname].append(self._collapse(child))
        else:
          attrs[cname] = [attrs[cname],self._collapse(child)]
      elif cname in self.force_array:
        logging.debug("forcing array %s", cname)
        to_force = self._collapse(child)
        if isinstance(to_force, list):
          attrs[cname] = to_force
        else:
          attrs[cname] = [to_force]
      else:
        attrs[cname] = self._collapse(child)
    #key_attr processing pass, after force_array
    for aname, aval in attrs.items():
      if isinstance(aval,list):
        copy, key_attr = self.find_key_attr(aname, aval)
        if key_attr is not None:
          logging.debug('key_attr: %s', key_attr)
          d = {}
          for item in aval: #elements in list to be converted into a dict
            d[item[key_attr]] = item
            if not copy:
              del item[key_attr]
            attrs[aname] = d
    #group tags
    if len(attrs) == 1 and name in self.group_tags:
      if self.group_tags[name] in attrs:
        logging.debug('grouping tags %s', name)
        attrs = attrs[self.group_tags[name]]
    return attrs

def xml_in(file, *args, **kwargs):
  collapser = xml_collapser(*args, **kwargs)
  parser = make_parser()
  content = xml_tree()
  parser.setContentHandler(content)
  parser.parse(file)
  t = collapser.collapse(content.tree)
  return t

def list_or_dict_arg(args):
  if ':' not in args[0]:
    return args
  else:
    res = {}
    for arg in args:
      k,v = arg.split(':',2)
      res[k] = v
    return res


if __name__ == '__main__':
  import argparse
  from pprint import pprint

  parser = argparse.ArgumentParser(description='XML simple parser')
  parser.add_argument('-a', '--force-array', nargs='*')
  parser.add_argument('-c', '--content-key')
  parser.add_argument('-r', '--keep-root', action='store_true', default=False)
  parser.add_argument('-g', '--group-tags', nargs='*')
  parser.add_argument('-k', '--key-attr', nargs='*')
  parser.add_argument('file', metavar='file', type=argparse.FileType('r'))
  args = vars(parser.parse_args())

  file = args.pop('file')

  for k,v in args.items():
    if v is None:
      del(args[k])
    elif k in ['key_attr', 'group_tags']:
      args[k] = list_or_dict_arg(args[k])

  doc = xml_in(file, **args)
  pprint(doc)



