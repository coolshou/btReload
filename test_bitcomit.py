#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 31 10:07:06 2017

@author: 10007014
"""

from bitcomit import bitcomit
# main
if __name__ == '__main__':
    
    #p = "D:\中文.txt"
    p = "D:\\中文\\"
    bt = bitcomit("http://127.0.0.1", "12345", "admin", "123456", 60)
    bt.remove(p)