#!/usr/bin/python

import xml_simple

if __name__ == '__main__':
  xml_simple.xml_in('samples/sample1.xml', content_key='value',
                    keep_root=True, force_array=['server', 'address'],
                    key_attr=['name'], group_tags={'servers':'server'})

