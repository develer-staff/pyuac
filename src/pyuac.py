#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Copyright 2006 Develer S.r.l. (http://www.develer.com/)
# All rights reserved.
#
# $Id:$
#
# Author: Matteo Bertini <naufraghi@develer.com>

import sys
from PyQt4 import uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *

try:
    from xml.etree import ElementTree as ET
except ImportError:
    try:
        from elementtree import ElementTree as ET
    except ImportError:
        raise ImportError, "ElementTree (or py2.5) needed"

from QRemoteTimereg import RemoteTimereg

import logging
log = logging.getLogger("pyuac.gui")

def debug(msg):
    if __debug__:
        msg = "#-#-# "+msg.replace(r"%%", r"%").replace(r"%", r"%%")
        qDebug(msg)
        log.debug(msg)

class TimeregApplication(QApplication):
    def __init__(self, args):
        QApplication.__init__(self, args)
        win = TimeBrowseWindow("http://www.develer.com/~naufraghi/achievo/",
                               "matteo", "matteo99")
        win.show()
        sys.exit(self.exec_())

class TimeBrowseWindow(QMainWindow):
    def __init__(self, achievouri, user, password):
        QMainWindow.__init__(self)
        self.auth = [achievouri, user, password]
        self.ui = uic.loadUi("pyuac_browse.ui", self)
        self.edit = TimeregWindow("http://www.develer.com/~naufraghi/achievo/",
                                  "matteo", "matteo99", parent=self)
        self.rt = RemoteTimereg(self, self.auth)
        self.err = QErrorMessage(self)

        self.projects = []
        self._connectSlots()
        self._setupGui()

    def _setupGui(self):
        self.ui.tableTimereg.setColumnCount(5)
        for c, head in enumerate("Date Project/Phase Activity Remark Time".split()):
            cellHead = QTableWidgetItem(head)
            self.ui.tableTimereg.setHorizontalHeaderItem(c, cellHead)
        self.ui.dateEdit.setDateTime(QDateTime.currentDateTime())
    
    def _connectSlots(self):
        self.connect(self.ui.btnTimereg, SIGNAL("clicked()"),
                     self._timereg)
        self.connect(self.ui.btnQuit, SIGNAL("clicked()"),
                     self.ui.close)
        self.connect(self.ui.btnToday, SIGNAL("clicked()"),
                     self._setupGui)
        self.connect(self.ui.dateEdit, SIGNAL("dateChanged(const QDate&)"),
                     self._timereport)
        self.connect(self.rt, SIGNAL("timereportDone(PyObject *)"),
                     self._updateTimereport)
        self.connect(self.edit, SIGNAL("registrationDone()"),
                     self._setupGui)
        self.connect(self.ui.tableTimereg, SIGNAL("cellDoubleClicked(int,int)"),
                     self._timeedit)

    def _timereg(self):
        self.edit.show()
        
    def _timeedit(self, row, column):
        project = self.projects[row]
        self.edit.edit(project)
        self.edit.show()

    def _timereport(self, qdate):
        reportdate = qdate.toString("yyyyMMdd")
        self.rt.timereport(date=reportdate)

    def _updateTimereport(self, projects):
        self.projects = list(projects)
        self.ui.tableTimereg.setRowCount(len(projects))
        for r, p in enumerate(projects):
            row = []
            row.append(QTableWidgetItem(p.get("activitydate")))
            row.append(QTableWidgetItem("%(project_name)s / %(phase_name)s" %\
                                        dict(p.items())))
            row.append(QTableWidgetItem(p.get("activity_name")))
            row.append(QTableWidgetItem(p.get("remark")))
            hmtime = "%02d:%02d" % (int(p.get("time"))/60, int(p.get("time")) % 60)
            p.set("hmtime", hmtime)
            row.append(QTableWidgetItem(hmtime))
            for c, cell in enumerate(row):
                self.ui.tableTimereg.setItem(r, c, cell)

class TimeregWindow(QMainWindow):
    def __init__(self, achievouri, user, password, parent=None):
        QMainWindow.__init__(self, parent)
        self.auth = [achievouri, user, password]
        self.baseproject = None
        self.ui = uic.loadUi("pyuac_edit.ui", self)
        self.rt = RemoteTimereg(self, self.auth)
        self.err = QErrorMessage(self)
        
        self.projects = []
        self.allProjects = []
        self._connectSlots()
        self._setupGui()

    def _setupGui(self):
        self.ui.dateTimeregDate.setDate(QDate.currentDate())
        self.ui.comboTimeWorked.clear()
        for hour in range(24):
            for quarter in range(4):
                if hour + quarter > 0:
                    htext = "%02d:%02d" % (hour, 15*quarter)
                    self.ui.comboTimeWorked.addItem(htext)
        self.ui.labelExactTime.setText("00:00")
        #fino a quando non sarà attiva la gestione delle modifiche...
        [i.setEnabled(False) for i in (self.ui.txtRemark,
                                       self.ui.btnSave)]
        self.ui.setWindowTitle("Time Registration - %s" % self.auth[1])
        self.ui.txtRemark.setPlainText("")
        self.ui.comboSmartQuery.lineEdit().setText("")
        self.ui.comboSmartQuery.lineEdit().setFocus()
        self._smartQueryChanged("")
 
    def _connectSlots(self):
        self.connect(self.ui.comboSmartQuery, SIGNAL("editTextChanged(QString)"),
                     self._smartQueryChanged)
        self.connect(self.ui.btnSave, SIGNAL("clicked()"),
                     self.timereg)
        self.connect(self.rt, SIGNAL("searchStarted()"),
                     self._searchStarted)
        self.connect(self.rt, SIGNAL("searchDone(PyObject *)"),
                     self._projectsChanged)
        self.connect(self.rt, SIGNAL("timeregStarted()"),
                     self._timeregStarted)
        self.connect(self.rt, SIGNAL("timeregDone()"),
                     self._timeregDone)
        self.connect(self.rt, SIGNAL("timeregError()"),
                     self._timeregError)
        self.connect(self.rt, SIGNAL("processError(int)"),
                     self._processError)
        self.connect(self.ui.comboProjectPhase, SIGNAL("activated(const QString&)"),
                     self._comboProjectPhaseActivated)
        self.connect(self.ui.comboActivity, SIGNAL("activated(const QString&)"),
                     self._comboActivityActivated)
        self.connect(self.ui.comboTimeWorked, SIGNAL("activated(const QString&)"),
                     self._comboTimeWorkedActivated)

    def _smartQueryChanged(self, smartquery):
        debug("-------> pre search")
        smartquery = "%"+unicode(smartquery)
        self.rt.search(smartquery)
        debug("-------> post search")
                      
    def _projectsChanged(self, projects):
        debug("_projectsChanged %s" % len(projects))
        if len(self.allProjects) < len(projects):
            #TODO: mettere in un init, qua ci entro solo alla prima query con %
            self.allProjects = list(projects) #mi stacco dall'oggetto originale
        self.projects = list(projects)

        # ---- Update comboboxes ----
        self.ui.comboProjectPhase.clear()
        self.ui.comboActivity.clear()
        projphases = set()
        activities = set()
        for p in self.allProjects:
            projphases.add("%(project_name)s / %(phase_name)s" % dict(p.items()))
            activities.add(p.get("activity_name"))
        self.ui.comboProjectPhase.addItems(list(projphases))
        self.ui.comboActivity.addItems(list(activities))
        # ^^^^ Update comboboxes ^^^^

        if len(self.projects) == 1:
            p = self.projects[0]
            
            projectphase = "%(project_name)s / %(phase_name)s" % dict(p.items())
            id = self.ui.comboProjectPhase.findText(projectphase)
            self.ui.comboProjectPhase.setCurrentIndex(id)

            id = self.ui.comboActivity.findText(p.get("activity_name"))
            self.ui.comboActivity.setCurrentIndex(id)
            
            id = self.ui.comboTimeWorked.findText(p.get("hmtime"))
            self.ui.comboTimeWorked.setCurrentIndex(id)

            self.ui.labelExactTime.setText(p.get("input_hours") or "00:00")
            self.ui.txtRemark.setPlainText(p.get("remark"))
            self.ui.labelTimeWorked.setEnabled(p.get("hmtime") != "00:00")
            self.ui.labelRemark.setEnabled(p.get("remark") != "")
            self.ui.btnSave.setEnabled(p.get("hmtime") != "00:00" and p.get("remark") != "")
            self.ui.labelProjectPhase.setEnabled(True)
            self.ui.labelActivity.setEnabled(True)
        else:
            self.ui.txtRemark.setPlainText("")
            self.ui.labelProjectPhase.setEnabled(False)
            self.ui.labelActivity.setEnabled(False)
            self.ui.labelTimeWorked.setEnabled(False)
            self.ui.labelRemark.setEnabled(False)
            self.ui.btnSave.setEnabled(False)
 
    def _timeregStarted(self):
        debug("_timeregStarted")
    
    def _timeregDone(self):
        debug("_timeregDone")
        self._setupGui()
        self.emit(SIGNAL("registrationDone()"))
        self.baseproject = None
        self.ui.close()

    def _timeregError(self):
        debug("_timeregError")

    def _searchStarted(self):
        debug("_searchStarted")

    def _processError(self, int):
        debug("_processError %s" % int)
        self.err.showMessage("Errore nell'avviare il processo interfaccia con Archievo.")
     
    def _comboProjectPhaseActivated(self, combotext):
        #TODO: fattorizzare in qualche modo questi 3
        origtext = unicode(self.ui.comboSmartQuery.lineEdit().text())
        origlist = origtext.split(" ", 4)
        while len(origlist) < 5:
            origlist.append("")
        newproj, newpha = unicode(combotext).split("/")
        origlist[0] = newproj.strip()
        origlist[1] = newpha.strip()
        self.ui.comboSmartQuery.setEditText(" ".join(origlist).strip()+" ")
    
    def _comboActivityActivated(self, combotext):
        origtext = unicode(self.ui.comboSmartQuery.lineEdit().text())
        origlist = origtext.split(" ", 4)
        while len(origlist) < 5:
            origlist.append("")
        newact = unicode(combotext)
        origlist[2] = newact.strip()
        self.ui.comboSmartQuery.setEditText(" ".join(origlist).strip()+" ")

    def _comboTimeWorkedActivated(self, combotext):
        origtext = unicode(self.ui.comboSmartQuery.lineEdit().text())
        origlist = origtext.split(" ", 4)
        while len(origlist) < 5:
            origlist.append("")
        newact = unicode(combotext)
        origlist[3] = newact.strip()
        self.ui.comboSmartQuery.setEditText(" ".join(origlist).strip()+" ")        

    def timereg(self):
        p = self.projects[0]
        params = dict([(k, p.get(k)) for k in "projectid phaseid activityid hmtime remark".split()])
        params["activitydate"] = self.ui.dateTimeregDate.date().toString("yyyyMMdd")
        if self.baseproject != None:
            params["id"] = self.baseproject.get("id")
        debug(str(params))
        self.rt.timereg(**params)
        self.ui.setWindowTitle("Time Registration - saving...")
    
    def edit(self, project):
        self.baseproject = project
        smartquery = "%(project_name)s %(phase_name)s %(activity_name)s\
                      %(hmtime)s %(remark)s" % dict(project.items())
        self.ui.comboSmartQuery.setEditText(smartquery) 
        

if __name__ == "__main__":
    app = TimeregApplication(sys.argv)
    #2 m a 2:34 prova prova èàò
