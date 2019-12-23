from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtGui import QTextCharFormat,QFont
from lxml import etree
from bs4 import BeautifulSoup
import os
from datetime import datetime
import urllib.parse

class dersArsiv(QDialog):
    def __init__(self, ctx):
        global debug
        super(dersArsiv, self).__init__()
        self.ctx = ctx
        uic.loadUi(self.ctx.get_resource('dersArsiv.ui'), self)
        debug = self.ctx.debug
        os.makedirs(self.ctx.anaKlasor + '\\arsiv', exist_ok=True)
