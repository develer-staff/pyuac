﻿#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Copyright 2006 Develer S.r.l. (http://www.develer.com/)
# All rights reserved.
#
# $Id: QTimeBrowseWindow.py 21759 2008-06-18 08:42:23Z duplo $
#
# Author: Matteo Bertini <naufraghi@develer.com>
"""
Modulo contenente il codice della MainWindow di pyuac (TimeBrowseWindow), della finestra di login
(LoginDialog) e del menù del toolbutton della MainWindow.
"""

import os, sys
import sip

from collections import defaultdict

from pyuac_utils import *
from QRemoteTimereg import *
from QTimeregWindow import *
from QTimeCalculator import *

class LoginDialog(QDialog, QAchievoWindow):
    """
    Finestra di login di pyuac. Viene lanciata all'avvio del programma per
    raccogliere le credenziali di accesso ad Achievo.
    """

    def __init__(self, parent, config):
        QDialog.__init__(self, parent)
        self.__setup__(_path='pyuac_auth.ui')
        _achievouri = self.settings.value("achievouri", QVariant(config["achievouri"])).toString()
        _username = self.settings.value("username", QVariant(config["username"])).toString()
        self.ui.editAchievoUri.setText(_achievouri)
        self.ui.editUsername.setText(_username)
        self.connect(self.ui, SIGNAL("accepted()"), self.login)
        self.connect(self.ui, SIGNAL("rejected()"), self.cancel)
        self.ui.editPassword.setFocus()
        self.ui.show()

    def login(self):
        """
        Memorizza i valori di achievouri e username in un ASettings e emette il segnale 'login' 
        passando una lista contenente achievouri, username e password (auth) dopodiché nasconde la 
        finestra.
        """
        self.settings.setValue("achievouri", QVariant(self.ui.editAchievoUri.text())) 
        self.settings.setValue("username", QVariant(self.ui.editUsername.text()))
        auth = [self.ui.editAchievoUri.text()]
        auth += [self.ui.editUsername.text()]
        auth += [self.ui.editPassword.text()]
        self.emit(SIGNAL("login"), auth)
        self.ui.editPassword.setText("")
        self.ui.hide()

    def cancel(self):
        """
        Emette il segnale 'cancel' e chiude la finestra di login.
        """
        self.emit(SIGNAL("cancel"))
        self.ui.close()


class TimeBrowseWindow(QMainWindow, QAchievoWindow):
    """
    MainWindow di pyuac, contiene le tabelle con gli orari registrati.
    """
    
    def __init__(self, parent, auth=None, config=None):
        QMainWindow.__init__(self, parent)
        self.projects = None
        self.calculator = None
        self._working_date = None
        if config != None:
            self.login = LoginDialog(self, config)
            self.connect(self.login, SIGNAL("login"), self.__auth__)
            self.connect(self.login, SIGNAL("cancel"), self._slotClose)
        elif auth != None:
            self.__auth__(auth)
        else:
            raise TypeError, "Provide auth or config"

    def __auth__(self, auth):
        """
        Inizializza le componenti grafiche e imposta le variabili di istanza.
        :param auth: lista contenente in ordine achievouri,  username e password.
        """
        self.__setup__(auth, 'pyuac_browse.ui')
        self._mode= ""
        self._setupGui()
        self._connectSlots()
        self.ui.resize(self.settings.value("size",QVariant(self.ui.sizeHint())).toSize())
        self.move(self.settings.value("pos", QVariant(QPoint(200, 200))).toPoint());
        self.ui.show()

    def _connectSlots(self):
        """
        Connette i signal agli slot necessari.
        """
        self.connect(self.remote, SIGNAL("timereportStarted"),
                     self._slotTimereportStarted)
        self.connect(self.remote, SIGNAL("timereportOK"),
                     self._slotUpdateTimereport)
        self.connect(self._menu,  SIGNAL("selected"),
                        self._slotNewTimereg)
        self.connect(self.ui.tlbTimereg,  SIGNAL("clicked()"), 
                        self._slotNewTimereg)
        self.connect(self.ui.btnToday, SIGNAL("clicked()"),
                     lambda: self._changeDate(QDate.currentDate()))
        self.connect(self.ui.btnThisWeek, SIGNAL("clicked()"),
                     lambda: self._changeDate(QDate.currentDate()))
        self.connect(self.ui.btnNext, SIGNAL("clicked()"),
                     lambda: self._changeDateDelta(1))
        self.connect(self.ui.btnPrev, SIGNAL("clicked()"),
                     lambda: self._changeDateDelta(-1))
        self.connect(self.ui.dateEdit, SIGNAL("dateChanged(const QDate&)"),
                     self._slotDateEditChanged)
        self.connect(self.ui.tableTimereg, SIGNAL("cellDoubleClicked(int,int)"),
                     self._slotTimeEdit)
        self.connect(self.ui.tableWeekTimereg, SIGNAL("cellDoubleClicked(int,int)"),
                     self._slotTimeEdit)
        self.connect(self.ui.tableWeekTimereg, SIGNAL("cellClicked(int,int)"),
                     self._slotWeeklyDateChanged)
        self.connect(self.ui.btnDaily, SIGNAL("clicked()"),
                     self._slotChangeToDaily)
        self.connect(self.ui.btnWeekly, SIGNAL("clicked()"),
                     self._slotChangeToWeekly)
        self.connect(self.ui.actionSingleRegistration, SIGNAL("triggered(bool)"),
                     lambda: self._slotNewTimereg("single"))
        self.connect(self.ui.actionRangeRegistration, SIGNAL("triggered(bool)"),
                     lambda: self._slotNewTimereg("range"))
        self.connect(self.ui.actionHoursRegistration, SIGNAL("triggered(bool)"),
                     lambda: self._slotNewTimereg("hours"))
        self.connect(self.ui.actionQuit, SIGNAL("triggered(bool)"),
                     self.ui.close)
        self.connect(self.ui.actionTimeCalculator, SIGNAL("triggered(bool)"),
                     self._slotNewTimeCalculator)
        self.connect(self, SIGNAL("workingDateChanged"),
                     self._slotWorkingDateChanged)

    def _changeDate(self, date):
        """
        Modifica la data della vista corrente a partire da una nuova QDate.
        :param date: QDate contenente la nuova data.
        """
        tmp = self._working_date
        self._working_date = date
        self.emit(SIGNAL("workingDateChanged"), tmp)

    def _changeDateDelta(self, direction):
        """
        Modifica la data a partire dalla data della vista corente e aggiungendo (o rimuovendo) uno 
        (sette) giorni. Questo metodo ha un effetto diverso a seconda della modalità di 
        visualizzazione. In modalità 'daily' permette di raggiungere il giorno precedente o successivo 
        a quello corrente; in modalità 'weekly' permette di scorrere alla settimana precedente o 
        successiva.
        :param direction: intero, può contenere 1 o -1 a seconda che si necessiti di andare avanti o dietro.
        """
        if self._mode == "daily":
            numdays = direction
        elif self._mode == "weekly":
            numdays = 7 * direction
        date = self._working_date
        date = date.addDays(numdays)
        self._changeDate(date)

    def _setupGui(self):
        """
        Reimposta la gui ai volori di default (titoli colonne e data attuale).
        """
        self.ui.tableTimereg.setColumnCount(5)
        for c, head in enumerate(("Date", "Project/Phase", "Activity", "Time", "Remark")):
            cellHead = QTableWidgetItem(head)
            self.ui.tableTimereg.setHorizontalHeaderItem(c, cellHead)
        self.ui.tableTimereg.horizontalHeader().setStretchLastSection(True)
        self.ui.tableWeekTimereg.setColumnCount(7)
        for c in range(7):
            cellHead = QTableWidgetItem()
            self.ui.tableWeekTimereg.setHorizontalHeaderItem(c, cellHead)
            self.ui.tableWeekTimereg.horizontalHeader().setResizeMode(c, QHeaderView.Stretch)
        self._changeDate(QDate.currentDate())
        self._menu = TimeregMenu(self)
        self.ui.tlbTimereg.setMenu(self._menu)
        self._slotChangeToDaily()

    def _slotChangeToWeekly(self):
        """
        Imposta l'interfaccia per lavorare in modalità 'weekly'.
        """
        if self._mode != "weekly":
            self._mode = "weekly"
            self.ui.stackedWidget.setCurrentIndex(1)
            self._slotTimereport(self._working_date)
        self.ui.btnDaily.setChecked(False)
        self.ui.btnWeekly.setChecked(True)
   
    def _slotChangeToDaily(self):
        """
        Imposta l'interfaccia per lavorare in modalità 'daily'.
        """
        if self._mode != "daily":
            self._mode = "daily"
            self.ui.stackedWidget.setCurrentIndex(0)
            self.ui.dateEdit.blockSignals(True)
            self.ui.dateEdit.setDate(self._working_date)
            self.ui.dateEdit.blockSignals(False)
            self._slotTimereport(self._working_date)
        self.ui.btnDaily.setChecked(True)
        self.ui.btnWeekly.setChecked(False)

    def _slotDateEditChanged(self, date):
        tmp = self._working_date
        self._working_date = QDate(date)
        self.emit(SIGNAL("workingDateChanged"), tmp)
    
    def _slotWorkingDateChanged(self, old_date):
        if old_date != self._working_date:
            if self._mode == "daily" or self._mode == "":
                self.ui.dateEdit.blockSignals(True)
                self.ui.dateEdit.setDate(self._working_date)
                self.ui.dateEdit.blockSignals(False)
                self._slotTimereport(self._working_date)
            elif self._mode == "weekly" and not old_date in getweek(self._working_date):
                self._slotTimereport(self._working_date)

    def _slotWeeklyDateChanged(self, row, column):
        tmp = self._working_date
        self._working_date = [date for date in getweek(self._working_date)][column]
        self.emit(SIGNAL("workingDateChanged"), tmp)

    def _createTimeregWindow(self, mode):
        """
        Costruisce una TimeregWindow e la restituisce al chiamante.
        :param mode: modalità di inserimento ore ('single' o 'range').
        """
        editwin = TimeregWindow(self, self.remote.auth, mode)
        self.connect(editwin, SIGNAL("registrationDone"),
                     self._slotRegistrationDone)
        return editwin

    def _slotNewTimereg(self, mode="single"):
        """
        Slot attivato quando viene utilizzato self.ui.tlbTimereg o il menu.
        :param mode: modalità di inserimento ore ('single' o 'range')
        """
        selected_date = unicode(self._working_date.toString("yyyy-MM-dd"))
        project_template = AchievoProject()
        project_template.set("activitydate", selected_date)
        editwin = self._createTimeregWindow(mode)
        editwin.setupEdit(project_template)
        editwin.show()

    def _slotNewTimeCalculator(self):
        if not self.calculator or sip.isdeleted(self.calculator):
            self.calculator = TimeCalculator()
            self.calculator.setAttribute(Qt.WA_DeleteOnClose)
            self.calculator.show()
        else:
            self.calculator.activateWindow()
            self.calculator.raise_()

    def _slotTimeEdit(self, row, column):
        """
        Slot attivato da self.ui.tableTimereg, SIGNAL("cellDoubleClicked(int,int)"). Prepara un 
        template con i dati della riga selezionata ed avvia la form di modifica (modalità 'single').
        :param row: intero, cordinata verticale della cella su cui si è clickato.
        :param column: intero, cordinata orizzontale della della su cui si è clickato.
        """
        #modalità corrente: 'daily'
        if self._mode == "daily":
            project = self.projects[0][row]
        #modalità corrente: 'weekly'
        elif self._mode == "weekly" and column in self.projects.keys() \
                                                and row in self.projects[column].keys():
            project = self.projects[column][row]
        #se si è in modalità 'weekly' e si doppioclicka su una cella vuota il programma
        #avvia la registrazione nella data corrente.
        else:
            self._slotWeeklyDateChanged(row, column)
            project = AchievoProject()
            project.set("activitydate", self._working_date.toString("yyyy-MM-dd"))
        #viene creata la TimeregWindow in modalità 'single'
        editwin = self._createTimeregWindow("single")
        #vengono impostati tutti i campi della TimeregWindow con i valori della registrazione corrente
        editwin.setupEdit(self._createProjectTemplate(project))
        editwin.show()

    def _createProjectTemplate(self, project):
        """
        Crea e restituisce un AchievoProject contenente le chiavi e i valori del progetto passato 
        come parametro.
        :param project: AchievoProject contenente una sola registrazione di ore.
        """
        project_template = AchievoProject()
        for k in project_template.keys:
            project_template.set("in_%s" % k, project.get(k))
        for k in ("id",  "activitydate"):
            project_template.set(k, project.get(k))
        return project_template

    def _slotRegistrationDone(self, eresp):
        """
        Slot attivato da editwin, SIGNAL("registrationDone"). Fa il refresh della vista dopo il nuovo
        inserimento.
        :param eresp: ElementTree, contiene la risposta del server all'inserimento ore appena terminato.
        """
        newdate = QDate.fromString(str(eresp.get("activitydate")), "yyyy-MM-dd")
        if newdate != self._working_date:
            self._changeDate(newdate)
        self._slotTimereport(self._working_date)

    def _slotTimereport(self, qdate):
        """
        Slot attivato da self.ui.dateEdit, SIGNAL("dateChanged(const QDate&)"). Una volta modificata
        la data corrente invia la query al server per aggiornare le viste alla nuova data.
        :param qdate: QDate contenente la nuova data da inserire nella query.
        """
        #si effettua una restore prima del cambiamento del cursore poiché questa
        #funzione è stata progettata per essere chiamata anche più volte consecutive.
        #il restore vero e proprio viene eseguito una volta ricevuta la timereport
        QApplication.restoreOverrideCursor()
        QApplication.setOverrideCursor(QCursor(Qt.BusyCursor))
        self.notify(self.tr("Searching..."))
        #pulisce la tabella con la vista settimanale solamente nel caso si sia in modalità 'weekly'
        if self._mode == "weekly":
            days = getweek(qdate)
            self.ui.tableWeekTimereg.clearContents()
            self.ui.tableWeekTimereg.setRowCount(0)
            for c, day in enumerate(getweek(qdate)):
                self.ui.tableWeekTimereg.horizontalHeaderItem(c).setText(QDate.longDayName(
                                                day.dayOfWeek())[:3] + " " + day.toString("dd-MM-yyyy"))
        #pulisce la tabella con la vista giornaliera colamente nel caso si sia in modalità 'daily'
        else:
            days = [self.ui.dateEdit.date()]
            self.ui.tableTimereg.clearContents()
        self.projects = defaultdict(dict)
        self.remote.timereport([{"date": date.toString("yyyy-MM-dd")} for date in days])

    def _slotTimereportStarted(self):
        """
        Slot attivato da self.remote, SIGNAL("timereportStarted"). Disabilita il pulsante 
        self.ui.tlbTimereg durante l'attesa della risposta dal server.
        """
        self.ui.tlbTimereg.setEnabled(False)

    def _updateDailyTimereport(self, eprojects):
        """
        Metodo chiamato da self._slotUpdateTimereport. Aggiunge le ore registrate nella variabile di
        istanza self.projects nell'ordine in cui arrivano.
        :param eprojects: ElementTree, contiene la risposta dal server con la lista di tutte le ore
        registrate nell'arco della giornata.
        """
        for project in eprojects:
            self.ui.tableTimereg.setRowCount(len(project))
            total_time = 0
            for r, p in enumerate(project):
                self.projects[0][r] = AchievoProject(p)
                p = self.projects[0][r]
                hmtime = min2hmtime(int(p.get("time")))
                p.set("hmtime", hmtime)
                total_time += int(p.get("time"))
                row = (QTableWidgetItem(p.get("activitydate")),
                       QTableWidgetItem("%s / %s" % (p.get("prj"), p.get("pha"))),
                       QTableWidgetItem(p.get("act")),
                       QTableWidgetItem(hmtime),
                       QTableWidgetItem("\n" + p.get("remark") + "\n"))
                for c, cell in enumerate(row):
                    self.ui.tableTimereg.setItem(r, c, cell)
                    if c != 4:
                        self.ui.tableTimereg.resizeColumnToContents(c)
        self.notify(self.tr("Day total: ") + "%s" % min2hmtime(total_time))
        self.ui.tableTimereg.resizeRowsToContents()
        self.ui.btnToday.setEnabled(self._working_date != QDate.currentDate())
        self.ui.tlbTimereg.setEnabled(True)

    def _updateWeeklyTimereport(self, eprojects):
        """
        Metodo chiamato da self._slotUpdateTimereport. Aggiunge le ore registrate, giorno per giorno,
        nella variabile di istanza self.projects nell'ordine in cui arrivano dal server.
        :param eprojects: lista di ElementTree, contiene la risposta dal server con la lista di tutte
        le ore registrate nell'arco di una data giornata.
        """
        for project in eprojects:
            if self.ui.tableWeekTimereg.rowCount() < len(project):
                self.ui.tableWeekTimereg.setRowCount(len(project))
            for r, p in enumerate(project):
                p = AchievoProject(p)
                hmtime = min2hmtime(int(p.get("time")))
                p.set("hmtime", hmtime)
                item = QTableWidgetItem("\n".join([p.get("prj"), p.get("pha") + " / " + p.get("act"), hmtime]))
                c = QDate.fromString(p.get("activitydate").replace("-", ""), "yyyyMMdd").dayOfWeek() - 1
                self.projects[c][r] = p
                self.ui.tableWeekTimereg.setItem(r, c, item)
                self.ui.tableWeekTimereg.item(r, c).setTextAlignment(Qt.AlignHCenter)
                self.ui.tableWeekTimereg.resizeRowToContents(r)
                self.ui.tableWeekTimereg.verticalHeader().setVisible(False)
        self.ui.tableWeekTimereg.insertRow(self.ui.tableWeekTimereg.rowCount())
        for day in self.projects.iterkeys():
            hours = 0
            for prj in self.projects[day].iterkeys():
                hours += hmtime2min(self.projects[day][prj].get("hmtime"))
            hours = min2hmtime(hours)
            item = QTableWidgetItem("Total: %s" % hours)
            self.ui.tableWeekTimereg.setItem(self.ui.tableWeekTimereg.rowCount() - 1,
                                             day, item)
            self.ui.tableWeekTimereg.item(self.ui.tableWeekTimereg.rowCount() - 1,
                                          day).setTextAlignment(Qt.AlignHCenter)
            self.ui.tableWeekTimereg.item(self.ui.tableWeekTimereg.rowCount() - 1,
                                          day).setFont(QFont(QFont().defaultFamily(),
                                                             15, QFont.Bold))
            self.ui.tableWeekTimereg.resizeRowToContents(self.ui.tableWeekTimereg.rowCount() - 1)
        if QDate.currentDate() in getweek(self._working_date):
            column = QDate.currentDate().dayOfWeek() -1
            for row in range(self.ui.tableWeekTimereg.rowCount()):
                if not self.ui.tableWeekTimereg.item(row, column):
                    self.ui.tableWeekTimereg.setItem(row, column, QTableWidgetItem(""))
                self.ui.tableWeekTimereg.item(row, column).setBackground(QBrush(QColor(255, 255, 0)))
        #TODO: sistemare la notify in modo che dia informazioni utili
        self.notify("Search completed")
        #self.ui.tableTimereg.resizeRowsToContents()
        self.ui.btnThisWeek.setEnabled(self._working_date not in getweek(QDate.currentDate()))
        self.ui.tlbTimereg.setEnabled(True)

    def _slotUpdateTimereport(self, eprojects):
        """
        Slot attivato da self.remote, SIGNAL("timereportOK"). Chiama il metodo corretto per aggiornare
        l'interfaccia corrente.
        :param eprojects: lista di ElementTree, contiene la risposta dal server con una lista di ore
        registrate.
        """
        QApplication.restoreOverrideCursor()
        if self._mode == "daily":
            self._updateDailyTimereport(eprojects)
        elif self._mode == "weekly":
            self._updateWeeklyTimereport(eprojects)
        else:
            assert False, "modo non gestito: %s" % self._mode

    
    def close(self):
        """
        Reimplementazione del metodo close per fare in modo che la time calculator
        venga chiusa quando si chiude la finestra principale.
        """
        if self.calculator and not sip.isdeleted(self.calculator):
            self.calculator.close()
        self.settings.setValue("size", QVariant(self.ui.size()))
        self.settings.setValue("pos", QVariant(self.ui.pos()))
        QMainWindow.close(self)
    
    def closeEvent(self, close_event):
        """
        Reimplementazione del metodo closeEvent che redirige tutti gli eventi di
        chiusura al metodo close reimplementato.
        """
        self.close()

class TimeregMenu(QMenu):
    """
    Classe derivata di QMenu contenente il menu contestuale di tlbTimereg.
    """
    
    def __init__(self,  parent = None):
        QMenu.__init__(self, parent)
        self._single = self.addAction("Single editing mode")
        self._range = self.addAction("Range editing mode")
        self._hours = self.addAction("Hours editing mode")
        self.connect(self._single, SIGNAL("triggered(bool)"), 
                        self._singleTriggered)
        self.connect(self._range, SIGNAL("triggered(bool)"), 
                        self._rangeTriggered)
        self.connect(self._hours, SIGNAL("triggered(bool)"),
                     self._hoursTriggered)
        self.connect(self,  SIGNAL("clicked()"), 
                        self._singleTriggered)
    
    def _singleTriggered(self):
        self.emit(SIGNAL("selected"), "single")
    
    def _rangeTriggered(self):
        self.emit(SIGNAL("selected"), "range")
    
    def _hoursTriggered(self):
        self.emit(SIGNAL("selected"), "hours")
