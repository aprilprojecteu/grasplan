#!/usr/bin/env python3

import os
import tf
import math
import rospy
import rospkg
import yaml

from qt_gui.plugin import Plugin
from python_qt_binding import loadUi
from python_qt_binding.QtWidgets import QWidget, QFileDialog, QMessageBox

from grasplan.rqt_grasplan.grasps import Grasps
from grasplan.visualisation.grasp_visualiser import GraspVisualiser

from std_msgs.msg import Int8, String
from geometry_msgs.msg import Pose, PoseArray, PoseStamped

from grasplan.rqt_planning_scene.vizualize_planning_scene import PlanningSceneVizSettings, PlanningSceneViz

class ErrorDialogPlugin(Plugin):
    def __init__(self, context):
        super(ErrorDialogPlugin, self).__init__(context)
        self.setObjectName('ErrorDialogPlugin')

        self._widget = QtWidgets.QWidget()
        self._widget.setWindowTitle('Error Dialog Plugin')

        self._show_error_button = QtWidgets.QPushButton('Show Error')
        self._show_error_button.clicked.connect(self._show_error_dialog)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._show_error_button)
        self._widget.setLayout(layout)

        context.add_widget(self._widget)

    def _show_error_dialog(self):
        error_message = "An error occurred!"
        QMessageBox.critical(self._widget, "Error", error_message)

class OpenFileDialog(QWidget):
    '''
    allow the user to select a different yaml file with a button,
    this will open a dialog to select and open a yaml file
    '''
    def __init__(self, initial_path=None):
        super().__init__()
        left, top, width, height = 10, 10, 640, 480
        self.setGeometry(left, top, width, height)
        self.initial_path = initial_path

    def openFileNameDialog(self, save_file_name_dialog=False):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        if self.initial_path is None:
            initial_path = os.environ['HOME']
        else:
            initial_path = self.initial_path
        if save_file_name_dialog:
            fileName, _ = QFileDialog.getSaveFileName(self, 'Select boxes yaml file',\
                          initial_path, 'Yaml Files (*.yaml)', options=options)
        else:
            fileName, _ = QFileDialog.getOpenFileName(self, 'Select boxes yaml file',\
                          initial_path, 'Yaml Files (*.yaml)', options=options)
        if fileName:
            return fileName

    def saveFileNameDialog(self):
        return self.openFileNameDialog(save_file_name_dialog=True)

class RqtPlanningScene(Plugin):

    def __init__(self, context):
        super(RqtPlanningScene, self).__init__(context)
        rospy.loginfo('Initializing grasplan rqt, have a happy planning scene editing !')

        self.setObjectName('RqtPlanningScene')
        # Create QWidget
        self._widget = QWidget()
        # Get path to UI file (xml description of the gui window created with qtcreator)
        grasplan_path = rospkg.RosPack().get_path('grasplan')
        ui_file = os.path.join(grasplan_path, 'config/rqt_planning_scene', 'rqtplanning_scene.ui')
        # Extend the widget with all attributes and children from UI file
        loadUi(ui_file, self._widget)
        self._widget.setObjectName('grasplan - rqt planning scene')
        # Show _widget.windowTitle on left-top of each plugin (when
        # it's set in _widget). This is useful when you open multiple
        # plugins at once. Also if you open multiple instances of your
        # plugin at once, these lines add number to make it easy to
        # tell from pane to pane.
        if context.serial_number() > 1:
            self._widget.setWindowTitle(self._widget.windowTitle() + (' (%d)' % context.serial_number()))

        # variables
        self.selected_box = None

        # parameters
        self.settings = PlanningSceneVizSettings()
        self.settings.yaml_path_to_read = grasplan_path + '/config/examples/planning_scene.yaml'
        self.settings.yaml_path_to_write = grasplan_path + '/config/examples/auto_generated_planning_scene.yaml'
        self.settings.publication_type = 'single'
        self.psv = PlanningSceneViz(self.settings) # TODO: add use case: create planning scene from scratch
        self.psv.publish_boxes()

        # publications
        # self.psv publishes internally, no need to register any publishers here

        self.all_boxes_names = self.psv.get_all_boxes_names()
        self._widget.comboExistingBoxes.addItems([''] + self.all_boxes_names)

        # make a connection between the qt objects and this class methods

        # buttons
        self._widget.cmdAddNew.clicked.connect(self.handle_cmdAddNew)
        self._widget.cmdLoadYaml.clicked.connect(self.handle_cmdLoadYaml)
        self._widget.cmdSaveYaml.clicked.connect(self.handle_cmdSaveYaml)
        self._widget.cmdReset.clicked.connect(self.handle_cmdReset)

        # slide change event
        self._widget.slideRoll.valueChanged.connect(self.slideRoll_value_changed)
        self._widget.slidePitch.valueChanged.connect(self.slidePitch_value_changed)
        self._widget.slideYaw.valueChanged.connect(self.slideYaw_value_changed)
        self._widget.slideX.valueChanged.connect(self.slideX_value_changed)
        self._widget.slideY.valueChanged.connect(self.slideY_value_changed)
        self._widget.slideZ.valueChanged.connect(self.slideZ_value_changed)

        # combo box changed selection
        self._widget.comboExistingBoxes.currentIndexChanged.connect(self.comboExistingBoxes_changed)

        # chk hide changes
        self.hide_chks = [self._widget.chkHide1,
                            self._widget.chkHide2,
                            self._widget.chkHide3,
                            self._widget.chkHide4,
                            self._widget.chkHide5,
                            self._widget.chkHide6,
                            self._widget.chkHide7,
                            self._widget.chkHide8,
                            self._widget.chkHide9,
                            self._widget.chkHide10]
        for hide_chk in self.hide_chks:
            hide_chk.stateChanged.connect(self.chkHide_changed)

        # viz widgets
        self.viz_widgets = [self._widget.txtViz1,
                            self._widget.txtViz2,
                            self._widget.txtViz3,
                            self._widget.txtViz4,
                            self._widget.txtViz5,
                            self._widget.txtViz6,
                            self._widget.txtViz7,
                            self._widget.txtViz8,
                            self._widget.txtViz9,
                            self._widget.txtViz10]

        # populate visibility panel box names
        for i, box_name in enumerate(self.all_boxes_names):
            if i < len(self.viz_widgets):
                self.viz_widgets[i].setPlainText(box_name)
            else:
                rospy.logwarn('visibility panel capacity exceeded, ignoring some boxes')

        self.psv.publish_boxes()
        context.add_widget(self._widget)
        rospy.loginfo('planning scene rqt initialization complete')
        # end of constructor

    # ::::::::::::::  class methods

    def hide(self, scene_name):
        self.psv.settings.ignore_set.add(scene_name)

    def unhide(self, scene_name):
        if scene_name in self.psv.settings.ignore_set:
            self.psv.settings.ignore_set.remove(scene_name)

    def chkHide_changed(self):
        for i, hide_chk in enumerate(self.hide_chks):
            scene_name = self.viz_widgets[i].toPlainText()
            if hide_chk.isChecked():
                self.hide(scene_name)
            else:
                self.unhide(scene_name)
        self.psv.publish_boxes()

    def handle_cmdReset(self):
        self.psv.reset_scene_name(self._widget.comboExistingBoxes.currentText())
        # self._widget.comboExistingBoxes.setCurrentIndex(0)

    def update_slide_values(self, scene_name):
        box = self.psv.get_box_values(scene_name)
        value_x, min_x, max_x  = self.get_slide_value_and_limits('x')
        value_y, min_y, max_y  = self.get_slide_value_and_limits('y')
        value_z, min_z, max_z  = self.get_slide_value_and_limits('z')

        box_position_x = box['box_position_x']
        box_position_y = box['box_position_y']
        box_position_z = box['box_position_z']

        # make sure box values are within range
        #continue_ = False
        #if box_position_x > min_x:
            #if box_position_x < max_x:
                #if box_position_y < min_y:
                    #if box_position_y < max_y:
                        #if box_position_z < min_z:
                            #if box_position_z < max_z:
                                #continue_ = True
        #if not continue_:
            #rospy.logwarn('box values are outside limits, will not update slide values')
            #return

        # diff   -> 100%   # diff = max_scroll_limit - min_scroll_limit
        # value  -> slide_value?  # value = box_position_x
        slide_value_x = (box_position_x - min_x) * 100.0 / (max_x - min_x)
        slide_value_y = (box_position_y - min_y) * 100.0 / (max_y - min_y)
        slide_value_z = (box_position_z - min_z) * 100.0 / (max_z - min_z)

        self._widget.slideX.setValue(slide_value_x)
        self._widget.slideY.setValue(slide_value_y)
        self._widget.slideZ.setValue(slide_value_z)

    def select_box(self, scene_name):
        self.selected_box = scene_name
        self.psv.settings.colors = {}
        self.psv.settings.colors[scene_name] = 'orange'
        self.psv.publish_boxes()
        self.update_slide_values(scene_name)

    def comboExistingBoxes_changed(self):
        combo_text = self._widget.comboExistingBoxes.currentText()
        if combo_text != '':
            rospy.loginfo(f'selecting box: {combo_text}')
            self.select_box(combo_text)

    def handle_cmdAddNew(self):
        print(self._widget.txtRefFrame.toPlainText())

    def handle_cmdLoadYaml(self):
        print('not implemented')

    def handle_cmdSaveYaml(self):
        print('not implemented')

    def slideRoll_value_changed(self):
        if self.selected_box:
            print(self._widget.slideRoll.value())
        else:
            self.error()

    def slidePitch_value_changed(self):
        if self.selected_box:
            print(self._widget.slidePitch.value())
        else:
            self.error()

    def slideYaw_value_changed(self):
        if self.selected_box:
            print(self._widget.slideYaw.value())
        else:
            self.error()

    def error(self, error_msg='No box selected!'):
        QMessageBox.critical(self._widget, "Error", error_msg)

    def compute_value(self, axis):
        slide_value, min_scroll_limit, max_scroll_limit = self.get_slide_value_and_limits(axis)
        if self.selected_box:
            rospy.logdebug(f'slide_value : {slide_value}')
            # diff   -> 100%   # diff = max_scroll_limit - min_scroll_limit
            # value? -> slide_value
            value = min_scroll_limit + slide_value * (max_scroll_limit - min_scroll_limit) / 100.0
            rospy.logdebug(f'box position = {value}')
            return value
        else:
            rospy.logwarn('no box selected, doing nothing...')
            self.error()

    def get_slide_value_and_limits(self, slide):
        '''
        slide can take values of 'x', 'y', or 'z'
        '''
        if slide == 'x':
            return float(self._widget.slideX.value()),\
                    float(self._widget.txtScrollMinX.toPlainText()),\
                    float(self._widget.txtScrollMaxX.toPlainText())
        elif slide == 'y':
            return float(self._widget.slideY.value()),\
                    float(self._widget.txtScrollMinY.toPlainText()),\
                    float(self._widget.txtScrollMaxY.toPlainText())
        elif slide == 'z':
            return float(self._widget.slideZ.value()),\
                    float(self._widget.txtScrollMinZ.toPlainText()),\
                    float(self._widget.txtScrollMaxZ.toPlainText())

    def slideX_value_changed(self):
        value = self.compute_value('x')
        if value:
            self.psv.modify_box(self.selected_box, modify_box_position_x=True, box_position_x=value)

    def slideY_value_changed(self):
        value = self.compute_value('y')
        if value:
            self.psv.modify_box(self.selected_box, modify_box_position_y=True, box_position_y=value)

    def slideZ_value_changed(self):
        value = self.compute_value('z')
        if value:
            self.psv.modify_box(self.selected_box, modify_box_position_z=True, box_position_z=value)


#txtSceneName
#comboRefFrame
#comboExistingBoxes

#buttons

#cmdAddNew
#cmdSelectExisting
#cmdLoadYaml
#cmdSaveYaml

#slides

#slideRoll
#slidePitch
#slideYaw

#slideX
#slideY
#slideZ

# transform

#txtTFX
#txtTFY
#txtTFZ
#txtTFQx
#txtTFQy
#txtTFQz
#txtTFQw

#txtScrollMinX
#txtScrollMinY
#txtScrollMinZ

#txtScrollMaxX
#txtScrollMaxY
#txtScrollMaxZ