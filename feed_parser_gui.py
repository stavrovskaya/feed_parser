
# coding: utf-8

# In[1]:


import urllib
import xml.etree.cElementTree as etree
import pandas as pd
import re
import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QPushButton,
    QInputDialog, QFileDialog, QApplication, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, 
                             QTextEdit, QLineEdit, QListWidget, QListWidgetItem, 
                             QMessageBox, QSpacerItem, QSizePolicy, QProgressBar, QDialog)
from PyQt5.QtGui import (QIcon, QFont, QColor)
from PyQt5.QtCore import (QAbstractTableModel, Qt, QVariant, QModelIndex, QThread, pyqtSignal)

from feed_parser import FeedParser
        


# Threads
class AdvertisementsThread(QThread):
    """
    Runs a counter thread.
    """
    countChanged = pyqtSignal(int)
    def __init__(self, parentWindow):
        super().__init__()
        self.parentWindow = parentWindow

    def run(self, templates,header_template,name_template):
        
        result = self.parentWindow.feedParser.create_advertisements(templates, 
                                                                   header_template = header_template, 
                                                                   name_template = name_template, 
                                                                   progressThread = self)
    
        
                
        valid_result = result[result.wordCount <= FeedParser.MAX_WORD_COUNT]
        removed_result = result[result.wordCount > FeedParser.MAX_WORD_COUNT]
            
        fname = self.parentWindow.fileName.text()
        valid_result[["name", "num", "keyword", "url"]].to_csv(fname,index=False, sep=';', encoding='cp1251')
            
        r_fname = re.sub("(\.\w+)$", "_removed\\1", fname)
        removed_result.to_csv(r_fname,index=False, sep=';', encoding='cp1251')

        

        
# GUI



class DFfeedTableWidget(QTableWidget):
    def __init__(self, parent=None, df = pd.DataFrame()):
        super().__init__(parent)
        self.df = df
        self.initUI()
        
    def initUI(self): 
        self.setColumnCount(self.df.shape[1])     
        self.setRowCount(self.df.shape[0])        
 
        fnt = QFont()
        fnt.setBold(True)
        bkg = QColor("gray")
        
        # Устанавливаем заголовки таблицы
        for i in range(len(self.df.columns)):
            item = QTableWidgetItem(str(self.df.columns[i]))
            item.setBackground(bkg)
            item.setFont(fnt)
            
            self.setHorizontalHeaderItem(i,item)
        #self.setHorizontalHeaderLabels(list(self.df.columns))
 
  
        # заполняем
        for i in range(self.df.shape[0]):
            for j in range(self.df.shape[1]):
                item = QTableWidgetItem(str(self.df.iloc[i,j]))
                if i == self.df.shape[0] - 1:
                    item.setTextAlignment(Qt.AlignCenter)
                    proc = int(str(item.text()).strip("%"))
                    if proc == 100:
                        item.setBackground(QColor(FeedParcerGUI.GREEN))
                    elif proc == 0:
                        item.setBackground(QColor(FeedParcerGUI.RED))
                    else:
                        item.setBackground(QColor(FeedParcerGUI.YELLOW))
                    item.setFont(fnt)
                    
                self.setItem(i, j, item)
     
        # делаем ресайз колонок по содержимому
        self.resizeColumnsToContents()
    def setData(self, df):
        self.df = df
        self.initUI()

class FeedParcerGUI(QMainWindow):
    
    GREEN = "#99ff99"
    RED = "#ff9999"
    YELLOW = "#ffff99"
    
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.font = QFont()
        self.font.setPointSize(11)
        
        
        self.tableWidget = DFfeedTableWidget(self)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.setFixedHeight(370)
        
        
        verticalLayout = QVBoxLayout()
        verticalLayout.addWidget(self.tableWidget)
        
        
        
        verticalLayoutMain = QVBoxLayout()
        verticalLayoutMain.addLayout(verticalLayout)

        self.offerNum = QLabel(self)
        self.offerNum.setFont(self.font)
        
        
        self.progress = QProgressBar(self)
        self.progress.setGeometry(0, 0, 300, 25)
        self.progress.setMaximum(100)
        
        self.calc = AdvertisementsThread(self)
        self.calc.countChanged.connect(self.onCountChanged)
        
        
        horizontalLayoutUrl = QHBoxLayout()
        horizontalLayoutUrl.addWidget(self.offerNum)
        horizontalLayoutUrl.addWidget(self.progress)
        
        
        verticalLayoutMain.addLayout(horizontalLayoutUrl)
        
        gridLayout = QGridLayout()
        gridLayout.setSpacing(10)
        
        tagLabel = QLabel("Тэги")
        tagLabel.setFont(self.font)
        tagLabel.setAlignment(Qt.AlignCenter)
        gridLayout.addWidget(tagLabel, 0, 0)
        
        templateFormLabel = QLabel("Формируемый шаблон ключевого слова")
        templateFormLabel.setFont(self.font)
        templateFormLabel.setAlignment(Qt.AlignCenter)
        gridLayout.addWidget(templateFormLabel, 0, 1)
        
        addGroupTip = "Выбранный шаблон - название группы объявлений.\n"         "Следует выбирать в качестве названия группы шаблон, теги которого присутствуют у всех товаров."
        templateListLabel = QLabel("Список шаблонов ключевых слов")
        templateListLabel.setFont(self.font)
        templateListLabel.setToolTip(addGroupTip)
        templateListLabel.setAlignment(Qt.AlignCenter)
        gridLayout.addWidget(templateListLabel, 0, 3)
        
        names = ["category", "vendor", "vendorCode", "typePrefix", "model", "name"]

        positions = [(i + 1,0) for i in range(len(names))]
        
        self.buttonDict = {}

        for position, name in zip(positions, names):
            
            button = QPushButton(name)
            button.setFont(self.font)
            button.setCheckable(True)
            button.setDisabled(True)
            self.buttonDict[name] = button
            
            button.clicked[bool].connect(self.selectTag)

            gridLayout.addWidget(button, *position)

        self.templateFormText = QTextEdit()
        self.templateFormText.setFont(self.font)
        self.templateFormText.setEnabled(False)
        self.templateFormText.setStyleSheet("QTextEdit{background: white;}")
        gridLayout.addWidget(self.templateFormText, 1, 1, len(names) + 1, 1)
        
        toTemplateButton = QPushButton(">>")
        toTemplateButton.setFont(self.font)
        toTemplateButton.clicked.connect(self.addTemplate)
        
        gridLayout.addWidget(toTemplateButton, 2, 2)
        
        self.templateList = QListWidget(self)
        self.templateList.setFont(self.font)
        self.templateList.setToolTip(addGroupTip)

        self.templateList.doubleClicked.connect(self.listdoubleckickhandler)
        
        gridLayout.addWidget(self.templateList, 1, 3, len(names) - 2, 1)
        
        toHeaderButton = QPushButton(">>")
        toHeaderButton.setFont(self.font)
        toHeaderButton.clicked.connect(self.addHeader)
        gridLayout.addWidget(toHeaderButton, len(names) + 1, 2)
        
        
        
        
        headerLabel = QLabel("Шаблон заголовка объявления")
        headerLabel.setFont(self.font)
        headerLabel.setAlignment(Qt.AlignCenter)
        gridLayout.addWidget(headerLabel, len(names), 3)
        
        self.header = QLineEdit(self)
        self.header.setFont(self.font)
        self.header.setEnabled(False)
        self.header.setStyleSheet("QLineEdit{background: white;}")
        gridLayout.addWidget(self.header, len(names) + 1, 3)
        
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        gridLayout.addItem(spacer, len(names) + 2, 1)
        
        
        fileSaveLabel = QLabel("Результат сохранить в файл (.csv)")
        fileSaveLabel.setFont(self.font)
        gridLayout.addWidget(fileSaveLabel, len(names) + 3, 0)
        
        horizontalLayoutFile = QHBoxLayout()
        self.fileName = QLineEdit(self)
        self.fileName.setFont(self.font)
        self.fileName.setEnabled(False)
        horizontalLayoutFile.addWidget(self.fileName)
        
        self.fileSelectButton = QPushButton("Выбрать")
        self.fileSelectButton.setFont(self.font)
        self.fileSelectButton.setDisabled(True)
        self.fileSelectButton.clicked.connect(self.selectFileName)
        horizontalLayoutFile.addWidget(self.fileSelectButton)
        

        
        gridLayout.addLayout(horizontalLayoutFile, len(names) + 3, 1)
        
        horizontalLayout = QHBoxLayout()
        okButton = QPushButton("OK")
        okButton.setFont(self.font)
        okButton.clicked.connect(self.okClicked)
        
        cancelButton = QPushButton("Cancel")
        cancelButton.setFont(self.font)
        cancelButton.clicked.connect(self.cancelClicked)
        
        otherUrlButton = QPushButton("Выбрать другой фид")
        otherUrlButton.clicked.connect(self.showDialog)
        
        horizontalLayout.addWidget(okButton)
        horizontalLayout.addWidget(cancelButton)
        horizontalLayout.addWidget(otherUrlButton)
        gridLayout.addLayout(horizontalLayout, len(names) + 3, 3)
        
        verticalLayoutMain.addLayout(gridLayout)
        
        central_widget = QWidget(self)
        central_widget.setLayout(verticalLayoutMain)
        self.setCentralWidget(central_widget) 
        
        self.statusBar()

        self.setGeometry(100, 100, 1200, 800)
        self.setWindowTitle('Feed parser')
        self.setWindowIcon(QIcon('./zvlogo.png'))
        self.show() 
        self.showDialog()

    def onCountChanged(self, value):
        self.progress.setValue(value)
        print("value=%d"%(value))
        
    def listdoubleckickhandler(self, item):
        selected = self.templateList.currentRow()
        self.templateList.takeItem(selected)
        
        if self.templateList.count() != 0:
                self.templateList.item(0).setSelected(True)
        

    def showDialog(self, message = ""):

        text, ok = QInputDialog.getText(self, 'Выбрать фид',
            '<html style="font-size:' + str(self.font.pointSize()) + 'pt;">Вставьте путь к фиду:</html>')

        if ok:
            
            try:
                self.offerNum.setText("Загружаю...")
                self.feedParser = FeedParser(text)
            except FileNotFoundError:
                print(sys.exc_info())
                QMessageBox.about(self, "Предупреждение", "Не удалось загрузить файл, проверьте правильность пути!")
                return()
            except urllib.error.HTTPError:
                print(sys.exc_info())
                QMessageBox.about(self, "Предупреждение", "Не удалось загрузить url, \nпроверьте правильность пути либо попробуйте скачать его!")
                return()
            except AttributeError:
                print(sys.exc_info())
                QMessageBox.about(self, "Предупреждение", "Вы не задали путь к фиду!")
                return()
             
            self.fnameToSave = re.sub("\.\w+$", ".csv", text)
            self.fillForm()
            
    def fillForm(self):
        self.tableWidget.setData(self.feedParser.get_offer_top_with_stat(10))
            
        self.fileSelectButton.setDisabled(False)
        self.fileName.setEnabled(True)
            
        if self.fnameToSave.startswith("http"):
            self.fnameToSave = re.sub(".*/(w+\.\w+)$", "\\1.csv", self.fnameToSave)
            
        self.fileName.setText("")
        #button color
        stat = self.feedParser.get_tag_statistic()
        for name in stat:
            name = str(name)
            if name == "url":
                continue
            self.buttonDict[name].setDisabled(False)
            if stat[name] == 100:
                self.buttonDict[name].setStyleSheet("background-color:" + self.GREEN)
            elif stat[name] == 0:
                self.buttonDict[name].setStyleSheet("background-color:" + self.RED)
                self.buttonDict[name].setDisabled(True)
            else:
                self.buttonDict[name].setStyleSheet("background-color:" + self.YELLOW)
                        
        self.offerNum.setText('Всего товаров: %d' % (self.feedParser.get_offer_count()))

            
    def selectFileName(self):
        
        name = QFileDialog.getSaveFileName(self, 'Save File', self.fnameToSave, "*.csv")
        if name[0] != '':
            self.fileName.setText(name[0]) 
        
    def selectTag(self, pressed):
        
        source = self.sender()
        
        tag = source.text()
        
        text = self.templateFormText.toPlainText()
        
        if pressed:            
            if (len(text) == 0) | (text == "<Уже в списке>"):
                self.templateFormText.setPlainText(tag)
            else:
                self.templateFormText.setPlainText(text + "+" + tag)
        else:
            tags = text.split("+")
            tags.remove(tag)
            self.templateFormText.setPlainText("+".join(tags))
    def addTemplate(self):
        template = self.templateFormText.toPlainText()
        
        if (template == "") | (template == "<Уже в списке>"):
            return
            
        newItem = QListWidgetItem(template)
        inList = False
        
        for i in range(self.templateList.count()):
            item = self.templateList.item(i)
            itemText = str(item.text())
            templateTags = template.split("+")
            itemTags = itemText.split("+")
            if set(templateTags) == set(itemTags):
                inList = True
                self.templateFormText.setPlainText("<Уже в списке>")
                break
            
        if not inList:
            self.templateList.addItem(newItem)
            self.templateFormText.setPlainText("")
            
            if self.templateList.count() == 1:
                self.templateList.item(0).setSelected(True)
        
        for name in self.buttonDict:
            button = self.buttonDict[name]
            if button.isChecked():
                button.toggle()
                
    def addHeader(self):
        self.header.setText(self.templateFormText.toPlainText())
        self.templateFormText.setPlainText("")
        for name in self.buttonDict:
            button = self.buttonDict[name]
            if button.isChecked():
                button.toggle()

                
    def cancelClicked(self):
        self.close() 
    def okClicked(self):
        text = ""
        stat = self.feedParser.get_tag_statistic()
        
        if self.templateList.count() == 0:
            text += "Задайте хотя бы один шаблон ключевого слова!\n"
        else:
            item = self.templateList.selectedItems()[0]
            
            nameTemplate = str(item.text())
            nameTemplateTags = nameTemplate.split("+")
            for tag in nameTemplateTags:
                if stat[tag] < 100:
                    text += "Название группы объявлений (ввыделенный шаблон ключевого слова) содержит тег,"                     "который представлен не во всех товарах! Выберите другой шаблон.\n"
                    self.header.setText("")
                    break
        
        if self.fileName.text() == "":
            text += "Укажите название файла для сохранения результата!\n"
        
        if self.tableWidget.rowCount()==0:
            text = "Ну что же Вы не выбрали фид!\nНажмите кнопку Выбрать другой фид.\n"
        
        headerTemplate = ""
        
        
        if self.header.text() == "":
            text += "Задайте шаблон заголовка объявления!\n"
        else:
            headerTemplate = self.header.text().split("+")
            for tag in headerTemplate:
                if stat[tag] < 100:
                    text += "Шаблон заголовка объявления содержит тег, который представлен не во всех товарах!\n"
                    break
                    
        
        
            
        if text != "":
            QMessageBox.about(self, "Предупреждение", text)
        else:
            templates = []
            for i in range(self.templateList.count()):
                item = self.templateList.item(i)
                itemText = str(item.text())
                templateTags = itemText.split("+")
                templates.append(templateTags)
                
                
            
            
            self.createAdvertisements(templates, nameTemplateTags, headerTemplate)
            self.close()
    def createAdvertisements(self, templates, selectedTemplate, headerTemplate):

        self.calc.run(templates, headerTemplate, selectedTemplate)
            
        
if __name__ == '__main__':

    app = QApplication(sys.argv)
    
    ex = FeedParcerGUI()
    ex.show()
    app.exec_()
  

