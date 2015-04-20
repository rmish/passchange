#!/usr/bin/python3
# -*- coding : utf-8 -*-

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from adModule import ad
from subprocess import check_output
from string import Template
import smtplib
from email.mime.text import MIMEText
from socket import gethostbyaddr, gethostname

class listDialog(QDialog):
    def __init__(self, usersList, parent=None):
        super(listDialog, self).__init__(parent)
        self.users = usersList
        self.selectedUser = None
        lay = QGridLayout()
        self.ulist = QListWidget()
        self.ulist.itemDoubleClicked.connect(self.saveName)
        ok = QPushButton('Выбрать пользователя')
        cancel = QPushButton('Отмена')
        lay.addWidget(self.ulist, 0, 0, 1, 2)
        lay.addWidget(ok, 1, 0, 1, 1)
        lay.addWidget(cancel, 1, 1, 1, 1)
        for user in self.users:
            self.ulist.addItem(user['distinguishedName'])
        ok.clicked.connect(self.saveName)
        cancel.clicked.connect(self.reject)
        self.setLayout(lay)

    def saveName(self):
        for user in self.users:
            if self.ulist.currentItem().text() == user['distinguishedName']:
                self.selectedUser = user
                self.accept()

class mainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(mainWindow, self).__init__(parent)

        self.config = QSettings("passchange.ini", QSettings.IniFormat)
        self.newPass = False
        self.timer = QTimer()
        mainLayout = QGridLayout()
        inputLayout = QFormLayout()

        self.tabn = QLineEdit()
        self.tabn.returnPressed.connect(self.searchUser)
        self.fio = QLineEdit()
        self.fio.returnPressed.connect(self.searchUser)
        self.fio.setMinimumWidth(500)
        self.account = QLineEdit()
        self.account.returnPressed.connect(self.searchUser)
        label1 = QLabel("MAIN\\")
        tmpLay = QHBoxLayout()
        tmpWidget = QWidget()
        tmpLay.addWidget(label1)
        tmpLay.addWidget(self.account)
        tmpWidget.setLayout(tmpLay)
        #self.account.setEnabled(False)
        self.email = QLineEdit()
        self.email.returnPressed.connect(self.searchUser)
        self.office = QLineEdit()
        self.office.setEnabled(False)
        self.post = QLineEdit()
        self.post.setEnabled(False)
        self.password = QLineEdit()
        self.locked = QCheckBox()
        self.locked.setEnabled(False)
        self.disabled = QCheckBox()
        self.disabled.setEnabled(False)
        self.expired = QCheckBox()
        self.expired.setEnabled(False)
        self.dontExpired = QCheckBox()
        self.dontExpired.setEnabled(False)
        self.dn = ''

        #self.tabn.editingFinished.connect(self.searchUser)
        #self.fio.editingFinished.connect(self.searchUser)
        #self.email.editingFinished.connect(self.searchUser)

        inputLayout.addRow('Табельнывй номер', self.tabn)
        inputLayout.addRow('ФИО', self.fio)
        inputLayout.addRow('Учётная запись', tmpWidget)
        inputLayout.addRow('Электронная почта', self.email)
        inputLayout.addRow('Место работы', self.office)
        inputLayout.addRow('Должность', self.post)
        inputLayout.addRow('Пароль', self.password)
        inputLayout.addRow('Учётная запись заблокирована',self.locked)
        inputLayout.addRow('Учётная запись выключена',self.disabled)
        inputLayout.addRow('Срок действия пароля истёк',self.expired)
        inputLayout.addRow('Срок действия пароля никогда не истекает',self.dontExpired)
        mainLayout.addLayout(inputLayout, 0, 1)

        checkUser = QPushButton('Найти пользователя в AD')
        checkUser.clicked.connect(self.searchUser)
        changePassword = QPushButton('Сменить пароль и отпарвить его на почту')
        changePassword.clicked.connect(self.resetPassword)
        clear = QPushButton('Очистить')
        clear.clicked.connect(self.clear)
        #sendPassword = QPushButton('Отправить пароль на почту')
        #sendPassword.clicked.connect(self.mailPassword)
        mainLayout.addWidget(checkUser, 1, 1)
        mainLayout.addWidget(changePassword, 2, 1)
        mainLayout.addWidget(clear, 3, 1)
        #mainLayout.addWidget(sendPassword, 3, 1)

        win = QWidget()
        win.setLayout(mainLayout)
        self.setCentralWidget(win)

        # create object to connect to ldap server
        self.c = ad()
        self.savedPasswd=''
        notConnected = True
        while notConnected == True:
            if self.config.value("connection/connectOnStart") == "true":
                try :
                    self.connectAct()
                    notConnected = False
                    self.timer.start(901000)
                except: #LDAPBindError
                    QMessageBox.critical(self,"Ошибка","Не могу подключиться к LDAP серверу - неверный пароль")
            else:
                self.statusBar().showMessage('Подключение к ldap серверу неактивно')

    def searchUser(self):
        """
        Search user in AD by tabid or parts of the FIO
        """
        self.newPass = False
        self.locked.setChecked(False)
        self.disabled.setChecked(False)
        self.expired.setChecked(False)
        self.dontExpired.setChecked(False)
        
        uac_locked   = 0x00000010
        uac_disabled = 0x00000002
        uac_expired  = 0x00800000
        uac_dontExpired  = 0x00010000
        attrs=['name', 'mail', 'department', 'title', 'distinguishedName','sAMAccountName','postalCode','userAccountControl']

        searchAttr = ''
        searchValue = ''
        found = None
        # check what we are searching for
        if len(self.tabn.text()) > 2:
            searchAttr = 'postalCode'
            searchValue = self.tabn.text()
        elif len(self.fio.text()) > 2:
            searchAttr = 'displayName'
            searchValue = '*'+self.fio.text()+'*'
        elif len(self.account.text()) > 2:
            searchAttr = 'sAMAccountName'
            searchValue = '*'+self.account.text()+'*'
        elif len(self.email.text()) > 2:
            searchAttr = 'mail'
            searchValue = '*'+self.email.text()+'*'
        else:
            return False
        # make search reques to ldap server
        if len(searchValue) > 2:
            try:
                users = self.c.searchUsers(searchAttr, searchValue, attrs, self.config.value('connection/basedn'))
                print(searchAttr+" " +searchValue)
                self.timer.start(901000)
            except:
                self.connectAct()
                #print(searchAttr+" " +searchValue)
                users = self.c.searchUsers(searchAttr, searchValue, attrs, self.config.value('connection/basedn'))
            if len(users) == 0:
                QMessageBox.information(self,"Никого","Не найдено ни одного пользователя")
                return False
            elif len(users) == 1:
                found = users[0]
            else:
                chosen = self.chooseUser(users)
                if not (chosen is None):
                    found = chosen
                else:
                    QMessageBox.information(self,"Никого","Не выбрано ни одного пользователя")
                    return False
        # have user in "found" variable, filling all forms
        self.tabn.setText(found['postalCode'])
        self.fio.setText(found['name'])
        self.email.setText(found['mail'])
        self.office.setText(found['department'])
        self.post.setText(found['title'])
        self.dn = found['distinguishedName']
        self.account.setText(found['sAMAccountName'])
        if (int(found['userAccountControl']) & uac_locked) : self.locked.setChecked(True)
        if (int(found['userAccountControl']) & uac_disabled) : self.disabled.setChecked(True)
        if (int(found['userAccountControl']) & uac_expired) : self.expired.setChecked(True)
        if (int(found['userAccountControl']) & uac_dontExpired) : self.dontExpired.setChecked(True)
        return True


    def connectAct(self):
        """
        Connecting to server using supplied config
        Returns true if successfull
        """
        if len(self.savedPasswd) > 1 :
            self.c.connect(self.config.value("connection/username"),
                    self.savedPasswd,self.config.value("connection/server"))
            self.timer.start(901000)
            #print("1")
        elif self.config.value("connection/password") is None :
            # print("asking for password"+self.config.value("connection/username"))
            passwd = QInputDialog.getText(self, 
                self.tr("Input password to connect to")+ 
                self.config.value("connection/server"),self.tr("Password for ")+ 
                self.config.value("connection/username"),QLineEdit.Password)
            # print(passwd)
            if passwd[1] and len(passwd[0]) >= 3 :
                self.c.connect(self.config.value("connection/username"),
                    passwd[0],self.config.value("connection/server"))
                self.savedPasswd = passwd[0]
                self.timer.start(901000)
                #print(self.savedPasswd)
        else :
            # print(self.config.value("connection/server"))
            self.c.connect(
                self.config.value("connection/username"), 
                self.config.value("connection/password"), 
                self.config.value("connection/server"))
            self.timer.start(901000)
        self.statusBar().showMessage('Подключены к '+self.config.value("connection/server"))
        return True

    def resetPassword(self):
        # generate password
        if self.config.value("ldap/passwordGenerator") == "apg" :
            newPass = check_output(["/usr/bin/apg","-q","-n 1", 
                    "-m 9","-x 12","-c cl_seed","-M NCL","-E l1IO0"], 
                    universal_newlines=True).strip().split("/n")
        elif self.config.value("ldap/passwordGenerator") == "wapg" :
            newPass = check_output(["wapg.exe","-q","-n","1", 
                    "-m","9","-x","12","-c","cl_seed","-M","NCL","-E","l1IO0"], 
                    universal_newlines=True).strip().split("/n")
        elif self.config.value("ldap/passwordGenerator") == "pwgen" :
            newPass = check_output(["/usr/bin/pwgen","-B","-1","12","1"], 
                    universal_newlines=True).strip().split("/n")
        else : print ("Unknown password generator")
        #print(newPass[0])
        self.password.setText(newPass[0])
        try:
            self.c.resetPassword(self.dn, self.password.text())
            self.timer.start(901000)
            self.newPass = True
        except:
            self.connectAct()
            self.c.resetPassword(self.dn, self.password.text())
            self.newPass = True
        # unlock account
        self.c.modifyAttribute('userAccountControl',0x10200,self.dn)
        self.locked.setChecked(False)
        self.disabled.setChecked(False)
        self.expired.setChecked(False)
        self.dontExpired.setChecked(True)
        self.mailPassword()
        return True

    def chooseUser(self, userlist):
        dialog = listDialog(userlist, self)
        dialog.exec()
        return dialog.selectedUser

    def clear(self):
        self.tabn.setText('')
        self.fio.setText('')
        self.account.setText('')
        self.email.setText('')
        self.office.setText('')
        self.post.setText('')
        self.password.setText('')
        self.dn = ''
        self.locked.setChecked(False)
        self.disabled.setChecked(False)
        self.expired.setChecked(False)
        self.dontExpired.setChecked(False)
        return True

    def mailPassword(self):
        if self.email.text() == 'no.mail@vsu.ru':
            QMessageBox.information(self,"Нет почты","Нельзя отправить пользователю письмо без рабочей почты")
            return False
        elif self.newPass :
            sender = "bot@" + str(gethostbyaddr(gethostname())[0])
            ftemplate = open(self.config.value('misc/mailTemplate'),'r',encoding='utf-8')
            body = Template(ftemplate.read())
            mailBody = MIMEText(body.safe_substitute(name=self.fio.text(),
                login=self.account.text(),password=self.password.text()),'plain',_charset='utf-8')
            mailBody['From'] = 'no-replay@main.vsu.ru'
            mailBody['To'] = self.email.text()
            mailBody['Subject'] = 'Смена пароля'
            try:
                server = smtplib.SMTP(self.config.value("misc/mailServer"))
                server.sendmail(sender, self.email.text(), mailBody.as_string())
                server.quit()
                return True
            except smtplib.SMTPRecipientsRefused as recipients:
                print("Фигня с отправкой почты на "+mail)
                print(recipients)            
                return False
        else:
            return False

if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    app.setOrganizationName("vsu")
    app.setOrganizationDomain("rcnit.vsu.ru")
    app.setApplicationName("passchange")
    # translator = QTranslator()
    #translator.load('ldapexplorer_ru')
    #app.installTranslator(translator)

    win = mainWindow()
    win.show()

    sys.exit(app.exec_())
