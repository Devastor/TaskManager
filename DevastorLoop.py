#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ================================================== #
# ================= Devastor Loop ================== #
# ================================================== #
# ============== Copyright by Devastor ============= #
# ================================================== #
# ================================================== #
MODULE_NAME = "DevastorLoop"
# ================================================== #
# ================ Main loop class ================= #
# ================================================== #
# ================================================== #

# import QT modules
from PyQt5.QtCore import QObject, QTextCodec
from PyQt5.QtCore import QDateTime, QUrl
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QFont

# import system modules
import os
import sys
import random
from gtts import gTTS
from playsound import playsound
from functools import partial
import json
import psutil
from threading import Timer
import csv

# import DEVASTOR modules
from DevastorNumberToText import DevastorNumberToText
import DevastorConfig
from DevastorAnalyzer import devastorLogInfo
from DevastorAnalyzer import devastorIsOnline

class DevastorLoop(QObject):
    # init parent class and all child class variables (list, list)
    def __init__(self, taskPanels, sidePanels):
        devastorLogInfo('(' + MODULE_NAME + ')', "__init__" + ":", "Initialize parent class...")
        super().__init__()

        devastorLogInfo('(' + MODULE_NAME + ')', "__init__" + ":", "Initialize class variables... ")
        self.numberTranslator = DevastorNumberToText()                          # number-to-text translator
        self.devastorTaskPanels = taskPanels                                    # instance of task panels array(main)
        self.devastorSidePanels = sidePanels                                    # instance of side panels array(main)
        self.devastorMinuteKooKoo = QDateTime.currentDateTime().time().minute() # minute kookoo object
        self.devastorHourKooKoo = QDateTime.currentDateTime().time().hour()     # hour kookoo object
        self.devastorTasks = []                                                 # array of actual tasks
        self.devastorFinishedTasks = []                                         # array of finished tasks
        self.needFood = False                                                   # is battery very low?
        self.powerPlugged = True                                                # is power plugged in?

        # Labels for DEBUG
        """
        self.devastorCommandLabel = QLabel()
        self.devastorCommandLabel.setText("")
        self.devastorCommandLabel.show()
        self.devastorStateLabel = QLabel()
        self.devastorStateLabel.setText("IDLE")
        self.devastorStateLabel.show()
        """

        # say 'hello'
        devastorLogInfo('(' + MODULE_NAME + ')', "__init__" + ":", "Greet user")
        self.saySample(DevastorConfig.GREET_PHRASE)
        # load all JSON data and put tasks to devastorTasks[]
        devastorLogInfo('(' + MODULE_NAME + ')', "__init__" + ":", "Load all JSON data")
        self.devastorLoadJSON()

        #self.devastorUpdateRegularJSON() # for DEBUG ONLY!

    # generate random filename, save it on disk, play, then delete from disk (String)
    def saySample(self, text):
        #self.devastorCommandLabel.setText(text)

        if devastorIsOnline():
            devastorLogInfo('(' + MODULE_NAME + ')', "saySample" + ":", "Generate VERY random filename")
            # generate VERY random filename
            r1 = random.randint(1, 10000000)
            r2 = random.randint(1, 10000000)
            self.devastorAudioSample = str(r2) + "speech" + str(r1) + ".mp3"

            # generate speech audio from input text variable  and save it to the disk
            devastorLogInfo('(' + MODULE_NAME + ')', "saySample" + ":", "Save generated audio to disk")
            speech = gTTS(text=text, lang='ru')
            speech.save(self.devastorAudioSample)
            devastorLogInfo('(' + MODULE_NAME + ')', "saySample" + ":", "file "+self.devastorAudioSample+' created')

            # if sound is ON, play generated audio
            if (DevastorConfig.SOUND_ON):
                devastorLogInfo('(' + MODULE_NAME + ')', "saySample" + ":", "Play saved file -",
                                os.path.normpath(DevastorConfig.DIR + '/' + self.devastorAudioSample))
                playsound(os.path.normpath(DevastorConfig.DIR + '/' + self.devastorAudioSample), True)
                devastorLogInfo('(' + MODULE_NAME + ')', "saySample" + ":", "Set timer to delete audiofile")
                timer = Timer(10, partial(self.onInfoTimerEnds, os.path.normpath(DevastorConfig.DIR + '/' + self.devastorAudioSample)))
                timer.start()
        else:
            for panel in self.devastorTaskPanels:
                panel.changePanel('NO NETWORK...',
                                None,
                                None,
                                None,
                                None,
                                None,
                                None,
                                None)

            playsound(os.path.normpath(DevastorConfig.DIR + '/offline.mp3'), True)

    # when it is ime to delete generated audio
    def onInfoTimerEnds(self, fileName):
        try:
            os.remove(fileName)
            devastorLogInfo('(' + MODULE_NAME + ')', "onInfoTimerEnds" + ":", "file " + fileName + ' deleted')
        except OSError as error:
            devastorLogInfo('(' + MODULE_NAME + ')', "onInfoTimerEnds" + ":", "ERROR -", error)

    # set new task to fast shedule and reload JSON (Dictionary)
    def devastorSetNewTask(self, newVoiceTask):
        # create temp task array
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSetNewTask" + ":", "Create temp task array")
        tempDevastorTasks = []

        # load fast JSON <DevastorFast.json>
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSetNewTask" + ":", "Load fast JSON file")
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSetNewTask" + ":",
                        "============= WITH box started ============")
        with open(DevastorConfig.JSON_FST, encoding='utf-8') as f:
            devastorLogInfo('(' + MODULE_NAME + ')', "devastorSetNewTask" + ":",
                            "For each task in loaded JSON put it to a temp array")
            devastorShedule = json.load(f)
            devastorLogInfo('(' + MODULE_NAME + ')', "devastorSetNewTask" + ":",
                            "============= FOR loop started ===========")
            for task in devastorShedule:
                devastorTask = {}
                devastorTask['name'] = task['name']
                devastorTask['deadline'] = task['deadline']
                devastorTask['priority'] = "middle"#task['priority']

                tempDevastorTasks.append(devastorTask)
                devastorLogInfo('(' + MODULE_NAME + ')', "devastorSetNewTask" + ":", devastorTask['name'], "- added!")
            devastorLogInfo('(' + MODULE_NAME + ')', "devastorSetNewTask" + ":",
                            "============= FOR loop finished ==========")
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSetNewTask" + ":",
                        "============= WITH box finished ===========")

        # add new voice task to the main task array
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSetNewTask" + ":",
                        "Add new voice task to the main task array")
        self.devastorTasks.append(newVoiceTask)

        # add new voice task to the temp task array
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSetNewTask" + ":", "Add new voice task to the temp task array")
        tempDevastorTasks.append(newVoiceTask)
        # save new task array to the fast JSON file
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSetNewTask" + ":", "Save temp task array to the fast JSON file")
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSetNewTask" + ":",
                        "============= WITH box started ============")
        with open(DevastorConfig.JSON_FST, 'w', encoding='utf-8') as outfile:
            json.dump(tempDevastorTasks, outfile, ensure_ascii=False, indent=4)
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSetNewTask" + ":",
                        "============= WITH box finished ===========")


        # reset all Panels
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSetNewTask" + ":", "Reset all panels")
        self.devastorSortSheduleByDeadline()
        self.setPanels()
        self.devastorUpdatePanelsTimeleft()
        """
        # reload all JSON data
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSetNewTask" + ":", "Reload JSON data")
        self.devastorLoadJSON()
        # reset all Panels
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSetNewTask" + ":", "Reset all panels")
        self.setPanels()
        # update panels with actual timeLeft parameter
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSetNewTask" + ":", "Update panels timeLeft parameter")
        self.devastorUpdatePanelsTimeleft()
        """

    # sort task in array by estimated time left
    def devastorSortSheduleByDeadline(self):
        format = "dd.MM.yyyy hh:mm"
        unSorted = True
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSortSheduleByDeadline" + ":", "Sort task array by timeLeft...")
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSortSheduleByDeadline" + ":",
                        "============ WHILE loop started ===========")

        while unSorted:
            unSorted = False
            for i in range(0, len(self.devastorTasks) - 1):
                devastorTaskDateTime1 = QDateTime.fromString(self.devastorTasks[i]['deadline'], format)
                devastorTaskDateTime2 = QDateTime.fromString(self.devastorTasks[i + 1]['deadline'], format)

                if (devastorTaskDateTime1.msecsTo(devastorTaskDateTime2) < 0):
                    devastorTemp = self.devastorTasks[i]
                    self.devastorTasks[i] = dict(self.devastorTasks[i + 1])
                    self.devastorTasks[i + 1] = devastorTemp
                    unSorted = True

        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSortSheduleByDeadline" + ":",
                        "============ WHILE loop finished ==========")
        """"""
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSortSheduleByDeadline" + ":", "Task array sorted by timeLeft:")
        # 'print' array just for LOGGING
        for devastorTask in self.devastorTasks:
            devastorLogInfo('(' + MODULE_NAME + ')', "devastorSortSheduleByDeadline" +
                            ":",
                            devastorTask['name'] +
                            '|' +
                            devastorTask['deadline'] +
                            '|' +
                            devastorTask['priority'])

    # return next day from input (String -> QDateTime)
    def devastorAddDaysToData(self, date, days):
        format = "dd.MM.yyyy hh:mm"
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorAddDaysToData" + ":", "Generate QDateTime from String")
        devastorTaskDateTime = QDateTime.fromString(date, format)
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorAddDaysToData" + ":", "Add one day and return QDateTime object")
        devastorTaskDateTime = devastorTaskDateTime.addDays(days)
        return devastorTaskDateTime

    # update regular JSON each day at 00:00
    def devastorUpdateRegularJSON(self):

        devastorDateTime = QDateTime.currentDateTime()
        currentDate = devastorDateTime.date()

        # create temp task array and load JSON
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":", "Create temp task array")
        devastorTasks = []

        devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":", "Load regular JSON shedule")
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":", "============= WITH box started ============")
        with open(DevastorConfig.JSON_REG, encoding='utf-8') as f:
            devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":",
                            "Read each task from shedule and put to an array")
            devastorShedule = json.load(f)
            # for each task in loaded shedule...
            devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":", "============= FOR loop started ============")
            for task in devastorShedule:
                devastorTask = {}
                devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":", "Reading task data...")
                devastorLogInfo('(' + MODULE_NAME + ')', "devastorSortSheduleByDeadline" +
                                ":",
                                task['name'] +
                                '|' +
                                task['deadline'] +
                                '|' +
                                task['priority'])

                self.daysToAdd = 0

                # check if the task is <Уборка хаты>
                if (task['name'] == 'Уборка хаты'):
                    devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":", "Task is <Уборка хаты>")
                    if (self.devastorDayToDayOfWeek(currentDate.dayOfWeek()) == 'ВС'):
                        devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":", "Today is Sunday")
                        devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":", "Add one week to the task")

                        # add seven days to the current task deadline
                        self.daysToAdd = 7
                    else:
                        # nothing to do right now
                        devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":", "Today is NOT Sunday. Nothing to add")
                        self.daysToAdd = 0
                else:
                    devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":", "Add one day to the task")

                    # add one day to the current task deadline
                    self.daysToAdd = 1

                date = self.devastorAddDaysToData(task['deadline'], self.daysToAdd)

                # fromat new date to the task shedule format
                year = str(date.date().year())
                day = str(date.date().day())
                if (len(day) == 1):
                    day = '0'+day

                month = str(date.date().month())
                if (len(month) == 1):
                    month = '0' + month

                hour = str(date.time().hour())
                if (len(hour) == 1):
                    hour = '0' + hour

                minute = str(date.time().minute())
                if (len(minute) == 1):
                    minute = '0' + minute

                # fill temp task array element
                devastorTask['name'] = task['name']
                devastorTask['deadline'] = day +\
                                            "." +\
                                            month +\
                                            "." +\
                                            year +\
                                            " " + \
                                            hour + \
                                            ":" + \
                                            minute

                devastorTask['priority'] = task['priority']
                devastorTask['timeleft'] = ""

                devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":", "New task data:")
                devastorLogInfo('(' + MODULE_NAME + ')', "devastorSortSheduleByDeadline" +
                                ":",
                                devastorTask['name'] +
                                '|' +
                                devastorTask['deadline'] +
                                '|' +
                                devastorTask['priority'])

                devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":", "Append new task to task array")
                devastorTasks.append(devastorTask)

            devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":",
                            "============= FOR loop finished ===========")

        devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":",
                        "============= WITH box finished ===========")

        # create new array for task data, then upload it to JSON file
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":", "Updated task array:")
        data = []
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":",
                        "============= FOR loop started ============")
        for devastorTask in devastorTasks:

            data.append({
                'name': devastorTask['name'],
                'deadline': devastorTask['deadline'],
                'priority': devastorTask['priority']
            })
            devastorLogInfo('(' + MODULE_NAME + ')', "devastorSortSheduleByDeadline" +
                            ":",
                            devastorTask['name'] +
                            '|' +
                            devastorTask['deadline'] +
                            '|' +
                            devastorTask['priority'])

        devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":",
                        "============= FOR loop finished ===========")

        devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":", "Save new task array to a JSON file")
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":",
                        "============= WITH box started ============")
        with open(DevastorConfig.JSON_REG, 'w', encoding='utf-8') as outfile:
            # json.dump(data, outfile)
            json.dump(data, outfile, ensure_ascii=False, indent=4)
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":",
                        "============= WITH box finished ===========")

        # reload all JSON data
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":", "Reload JSON data")
        self.devastorLoadJSON()
        # reset all Panels
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":", "Reset all panels")
        self.setPanels()
        # update panels with actual timeLeft parameter
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdateRegularJSON" + ":", "Update panels timeLeft parameter")
        self.devastorUpdatePanelsTimeleft()

    # save current task array to an actual JSON file
    def devastorSaveJSON(self):
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSaveJSON" + ":", "Create temp array for tasks")
        data = []
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSaveJSON" + ":",
                        "============= FOR loop started ============")
        for devastorTask in self.devastorTasks:
            data.append({
                'name': devastorTask['name'],
                'deadline': devastorTask['deadline'],
                'priority': devastorTask['priority']
            })
            devastorLogInfo('(' + MODULE_NAME + ')', "devastorSaveJSON" +
                            ": task to save = ",
                            devastorTask['name'] +
                            '|' +
                            devastorTask['deadline'] +
                            '|' +
                            devastorTask['priority'])
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSaveJSON" + ":",
                        "============= FOR loop finished ===========")
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSaveJSON" + ":",
                        "Save temp array to an actual JSON file")
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSaveJSON" + ":",
                        "============= WITH box started ============")
        with open(DevastorConfig.JSON_ACT, 'w', encoding='utf-8') as outfile:
            json.dump(data, outfile, ensure_ascii=False, indent=4)
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSaveJSON" + ":",
                        "============= WITH box finished ===========")

    # load all JSON data
    def devastorLoadJSON(self):
        self.saySample("Гружу!")
        # reset current task array
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "Reset current tasks array")
        self.devastorTasks = []
        format = "dd.MM.yyyy hh:mm"

        # load regular JSON <DevastorRegular.json>
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "Load regular JSON file")
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "============= WITH box started ============")
        with open(DevastorConfig.JSON_REG, encoding='utf-8') as f:
            devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "For each task in loaded JSON put it to a temp array")
            self.devastorShedule = json.load(f)
            devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "============= FOR loop started ===========")
            for task in self.devastorShedule:
                devastorTask = {}
                devastorTask['name'] = task['name']
                devastorTask['deadline'] = task['deadline']
                devastorTask['priority'] = task['priority']
                devastorTask['timeleft'] = ""

                devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "Checking only actual tasks")
                if (QDateTime.currentDateTime().secsTo(QDateTime.fromString(devastorTask['deadline'], format)) > 0):

                    # check if task already finished ?
                    devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "Check if task is already finished?")
                    devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "============= FOR loop started ===========")
                    taskAlreadyDone = False
                    for devastorFinishedTask in self.devastorFinishedTasks:
                        devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", devastorFinishedTask['name'], "- finished!")
                        if (devastorFinishedTask['name'] == devastorTask['name']):
                            devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":",
                                            devastorTask['name'], "- removed!")
                            taskAlreadyDone = True
                            break
                    devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "============= FOR loop finished ==========")

                    devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "If task is not finished, add it to the task array")
                    # if not, then add it to the task array
                    if (not taskAlreadyDone):
                        self.devastorTasks.append(devastorTask)
                        devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", devastorTask['name'], "- added!")

            devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "============= FOR loop finished ==========")
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "============= WITH box finished ===========")

        # load long JSON <DevastorLong.json>
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "Load long JSON file")
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":",
                        "============= WITH box started ============")
        with open(DevastorConfig.JSON_LNG, encoding='utf-8') as f:
            devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":",
                            "For each task in loaded JSON put it to a temp array")
            self.devastorShedule = json.load(f)
            devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "============= FOR loop started ===========")
            for task in self.devastorShedule:
                devastorTask = {}
                devastorTask['name'] = task['name']
                devastorTask['deadline'] = task['deadline']
                devastorTask['priority'] = task['priority']
                devastorTask['timeleft'] = ""

                devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "Checking only actual tasks")
                if (QDateTime.currentDateTime().secsTo(QDateTime.fromString(devastorTask['deadline'], format)) > 0):

                    # check if task already finished ?
                    devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":",
                                    "Check if task is already finished?")
                    devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":",
                                    "============= FOR loop started ===========")
                    taskAlreadyDone = False
                    for devastorFinishedTask in self.devastorFinishedTasks:
                        devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", devastorFinishedTask['name'],
                                        "- finished!")
                        if (devastorFinishedTask['name'] == devastorTask['name']):
                            devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":",
                                            devastorTask['name'], "- removed!")
                            taskAlreadyDone = True
                            break
                    devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":",
                                    "============= FOR loop finished ==========")

                    devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":",
                                    "If task is not finished, add it to the task array")
                    # if not, then add it to the task array
                    if (not taskAlreadyDone):
                        self.devastorTasks.append(devastorTask)
                        devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", devastorTask['name'],
                                        "- added!")
            devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "============= FOR loop finished ==========")
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "============= WITH box finished ===========")

        # load fast JSON <DevastorFast.json>
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "Load fast JSON file")
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":",
                        "============= WITH box started ============")
        with open(DevastorConfig.JSON_FST, encoding='utf-8') as f:
            devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":",
                            "For each task in loaded JSON put it to a temp array")
            self.devastorShedule = json.load(f)
            devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "============= FOR loop started ===========")
            for task in self.devastorShedule:
                devastorTask = {}
                devastorTask['name'] = task['name']
                devastorTask['deadline'] = task['deadline']
                devastorTask['priority'] = task['priority']
                devastorTask['timeleft'] = ""

                devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "Checking only actual tasks")
                if (QDateTime.currentDateTime().secsTo(QDateTime.fromString(devastorTask['deadline'], format)) > 0):

                    # check if task already finished ?
                    devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":",
                                    "Check if task is already finished?")
                    devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":",
                                    "============= FOR loop started ===========")
                    taskAlreadyDone = False
                    for devastorFinishedTask in self.devastorFinishedTasks:
                        devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", devastorFinishedTask['name'],
                                        "- finished!")
                        if (devastorFinishedTask['name'] == devastorTask['name']):
                            devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":",
                                            devastorTask['name'], "- removed!")
                            taskAlreadyDone = True
                            break
                    devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":",
                                    "============= FOR loop finished ==========")

                    devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":",
                                    "If task is not finished, add it to the task array")
                    # if not, then add it to the task array
                    if (not taskAlreadyDone):
                        self.devastorTasks.append(devastorTask)
                        devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", devastorTask['name'],
                                        "- added!")
            devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "============= FOR loop finished ==========")
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "============= WITH box finished ===========")

        # call the sorting function
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorLoadJSON" + ":", "Sort new task array by deadline")
        self.devastorSortSheduleByDeadline()

    # save completed task to CSV
    def devastorSaveToCSV(self, task):
        with open('DevastorCompletedTasks.csv', mode='a', newline='', encoding='utf-8') as devastorCompletedTasks:
            devastorCSVWriter = csv.writer(devastorCompletedTasks)#, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            devastorDateTime = QDateTime.currentDateTime()
            currentDate = devastorDateTime.date()
            currentTime = devastorDateTime.time()
            devastorTaskCompleteTime = str(currentDate.day()) +\
                                       '.' +\
                                       str(currentDate.month()) +\
                                       '.' +\
                                       str(currentDate.year()) +\
                                       ' ' +\
                                       str(currentTime.hour()) +\
                                       ':' +\
                                       str(currentTime.minute())
            devastorCSVWriter.writerow([task['name'], task['deadline'], devastorTaskCompleteTime, task['priority']])

    # on task complete, remove it from an array (String)
    def devastorTaskComplete(self, devastorTaskName):
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorTaskComplete" + ":", "For each task in task array check if it's completed")
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorTaskComplete" + ":", "============= FOR loop started ===========")
        for devastorTask in self.devastorTasks:
            formatTask = ((devastorTask['name']).casefold()).replace(' ', '')
            doneTask = (devastorTaskName.casefold()).replace(' ', '')

            if (doneTask == formatTask):
                # play great sound!
                playsound(os.path.normpath(DevastorConfig.DIR + '/' + "tadam.mp3"), True)

                devastorLogInfo('(' + MODULE_NAME + ')', "devastorTaskComplete" + ":", devastorTask['name'], "- completed!")
                devastorTaskFinished = {}
                devastorTaskFinished['name'] = devastorTask['name']
                devastorTaskFinished['deadline'] = devastorTask['deadline']
                devastorTaskFinished['priority'] = devastorTask['priority']
                devastorLogInfo('(' + MODULE_NAME + ')', "devastorTaskComplete" + ":", "Add completed task to the finished tasks array")
                self.devastorFinishedTasks.append(devastorTaskFinished)
                self.devastorSaveToCSV(devastorTaskFinished)
                devastorLogInfo('(' + MODULE_NAME + ')', "devastorTaskComplete" + ":", "Remove task from task array")
                self.devastorTasks.remove(devastorTask)
                # reset all Panels
                devastorLogInfo('(' + MODULE_NAME + ')', "devastorTaskComplete" + ":", "Reset all panels")
                self.setPanels()
                # update panels with actual timeLeft parameter
                devastorLogInfo('(' + MODULE_NAME + ')', "devastorTaskComplete" + ":", "Update panels timeLeft parameter")
                self.devastorUpdatePanelsTimeleft()
            else:
                devastorLogInfo('(' + MODULE_NAME + ')', "devastorTaskComplete" + ":", devastorTask['name'], "- pending!")
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorTaskComplete" + ":", "============= FOR loop finished ==========")
        #self.devastorSaveJSON()

        # 'print' array just for LOGGING
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorTaskComplete" + ":", "Finished tasks:")
        for devastorTask in self.devastorFinishedTasks:
            devastorLogInfo('(' + MODULE_NAME + ')', "devastorTaskComplete" +
                            ":",
                            devastorTask['name'] +
                            '|' +
                            devastorTask['deadline'] +
                            '|' +
                            devastorTask['priority'])

    # set actual parameters for all panels
    def setPanels(self):
        devastorLogInfo('(' + MODULE_NAME + ')', "setPanels" + ":", "For each panel in panels")
        devastorLogInfo('(' + MODULE_NAME + ')', "setPanels" + ":", "============= FOR loop started ===========")
        taskNum = 0
        for devastorPanel in self.devastorTaskPanels:

            if(taskNum < len(self.devastorTasks)):
                devastorPanel.extra = None
                devastorPanel.changePanel(self.devastorTasks[taskNum]['name'],
                                          None,
                                          None,
                                          self.devastorTasks[taskNum]['deadline'],
                                          None,
                                          self.devastorTasks[taskNum]['priority'])

                devastorLogInfo('(' + MODULE_NAME + ')', "setPanels" + ":", "Task panel set - ", self.devastorTasks[taskNum]['name'])
            else:
                devastorPanel.changePanel(None,
                                          None,
                                          None,
                                          None,
                                          None,
                                          None,
                                          None,
                                          1)
                devastorLogInfo('(' + MODULE_NAME + ')', "setPanels" + ":", "Blank panel set")

            taskNum += 1

        print("************",taskNum)
        devastorLogInfo('(' + MODULE_NAME + ')', "setPanels" + ":", "============= FOR loop finished ==========")

    # return day in two-letter-format from input int (Int -> String)
    def devastorDayToDayOfWeek(self, day):
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorDayToDayOfWeek" + ":", "Convert day to two-letter-format")
        if (day == 1):
            return 'ПН'
        if (day == 2):
            return 'ВТ'
        if (day == 3):
            return 'СР'
        if (day == 4):
            return 'ЧТ'
        if (day == 5):
            return 'ПТ'
        if (day == 6):
            return 'СБ'
        if (day == 7):
            return 'ВС'

    # convert russian symbols in string (String -> String)
    def devastorStringToRussian(self, text):
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorStringToRussian" + ":", "Convert string to russian")
        return QTextCodec.codecForName("CP1251").toUnicode(text.encode('utf-8'))

    # update timeLeft parameter for all task panels
    def devastorUpdatePanelsTimeleft(self):
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdatePanelsTimeleft" + ":", "For each task panel upate timeLeft")
        # count differense defore deadline and current dateTime
        #  and update info af all panels
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdatePanelsTimeleft" + ":", "============= FOR loop started ===========")
        for devastorPanel in self.devastorTaskPanels:

            # if panel is not blank
            if (devastorPanel.extra != 1):
                format = "dd.MM.yyyy hh:mm"
                # calculate difference between current time and panel deadline
                devastorTaskDateTime = QDateTime.fromString(devastorPanel.deadline, format)
                differense = QDateTime.currentDateTime().secsTo(devastorTaskDateTime)

                # create temp vars to convert sec to day:hour:min format
                devastorDayDiff = int(differense / 24 / 60 / 60)
                devastorHourDiff = int((differense - devastorDayDiff * 60 * 60 * 24) / 60 / 60)
                devastorMinuteDiff = int((differense - devastorHourDiff * 60 * 60 - devastorDayDiff * 60 * 60 * 24) / 60)

                # add digit '0' to start if only one digit in number
                if (len(str(devastorDayDiff)) < 2):
                    devastorDayDiff = '0' + str(devastorDayDiff)
                else:
                    devastorDayDiff = str(devastorDayDiff)

                if (len(str(devastorHourDiff)) < 2):
                    devastorHourDiff = '0' + str(devastorHourDiff)
                else:
                    devastorHourDiff = str(devastorHourDiff)

                if (len(str(devastorMinuteDiff)) < 2):
                    devastorMinuteDiff = '0' + str(devastorMinuteDiff)
                else:
                    devastorMinuteDiff = str(devastorMinuteDiff)

                devastorTimeLeft = devastorDayDiff + \
                                   ':' + \
                                   devastorHourDiff + \
                                   ':' + \
                                   devastorMinuteDiff

                # change the panel info
                devastorPanel.changePanel(None, None, None, None, devastorTimeLeft)
                devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdatePanelsTimeleft" + ":",
                                "For task -",
                                devastorPanel.name,
                                "- left",
                                devastorTimeLeft)
                devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdatePanelsTimeleft" + ":", devastorPanel.name, "- updated!")
            else:
                devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdatePanelsTimeleft" + ":", devastorPanel.name, "- blank!")
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorUpdatePanelsTimeleft" + ":", "============= FOR loop finished ==========")

    # reads battery percent and plugged in and set concomitant variables
    def devastorReadBatteryData(self):
        # read battery data
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorREadBatteryData" + ":", "Reading battery data...")
        battery = psutil.sensors_battery()
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorREadBatteryData" + ":", "Percent -",
                        battery.percent,
                        ",",
                        "SecLeft -",
                        battery.secsleft,
                        ",",
                        "Charging -",
                        battery.power_plugged)
        # if power plugged in
        if (battery.power_plugged):
            # change powerPlugged flag to TRUE
            devastorLogInfo('(' + MODULE_NAME + ')', "devastorREadBatteryData" + ":", "Battery is charging...")
            self.powerPlugged = True
        # if not plugged in
        else:
            # change powerPlugged flag to False
            self.powerPlugged = False
            devastorLogInfo('(' + MODULE_NAME + ')', "devastorREadBatteryData" + ":", "Battery percent = ", str(battery.percent))
            # if battery VERY low?
            if (battery.percent <= 3):
                # change needFood flag to TRUE
                devastorLogInfo('(' + MODULE_NAME + ')', "devastorREadBatteryData" + ":", "Battery is VERY low!")
                self.needFood = True
            # if battery level is enough
            else:
                # change needFood flag to False
                self.needFood = False

    # return nearest N tasks (List -> String)
    def devastorGetNearestTasks(self, taskArray):
        devastorLogInfo('(' + MODULE_NAME + ')', "devastorSayNearestTasks" + ":",
                        "get nearest",
                        DevastorConfig.TASK_NEAREST,
                        "tasks")
        N = 0
        resultPhrase = ""
        for devastorTask in taskArray:
            days = int((self.devastorTaskPanels[N].timeLeft.split(":"))[0])
            hours = int((self.devastorTaskPanels[N].timeLeft.split(":"))[1])
            minutes = int((self.devastorTaskPanels[N].timeLeft.split(":"))[2])

            dayAdd = ""
            hourAdd = ""
            minuteAdd = ""

            if (days == 1):
                dayAdd = "один день"
            elif (days != 0):
                dayAdd = str(days) + " дня"

            if (hours == 1):
                hourAdd = "один час"
            elif (hours == 2 or
                  hours == 3 or
                  hours == 4):
                hourAdd = str(hours) + " часа"
            elif (hours != 0):
                hourAdd = str(hours) + " часов"

            if (minutes == 1):
                minuteAdd = "одна минута"
            elif (minutes == 2 or
                  minutes == 3 or
                  minutes == 4):
                minuteAdd = str(minutes) + " минуты"
            elif (minutes != 0):
                minuteAdd = str(minutes) + " минут"


            resultPhrase += "До задачи " +\
                            devastorTask['name'] +\
                            " осталось " +\
                            dayAdd +\
                            ',' +\
                            hourAdd +\
                            ',' +\
                            minuteAdd +\
                            '.'
            N += 1
            if (N > DevastorConfig.TASK_NEAREST):
                break

        return resultPhrase

    # run this function every minute
    def devastorEveryMinuteCheck(self):
        self.devastorKooKooTimer = None
        devastorDateTime = QDateTime.currentDateTime()
        currentDate = devastorDateTime.date()
        currentTime = devastorDateTime.time()

        resultFrase = ""

        # one time each hour
        if (self.devastorHourKooKoo != currentTime.hour()):
            self.devastorHourKooKoo = currentTime.hour()
            devastorLogInfo('(' + MODULE_NAME + ')', "run" + ":", "One hour has passed. Do the each-hour-stuff")

            # read battery data
            self.devastorReadBatteryData()

            # if it's midnight, update regular JSON
            if (int(self.devastorHourKooKoo) == 0):
                devastorLogInfo('(' + MODULE_NAME + ')', "run" + ":", "It's midnight. Let's update regular JSON")
                self.devastorUpdateRegularJSON()

            # pronounce hours correctly
            devastorLogInfo('(' + MODULE_NAME + ')', "run" + ":", "Assembling result phrase...")
            devastorLogInfo('(' + MODULE_NAME + ')', "run" + ":", "Add time to result phrase")
            resultAddon = ""
            timeInterval = 'AM'
            hour = int(currentTime.hour())

            if (hour >= 0 and hour <= 12):
                hour = hour
                timeInterval = 'AM'
            else:
                hour = str(int(hour) - 12)
                timeInterval = 'PM'

            if (hour == '1'):
                resultAddon = " час"
            elif (hour == '2' or
                  hour == '3' or
                  hour == '4'):
                resultAddon = " часа"
            else:
                resultAddon = " часов"

            hour = int(hour)
            if (timeInterval == 'AM'):
                if (hour >= 5 and hour <= 11):
                    resultFrase += str(hour) + resultAddon + " утра"
                if (hour >= 1 and hour <= 4):
                    resultFrase += str(hour) + resultAddon + " ночи"
                if (hour == 00):
                    resultFrase += "Наступила... полночь!"

            if (timeInterval == 'PM'):
                if (hour >= 6 and hour <= 11):
                    resultFrase += str(hour) + resultAddon + " вечера"
                if (hour >= 1 and hour <= 5):
                    resultFrase += str(hour) + resultAddon + " дня"

            resultFrase += '.'
            # say first N tasks
            resultFrase += self.devastorGetNearestTasks(self.devastorTasks)

        if (resultFrase != ""):
            resultFrase += '.'

        self.devastorMinuteKooKoo = currentTime.minute()
        devastorLogInfo('(' + MODULE_NAME + ')', "run" + ":", "One minute has passed. Do the each-minute-stuff")

        if (not self.powerPlugged):
            self.devastorReadBatteryData()

        # temp data object
        devastorDate = self.devastorDayToDayOfWeek(currentDate.dayOfWeek()) + \
                       '\n' \
                       + str(currentDate.day())

        hour = currentTime.hour()
        min = currentTime.minute()
        if (len(str(hour)) < 2):
            hour = '0' + str(hour)
        else:
            hour = str(hour)

        if (len(str(min)) < 2):
            min = '0' + str(min)
        else:
            min = str(min)

        # temp time object
        devastorTime = hour + \
                       '\n' + \
                       min

        devastorLogInfo('(' + MODULE_NAME + ')', "run" + ":", "Update data panel with actual data")
        self.devastorSidePanels[0].changePanel(devastorDate,
                                               None,
                                               None,
                                               None,
                                               None,
                                               None,
                                               None,
                                               2)

        devastorLogInfo('(' + MODULE_NAME + ')', "run" + ":", "Update clock panel with actual data")
        self.devastorSidePanels[1].changePanel(devastorTime,
                                               None,
                                               None,
                                               None,
                                               None,
                                               None,
                                               None,
                                               2)

        devastorLogInfo('(' + MODULE_NAME + ')', "run" + ":", "Update panels timeLeft parameter")
        self.devastorUpdatePanelsTimeleft()
        devastorLogInfo('(' + MODULE_NAME + ')', "run" + ":", "For each task check, if need to say it's deadline")
        devastorLogInfo('(' + MODULE_NAME + ')', "run" + ":", "============= FOR loop started ============")
        # for each task check if threre need to say deadline?
        for devastorTaskPanel in self.devastorTaskPanels:
            if (devastorTaskPanel.timeLeft):
                daysLeft = int(devastorTaskPanel.timeLeft.split(':')[0])
                hoursLeft = int(devastorTaskPanel.timeLeft.split(':')[1])
                minutesLeft = int(devastorTaskPanel.timeLeft.split(':')[2])

                if (daysLeft == 0 and hoursLeft == 0 and minutesLeft == 20):
                    devastorLogInfo('(' + MODULE_NAME + ')', "run" + ":",
                                    "For task - ",
                                    devastorTaskPanel.name,
                                    " - left 20 minutes")
                    resultFrase += "До конца задачи " + devastorTaskPanel.name + " осталось 20 минут!"

                if (daysLeft == 0 and hoursLeft == 0 and minutesLeft == 10):
                    devastorLogInfo('(' + MODULE_NAME + ')', "run" + ":",
                                    "For task - ",
                                    devastorTaskPanel.name,
                                    " - left 10 minutes")
                    resultFrase += "До конца задачи " + devastorTaskPanel.name + " осталось 10 минут!"

                if (daysLeft == 0 and hoursLeft == 0 and minutesLeft == 5):
                    devastorLogInfo('(' + MODULE_NAME + ')', "run" + ":",
                                    "For task - ",
                                    devastorTaskPanel.name,
                                    " - left 5 minutes")
                    resultFrase += "До конца задачи " + devastorTaskPanel.name + " осталось 5 минут!"

                if (daysLeft == 0 and hoursLeft == 0 and minutesLeft == 1):
                    devastorLogInfo('(' + MODULE_NAME + ')', "run" + ":",
                                    "For task - ",
                                    devastorTaskPanel.name,
                                    " - left 1 minute")
                    resultFrase += "До конца задачи " + devastorTaskPanel.name + " осталось одна минута!"

        devastorLogInfo('(' + MODULE_NAME + ')', "run" + ":", "============= FOR loop finished ===========")

        # if battery is low say it
        if (self.needFood):
            devastorLogInfo('(' + MODULE_NAME + ')', "run" + ":", "Battery is VERY low, keep telling about it")
            self.saySample(DevastorConfig.FOOD_PHRASE)
            self.needFood = False
        # else say normal phrase
        else:
            if (resultFrase != ""):
                devastorLogInfo('(' + MODULE_NAME + ')', "run" + ":", "Result phrase to say - ", resultFrase)
                self.saySample(resultFrase)

        # set the timer to run this function in 1 minute
        self.devastorKooKooTimer = Timer(60, self.devastorEveryMinuteCheck)
        self.devastorKooKooTimer.start()

    # function starts with the DevastorThread
    def run(self):
        devastorLogInfo('(' + MODULE_NAME + ')', "run" + ":", "Actual encoding = ", sys.stdout.encoding)
        # set all panels
        devastorLogInfo('(' + MODULE_NAME + ')', "run" + ":", "Set all panels data")
        self.setPanels()
        # main loop
        devastorLogInfo('(' + MODULE_NAME + ')', "run" + ":", "Launch every-minute check function")
        self.devastorEveryMinuteCheck()

    # on destroy. on future build...
    def destroy(self):
        pass