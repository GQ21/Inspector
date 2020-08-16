"""
Inspector v0.1
---------------
Sanity checker for polygon models.
Written by Gin "GQ21" Jankus
https://github.com/GQ21

"""

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import maya.cmds as mc
import maya.OpenMayaUI as omui

import os,cPickle,re
from functools import partial

import Inspector.checks.in_commands as in_commands


def maya_main_window():
    """
    Return the Maya main window widget as a Python object
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)

class OptionsDialog(QtWidgets.QDialog):    
   
    def __init__(self, options_dic, parent=maya_main_window()):
        super(OptionsDialog, self).__init__(parent)

        self.options = options_dic["options"]
        
        self.setWindowTitle("Options")
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        self.set_btn = QtWidgets.QPushButton("Set")
        self.opt_wdg = {}

        for opt in self.options:           
            opt_key = opt.keys()               
            if "QLineEdit" in opt[opt_key[0]]:
                self.opt_wdg[opt_key[0]] = QtWidgets.QLineEdit()
                self.opt_wdg[opt_key[0]].setText(str(opt[opt_key[0]][1]))                  
                
    def create_layout(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        for opt in self.options:
            opt_key = opt.keys()              
            main_layout.addWidget(QtWidgets.QLabel(opt_key[0]))            
            main_layout.addWidget(self.opt_wdg[opt_key[0]])

        main_layout.addWidget(self.set_btn)
        main_layout.addStretch()

    def create_connections(self):
        self.set_btn.clicked.connect(self.accept)

    def update_setting_list(self):
        for opt in self.options:
            opt_key = opt.keys()             

            if "QLineEdit" in opt[opt_key[0]]:
                opt[opt_key[0]][1] = self.opt_wdg[opt_key[0]].text() 

class Inspector(QtWidgets.QDialog):
    
    dlg_instance = None

    @classmethod
    def show_dialog(cls):                 
        try:
            cls.dlg_instance.close() # pylint: disable=E0601
            cls.dlg_instance.deleteLater()
        except:
            pass
        cls.dlg_instance = Inspector()
        cls.dlg_instance.show()        

    def __init__(self, parent=maya_main_window()):
        super(Inspector, self).__init__(parent)   

        # check current preset
        self.current_preset_path =  os.path.join(mc.internalVar(usd=True),"Inspector/presets/current_preset.txt")     
        try:
            self.current_preset_open = open(self.current_preset_path,"rb")     
        except:
            print("Error opening current preset file, {}".format(self.current_preset_path))
            raise            
        self.current_preset_list  = cPickle.load(self.current_preset_open)
        self.current_preset_open.close()

        # load current preset options         
        try:
            try:
                self.settings_list_open = open(self.current_preset_list[1],"rb")
            except:                      
                self.settings_list_open = open(
                                            os.path.join(
                                                mc.internalVar(usd=True),
                                                "Inspector/presets/custom/{}".format(self.current_preset_list[1])
                                                ),
                                            "rb")            
        except:
            print ("Error opening settings preset file, {}\nLoading Default Preset".format(self.current_preset_list[1]))
            self.default_preset_path  = os.path.join(mc.internalVar(usd=True),"Inspector/presets/default.txt")    
            self.current_preset_list = ["Default Preset", self.default_preset_path]
            self.default_preset_open = open(self.default_preset_path,"rb")    
            self.settings_list = cPickle.load(self.default_preset_open)      
            self.default_preset_open.close()   
        else:               
            self.settings_list = cPickle.load(self.settings_list_open)           
            self.settings_list_open.close()  

        self.obj_list = []
        self.script_jobs = []
        self.setWindowTitle("Inspector")
        self.preset_name = self.current_preset_list[0]
        self.setMinimumSize(900, 700)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.create_actions()
        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_actions(self):
        self.load_preset_action = QtWidgets.QAction("Load Preset", self)
        self.reload_preset_action = QtWidgets.QAction("Reload Preset", self)
        self.save_preset_action = QtWidgets.QAction("Save Preset", self)
        self.about_action = QtWidgets.QAction("About", self)       
   
        self.check_all_action = {}
        self.uncheck_action = {}
        self.invert_action = {}        
        self.add_action = {} 
        self.remove_action = {} 

        for category in self.settings_list:
            self.check_all_action[category[0]] = QtWidgets.QAction("Check All", self)
            self.uncheck_action[category[0]] = QtWidgets.QAction("Uncheck", self)
            self.invert_action[category[0]] = QtWidgets.QAction("Invert", self) 
            self.remove_action[category[0]] = QtWidgets.QAction("Remove Checked", self) 
            for command in category[1]:                                     
                self.add_action[command[0]] = QtWidgets.QAction(command[0], self) 
               
    def create_widgets(self):
        self.menu_bar = QtWidgets.QMenuBar()
        preset_menu = self.menu_bar.addMenu("Preset")
        preset_menu.addAction(self.load_preset_action)
        preset_menu.addAction(self.reload_preset_action)
        preset_menu.addAction(self.save_preset_action)
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction(self.about_action)

        self.label_wdg = QtWidgets.QWidget()        
        self.label_wdg.setMinimumHeight(100)  

        self.preset_label = QtWidgets.QLabel(self.preset_name,self.label_wdg)
        self.preset_label.setMinimumHeight(100)   
        self.preset_label.setMinimumWidth(500)        
        self.preset_label.setFrameStyle(QtWidgets.QFrame.Box | QtWidgets.QFrame.Raised)
        self.preset_label.setLineWidth(2)
        self.preset_label.setAlignment(QtCore.Qt.AlignCenter)                    
        self.preset_label.setStyleSheet("text-transform: uppercase; font-family: Helvetica; font-size: 20px;")          
        self.script_label = QtWidgets.QLabel("Inspector V0.1",self.preset_label) 
        self.script_label.setStyleSheet("text-transform: uppercase; font-family: Helvetica;font-size: 10px;")                 
        self.script_label.setGeometry(210, 20, 100, 100)

        self.obj_item_list_add_btn = QtWidgets.QPushButton("Add Selected")
        self.obj_item_list_add_btn.setMinimumWidth(120)
        self.obj_item_list_remove_btn = QtWidgets.QPushButton("Remove Selected") 
        self.obj_item_list_remove_btn.setMinimumWidth(120)
        self.obj_item_list_sl_all_btn = QtWidgets.QPushButton("Select All")                 
        self.obj_item_list = QtWidgets.QListWidget() 
        self.obj_item_list.setSelectionMode(QtWidgets.QAbstractItemView.ContiguousSelection)
        self.obj_item_list.setMaximumHeight(150) 

        self.log_label = QtWidgets.QLabel("Log:")
        self.log_clear_btn = QtWidgets.QPushButton("Clear Log")
        self.log_clear_btn.setMaximumWidth(120)       
      
        self.category_option_btn = {}
        self.category_option_menu = {}
        self.category_option_add_menu = {}
        self.category_option_rmv_menu = {}
        self.category_collapse_btn = {}      
        self.category_label = {}        
       
        self.command_cb = {}
        self.command_label = {}
        self.command_btn = {}
        self.command_sl = {} 
        self.command_opt_btn = {} 
        self.command_info_btn = {}         
      
        # creating category header widgets 
        for category in self.settings_list: 
            self.category_option_btn[category[0]] = QtWidgets.QPushButton()
            self.category_option_menu[category[0]] = QtWidgets.QMenu(self.category_option_btn[category[0]])           
            
            self.category_option_menu[category[0]].addAction(self.check_all_action[category[0]])
            self.category_option_menu[category[0]].addAction(self.uncheck_action[category[0]])
            self.category_option_menu[category[0]].addAction(self.invert_action[category[0]])           

            self.category_option_add_menu[category[0]] = QtWidgets.QMenu("Add Command", self.category_option_menu[category[0]])                       
            self.category_option_menu[category[0]].addMenu(self.category_option_add_menu[category[0]] )
            self.category_option_rmv_menu[category[0]] = QtWidgets.QMenu("Remove Command", self.category_option_menu[category[0]])
            self.category_option_rmv_menu[category[0]].addAction(self.remove_action[category[0]])
            self.category_option_menu[category[0]].addMenu(self.category_option_rmv_menu[category[0]])

            self.category_option_btn[category[0]].setIcon(QtGui.QIcon(":newPreset.png"))     
            self.category_option_btn[category[0]].setMenu(self.category_option_menu[category[0]])
            self.category_option_btn[category[0]].setMinimumWidth(30)      

            self.category_label[category[0]] = QtWidgets.QLabel(category[0])
            self.category_label[category[0]].setAlignment(QtCore.Qt.AlignCenter)
            self.category_label[category[0]].setStyleSheet("background-color: grey; text-transform: uppercase; font-family: Helvetica; color: #000000; font-size: 18px;")
            self.category_label[category[0]].setMinimumWidth(300)

            self.category_collapse_btn[category[0]] = QtWidgets.QPushButton()
            self.category_collapse_btn[category[0]].setIcon(QtGui.QIcon(":moveUVDown.png")) 
            self.category_collapse_btn[category[0]].setVisible(True)   
            self.category_collapse_btn[category[0]].setMaximumWidth(30)
                        
            # creating groupbox commands widgets  
            for command in category[1]:                             
                self.category_option_add_menu[category[0]].addAction(self.add_action[command[0]])
                self.command_cb[command[0]] = QtWidgets.QCheckBox()
                if command[1][0] == 1:
                    self.command_cb[command[0]].setChecked(1)                       
                self.command_label[command[0]] = QtWidgets.QLabel(command[0])
                self.command_label[command[0]].setMinimumWidth(140)

                self.command_btn[command[0]] = QtWidgets.QPushButton("Run")
                self.command_btn[command[0]].setMaximumWidth(50)
                self.command_btn[command[0]].setMaximumHeight(17)

                self.command_sl[command[0]] = QtWidgets.QPushButton("Select All")
                self.command_sl[command[0]].setEnabled(False)
                self.command_sl[command[0]].setMaximumHeight(17) 

                self.command_info_btn[command[0]] = QtWidgets.QPushButton()
                self.command_info_btn[command[0]].setIcon(QtGui.QIcon(":gameFbxExporterHelp.png"))
                self.command_info_btn[command[0]].setMaximumWidth(15)
                self.command_info_btn[command[0]].setMaximumHeight(17)
                self.command_info_btn[command[0]].setFlat(True)
                # adding widgets with options
                if len(command) > 2:                              
                    self.command_opt_btn[command[0]] = QtWidgets.QPushButton("OPT")
                    self.command_opt_btn[command[0]].setMaximumWidth(30)
                    self.command_opt_btn[command[0]].setMaximumHeight(17)

        self.commands_run_btn = QtWidgets.QPushButton("Run All Checked")

    def create_layout(self):
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setMenuBar(self.menu_bar)
        
        obj_up_btn_layout = QtWidgets.QHBoxLayout()
        obj_up_btn_layout.addWidget(self.obj_item_list_add_btn)
        obj_up_btn_layout.addWidget(self.obj_item_list_remove_btn)
        obj_up_btn_layout.addWidget(self.obj_item_list_sl_all_btn)
        obj_up_btn_layout.setSpacing(3) 
        obj_up_btn_layout.addStretch()

        log_box_layout = QtWidgets.QHBoxLayout()
        log_box_layout.addWidget(self.log_label)
        log_box_layout.addWidget(self.log_clear_btn)
                 
        log_list_grpbox = QtWidgets.QGroupBox()                        
        self.log_list_layout = QtWidgets.QFormLayout()  
        self.log_list_layout.setContentsMargins(0, 0, 0, 0)
        self.log_list_layout.setAlignment(QtCore.Qt.AlignTop)  
        log_list_grpbox.setLayout(self.log_list_layout)                         
        log_list = QtWidgets.QScrollArea()
        log_list.setWidget(log_list_grpbox)
        log_list.setWidgetResizable(True)

        log_layout = QtWidgets.QVBoxLayout()  
        log_layout.addWidget(self.label_wdg)            
        log_layout.addLayout(obj_up_btn_layout)              
        log_layout.addWidget(self.obj_item_list)
        log_layout.addLayout(log_box_layout)    
        log_layout.addWidget(log_list)

        self.log_list_command_wdg = {}
        self.log_list_command_btn = {} 
        self.log_list_objects_grpbox = {}
        self.log_list_object_form = {}
        self.log_list_object_wdg = {}             
               
        commands_layout = QtWidgets.QVBoxLayout()       
     
        category_header_layout = {}   
        commands_grpbox_layout = {}    
        commands_form_layout = {}
        commands_form_row_layout = {}
        self.commands_scroll_wdg = {} 
        self.commands_row_wdg = {}      
        
        # layout category sections
        for category in self.settings_list:    
            category_header_layout[category[0]] = QtWidgets.QHBoxLayout()
            category_header_layout[category[0]].setSpacing(0) 
            
            category_header_layout[category[0]].addWidget(self.category_option_btn[category[0]])     
            category_header_layout[category[0]].addWidget(self.category_label[category[0]] )           
            category_header_layout[category[0]].addWidget(self.category_collapse_btn[category[0]])
            
            # layout commands sections
            commands_grpbox_layout[category[0]] = QtWidgets.QGroupBox() 
            commands_form_layout[category[0]] = QtWidgets.QFormLayout()
            commands_grpbox_layout[category[0]].setLayout(commands_form_layout[category[0]])
            
            self.commands_scroll_wdg[category[0]] = QtWidgets.QScrollArea()
            self.commands_scroll_wdg[category[0]].setWidget(commands_grpbox_layout[category[0]])
            self.commands_scroll_wdg[category[0]].setWidgetResizable(True)
            self.commands_scroll_wdg[category[0]].setFixedHeight(100)
            self.commands_scroll_wdg[category[0]].setFixedWidth(370)
                           
            # adding commands rows                        
            for command in category[1]:                                   
                self.commands_row_wdg[command[0]] = QtWidgets.QWidget() 
                if command[1][1] == 0:
                    self.commands_row_wdg[command[0]].setVisible(False) 

                commands_form_row_layout[command[0]] = QtWidgets.QHBoxLayout(self.commands_row_wdg[command[0]])                             
                commands_form_row_layout[command[0]].setSpacing(4) 
                commands_form_row_layout[command[0]].addWidget(self.command_cb[command[0]])               
                commands_form_row_layout[command[0]].addWidget(self.command_label[command[0]])
                commands_form_row_layout[command[0]].addWidget(self.command_btn[command[0]])
                commands_form_row_layout[command[0]].addWidget(self.command_sl[command[0]]) 

                if len(command) > 2:
                    commands_form_row_layout[command[0]].addWidget(self.command_opt_btn[command[0]])  

                commands_form_row_layout[command[0]].addWidget(self.command_info_btn[command[0]])              
                commands_form_layout[category[0]].addWidget(self.commands_row_wdg[command[0]])                    
                commands_form_row_layout[command[0]].setContentsMargins(0, 0, 0, 0)                             
          
            commands_layout.addLayout(category_header_layout[category[0]])
            commands_layout.addWidget(self.commands_scroll_wdg[category[0]])
            commands_grpbox_layout[category[0]].setContentsMargins(0, 0, 0, 0)            
                                     
        commands_layout.addStretch()
        commands_layout.addWidget(self.commands_run_btn)       

        main_layout.addLayout(log_layout)
        main_layout.addLayout(commands_layout) 

    def create_connections(self):        
        self.save_preset_action.triggered.connect(self.save_preset)
        self.load_preset_action.triggered.connect(self.load_preset)
        self.reload_preset_action.triggered.connect(self.reload_preset)
        self.obj_item_list_add_btn.clicked.connect(self.add_selected)
        self.obj_item_list_remove_btn.clicked.connect(self.remove_selected)
        self.obj_item_list_sl_all_btn.clicked.connect(self.select_all)
        self.log_clear_btn.clicked.connect(self.clear_log)
        self.commands_run_btn.clicked.connect(self.run_all_checked)
        for category in self.settings_list:  
            self.remove_action[category[0]].triggered.connect(partial(self.off_command_row_visibility,category[0]))
            self.category_collapse_btn[category[0]].clicked.connect(partial(self.toggle_commands_visibility, category[0]))            
            for command in category[1]: 
                self.check_all_action[category[0]].triggered.connect(partial(self.check_all_category,command[0]))
                self.uncheck_action[category[0]].triggered.connect(partial(self.uncheck_all_category,command[0]))
                self.invert_action[category[0]].triggered.connect(partial(self.invert_all_category, command[0]))
                self.command_btn[command[0]].clicked.connect(self.clear_log)  
                self.command_btn[command[0]].clicked.connect(partial(self.run_command,command))  
                if len(command) == 2:                      
                    self.command_cb[command[0]].stateChanged.connect(partial(self.update_check_box_list, command[0]))                                                      
                    self.add_action[command[0]].triggered.connect(partial(self.on_command_row_visibility,command[0]))
                else:
                    self.command_cb[command[0]].stateChanged.connect(partial(self.update_check_box_list, command[0]))                    
                    self.command_opt_btn[command[0]].clicked.connect(partial(self.show_option_window, command[0], command[2]))
                    self.add_action[command[0]].triggered.connect(partial(self.on_command_row_visibility,command[0]))

    def add_selected(self):      
        selected_shapes = mc.ls(sl=1, type='mesh', dag=1) 
        selected_obj = mc.listRelatives(selected_shapes, type='transform',p=True)      
        if selected_obj == None:
            print "Nothing is selected"     
        else:
            for obj in selected_obj:
                if obj not in self.obj_list:
                    self.obj_list.append(obj)
                    self.obj_item_list.addItem(str(obj))
                else:
                    print "Object {} is already added".format(obj)

    def remove_selected(self):      
        selected_indexes = self.obj_item_list.selectedIndexes()           
        remove_list = []
        if not selected_indexes:
            print "Nothing is selected"
        else:           
            for item in selected_indexes:                
                index = self.obj_item_list.itemFromIndex(item).text() 
                self.obj_list.remove(index)  
                remove_list.append(index)              
            for i in remove_list:
                found_item = self.obj_item_list.findItems(i, QtCore.Qt.MatchExactly)
                self.obj_item_list.takeItem(self.obj_item_list.row(found_item[0]))  

    def select_all(self):
        for i in range(0,self.obj_item_list.count()):
            item = self.obj_item_list.item(i)
            item.setSelected(True)          

    def run_command(self,command):  
        if len(self.obj_list) == 0: 
            print "Error, there is no object to inspect" 
        else:
            if len(command) == 3:                     
                result = eval("in_commands."+str(command[0])+"(self.obj_list,command[2])")                   
            else:                
                result = eval("in_commands."+str(command[0])+"(self.obj_list)")    
      
            if result:
                state = 0
            else:
                state = 1  

            self.create_log_command_item(command,state) 

            if state == 1:                                  
                self.command_label[command[0]].setStyleSheet("background-color: rgba(0, 255, 67, 66);")   
            else:
                self.command_label[command[0]].setStyleSheet("background-color: rgba(206, 67, 67, 0.90);") 

            self.log_list_layout.addWidget(self.log_list_command_wdg[command[0]])
            self.log_list_layout.addWidget(self.log_list_objects_grpbox[command[0]]) 
            self.log_list_command_btn[command[0]].clicked.connect(partial(self.toggle_objects_grpbox_visibility, command[0]))  
            index_list = []
            command_error_nodes = []  
            for obj in self.obj_list:
                if state == 1: 
                    self.create_log_object_item(obj,state)
                    self.log_list_object_form[command[0]].addWidget(self.log_list_object_wdg[obj])  
                else:
                    for index in result:
                        index_list.append(index[0])
                    if obj not in index_list:
                        self.create_log_object_item(obj,1)
                        self.log_list_object_form[command[0]].addWidget(self.log_list_object_wdg[obj])  
                    else: 
                        for index in result:
                            if index[0] == obj:
                                if len(index) > 2:
                                    self.create_log_object_item(obj,0,index[1],index[2])
                                    command_error_nodes = command_error_nodes + index[2]
                                else:    
                                    self.create_log_object_item(obj,0,index[1])
                                    command_error_nodes = command_error_nodes + [obj]
                                self.log_list_object_form[command[0]].addWidget(self.log_list_object_wdg[obj]) 
                                self.command_sl[command[0]].setEnabled(True)  
            if result:                                 
                self.command_sl[command[0]].clicked.connect(partial(self.select_error_nodes, command_error_nodes))             
                            
    def create_log_command_item(self,command,state,error=None):           
        self.log_list_command_wdg[command[0]] = QtWidgets.QWidget()
        list_command_row_layout = QtWidgets.QHBoxLayout(self.log_list_command_wdg[command[0]])
        list_command_row_layout.setContentsMargins(0, 0, 0, 0) 
        list_command_row_layout.setSpacing(0) 
        list_command_label = QtWidgets.QLabel(str(command[0]))

        if state == 1:
            self.log_list_command_wdg[command[0]].setStyleSheet("background-color: rgba(0, 255, 67, 66);") 
            list_command_status = QtWidgets.QLabel(" -> SUCCESS! ")        
        else:
            self.log_list_command_wdg[command[0]].setStyleSheet("background-color: rgba(144, 22, 22);") 
            list_command_status = QtWidgets.QLabel(" -> ERROR! ")   

        self.log_list_command_btn[command[0]] = QtWidgets.QPushButton()
        self.log_list_command_btn[command[0]].setIcon(QtGui.QIcon(":moveUVDown.png"))  
        self.log_list_command_btn[command[0]].setMaximumWidth(20)       

        list_command_row_layout.addWidget(self.log_list_command_btn[command[0]]) 
        list_command_row_layout.addWidget(list_command_label) 
        list_command_row_layout.addWidget(list_command_status) 

        self.log_list_object_form[command[0]] = QtWidgets.QFormLayout()
        self.log_list_object_form[command[0]].setContentsMargins(0, 0, 0, 0) 
        self.log_list_object_form[command[0]].setSpacing(10) 

        self.log_list_objects_grpbox[command[0]] = QtWidgets.QGroupBox()
        self.log_list_objects_grpbox[command[0]].setContentsMargins(0, 0, 0, 0)                 
        self.log_list_objects_grpbox[command[0]].setLayout(self.log_list_object_form[command[0]])                                          
      
    def create_log_object_item(self,obj,state,error=None,error_nodes=None):       
        self.log_list_object_wdg[obj] = QtWidgets.QWidget()
        self.log_list_object_wdg[obj].setContentsMargins(0, 0, 0, 0)
        list_object_row_layout = QtWidgets.QHBoxLayout(self.log_list_object_wdg[obj]) 
        list_object_row_layout.setSpacing(0) 
        list_object_row_layout.setContentsMargins(0, 0, 0, 0) 
        list_object_row_label = QtWidgets.QLabel(obj)

        if state == 1:            
            self.log_list_object_wdg[obj].setStyleSheet("background-color: rgba(0, 255, 67, 66);") 
            list_object_status = QtWidgets.QLabel(" -> SUCCESS!    ")
        else:
            self.log_list_object_wdg[obj].setStyleSheet("background-color: rgba(206, 67, 67, 0.90);") 
            list_object_status = QtWidgets.QLabel(" -> ERROR!    ") 
            list_object_error_msg = QtWidgets.QLabel(error)         
            list_object_error_msg.setMinimumWidth(len(error)*7)
            self.list_object_row_btn = QtWidgets.QPushButton("Select")           
            if error_nodes:
                self.list_object_row_btn.clicked.connect(partial(self.select_error_nodes,error_nodes))
            else:
                self.list_object_row_btn.clicked.connect(partial(self.select_error_nodes,obj))

            self.list_object_row_btn.setStyleSheet("background-color: rgba(144, 22, 22);") 
            self.list_object_row_btn.setIcon(QtGui.QIcon(":moveShelfDown.png"))  
             
        list_object_row_layout.addWidget(list_object_row_label)        
        list_object_row_layout.addWidget(list_object_status)    

        if state == 0:
            list_object_row_layout.addWidget(self.list_object_row_btn)  
            list_object_row_layout.addWidget(list_object_error_msg)

    def select_error_nodes(self,nodes):
        mc.select(nodes)      

    def toggle_objects_grpbox_visibility(self,command):
        if self.log_list_objects_grpbox[command].isVisible():            
            self.log_list_objects_grpbox[command].setVisible(False)
            self.log_list_command_btn[command].setIcon(QtGui.QIcon(":moveUVRight.png")) 
        else:            
            self.log_list_objects_grpbox[command].setVisible(True)
            self.log_list_command_btn[command].setIcon(QtGui.QIcon(":moveUVDown.png")) 

    def clear_log(self):
        while self.log_list_layout.count() > 0:
            log_item = self.log_list_layout.takeAt(0)
            if log_item.widget():
                log_item.widget().deleteLater()
        
        for category in self.settings_list:            
            for command in category[1]: 
                self.command_label[command[0]].setStyleSheet("") 
                self.command_sl[command[0]].setEnabled(False)              

    def update_check_box_list(self,command_index,cb_state):            
        for category in self.settings_list:            
            for command in category[1]:                               
                if command[0] == command_index:                     
                    if cb_state == 2:                     
                        command[1][0] = 1 
                    else:
                        command[1][0] = 0  

    def check_all_category(self,command):
        if self.commands_row_wdg[command].isVisible():
            self.command_cb[command].setChecked(True)  
    
    def uncheck_all_category(self,command):
        if self.commands_row_wdg[command].isVisible():
            self.command_cb[command].setChecked(False) 

    def invert_all_category(self,command):
        if self.commands_row_wdg[command].isVisible():
            if self.command_cb[command].isChecked():
                self.command_cb[command].setChecked(False) 
            else:
                self.command_cb[command].setChecked(True) 
 
    def off_command_row_visibility(self,category_index):
        for category in self.settings_list:
            if category[0] == category_index:
                for command in category[1]:                    
                    if self.command_cb[command[0]].isChecked():
                        self.commands_row_wdg[command[0]].setVisible(False)
                        self.command_cb[command[0]].setChecked(False)
                        command[1][1] = 0    
                
    def on_command_row_visibility(self,command_index):
        for category in self.settings_list:
            for command in category[1]:
                if command[0] == command_index:
                    if self.commands_row_wdg[command_index].isVisible():
                        pass
                    else:
                        self.commands_row_wdg[command_index].setVisible(True) 
                        self.command_cb[command[0]].setChecked(True)
                        command[1][1] = 1                                  

    def toggle_commands_visibility(self,category):       
        if self.commands_scroll_wdg[category].isVisible():
            self.commands_scroll_wdg[category].setVisible(False)            
            self.category_collapse_btn[category].setIcon(QtGui.QIcon(":moveUVLeft.png")) 
        else:
            self.commands_scroll_wdg[category].setVisible(True)              
            self.category_collapse_btn[category].setIcon(QtGui.QIcon(":moveUVDown.png"))                    
            
    def show_option_window(self,command, options_dic):        
        options_windows = {}

        options_windows[command] = OptionsDialog(options_dic)

        result = options_windows[command].exec_()

        if result == QtWidgets.QDialog.Accepted:
            options_windows[command].update_setting_list()
    
    def run_all_checked(self):       
        self.clear_log()
        if self.obj_item_list.count() == 0:
            print "Error, there is no object to inspect"
        else:
            count = 0
            for category in self.settings_list:            
                for command in category[1]:
                    if self.command_cb[command[0]].isChecked():                  
                        self.run_command(command)     
                        count = count + 1
            if count == 0:
                print "Nothing is checked"

    def save_preset(self):                        
        file_path, selected_filter = QtWidgets.QFileDialog.getSaveFileName(
                                    self, "Save Preset", 
                                    "{}".format(os.path.join(mc.internalVar(usd=True),"Inspector/presets/custom")),
                                    "Text files (*.txt)")
        if file_path:
            saved_preset_path = file_path
            input_name = re.split('[_.]',os.path.split(file_path)[1])            
            file_name = input_name[0]
            for w in input_name[1:]:
                if w != 'txt':
                    file_name = file_name + " "  + w
            
            preset_index = [file_name,saved_preset_path]
            # save preset
            file_write = open(saved_preset_path,"wb")
            cPickle.dump(self.settings_list, file_write)
            file_write.close()
            # modify current preset
            current_preset_write = open(self.current_preset_path,"wb")
            cPickle.dump(preset_index, current_preset_write)
            current_preset_write.close()
            # set label name
            self.preset_label.setText(file_name)    

    def load_preset(self):                 
        file_path, selected_filter = QtWidgets.QFileDialog.getOpenFileName(
                                    self, "Load Preset", 
                                    "{}".format(os.path.join(mc.internalVar(usd=True),"Inspector/presets/custom")),
                                    "Text files (*.txt)")
        if file_path:
            loaded_preset_path = file_path
            input_name = re.split('[_.]' ,os.path.split(file_path)[1])            
            file_name = input_name[0]
            for w in input_name[1:]:
                if w != 'txt':
                    file_name = file_name + " "  + w

            preset_index = [file_name,loaded_preset_path]
            # modify current preset
            current_preset_write = open(self.current_preset_path,"wb")
            cPickle.dump(preset_index, current_preset_write)
            current_preset_write.close()     

            try:
                inspector_win.close() # pylint: disable=E0601
                inspector_win.deleteLater()
            except:
                pass          

            self.show_dialog() 

    def reload_preset(self):            
        try:
            inspector_win.close() # pylint: disable=E0601
            inspector_win.deleteLater()
        except:
            pass 

        self.show_dialog() 

if __name__ == "__main__":
    try:
        inspector_win.close() # pylint: disable=E0601
        inspector_win.deleteLater()
    except:
        pass

    inspector_win = Inspector()
    inspector_win.show()
