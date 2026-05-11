###
# This code has been developed by Alicia Pose Díez de la Lastra and Gemma Arce García, Universidad Carlos III de Madrid
# This code is part of the work "Unleashing HoloLens 2 Potential A User-Friendly App for Multi-Model Visualization and Real-Time Tracking in Surgical Settings"
# It is based on the module ARHealth developed by Rafael Moreta Martínez: https://github.com/BSEL-UC3M/OpenARHealth.
# Special thanks to Majd Sassi for the script "Google Drive Direct Download Link Generator.py", this script uses.
###
import logging
import os
from typing import Annotated, Optional

import json
import vtk, qt

import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

from slicer import vtkMRMLScalarVolumeNode

import numpy as np
import time
from pathlib import Path

import ctk
from qt import QPixmap, QIcon, QSize

#
# EZAR_setup
#

class EZAR_setup(ScriptedLoadableModule, VTKObservationMixin):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "EZAR_setup"
        self.parent.categories = ["AR"]
        self.parent.dependencies = []
        self.parent.contributors = ["Alicia Pose Díez de la Lastra (UC3M)"]
        # TODO: update with short description of the module and a link to online module documentation
        self.parent.helpText = """
App para complementar la app universal de HoloLens 2 que empezó Gemma.
See more information in <a href="https://github.com/organization/projectname#EZAR_setup">module documentation</a>.
"""
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""

#
# EZAR_setupParameterNode
#

@parameterNodeWrapper
class EZAR_setupParameterNode:
    """
    The parameters needed by module.

    inputVolume - The volume to threshold.
    imageThreshold - The value at which to threshold the input volume.
    invertThreshold - If true, will invert the threshold.
    thresholdedVolume - The output volume that will contain the thresholded volume.
    invertedVolume - The output volume that will contain the inverted thresholded volume.
    """
    inputVolume: vtkMRMLScalarVolumeNode
    imageThreshold: Annotated[float, WithinRange(-100, 500)] = 100
    invertThreshold: bool = False
    thresholdedVolume: vtkMRMLScalarVolumeNode
    invertedVolume: vtkMRMLScalarVolumeNode


#
# EZAR_setupWidget
#

class EZAR_setupWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._updatingGUIFromParameterNode = False

                

    def setup(self):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/EZAR_setup.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = EZAR_setupLogic()
        self.logic.setupScene()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # Buttons
        ### INITIALIZATION
        # LOAD MODELS
        self.ui.QRsize_SpinBox.connect("valueChanged(double)", self.onQRSizeSpinBoxChanged)
        self.ui.LoadQRModel_Button.connect("clicked(bool)", self.onLoadQRModelFromFileClicked)
        self.ui.LoadVuforiaMarkerModel_Button.connect("clicked(bool)", self.onLoadVuforiaMarkerModelFromFileClicked)
        self.ui.Model_Path.connect('currentPathChanged(QString)', self.onModelPathSelected)
        self.ui.LoadModel_Button.connect("clicked(bool)", self.onLoadModelFromFileClicked)
        self.ui.RemoveSelectedModel_Button.connect("clicked(bool)", self.onRemoveSelectedModelButtonClicked)
        self.ui.FinishAndCenter_Button.connect("clicked(bool)", self.onMoveToOriginButton)
        ### POSITIONING
        self.ui.scaleSliderWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
        self.ui.lrTranslationSliderWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
        self.ui.paTranslationSliderWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
        self.ui.isTranslationSliderWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
        self.ui.lrRotationSliderWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
        self.ui.paRotationSliderWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
        self.ui.isRotationSliderWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
        self.ui.savePos_Button.connect("clicked(bool)", self.onSavePosButton)
        self.ui.resetPos_Button.connect("clicked(bool)", self.onResetPosButton)
        ### CUSTOMIZABLE AND SAVE PARAMETERS
        self.ui.ModelToCustomize_InputSelector.connect('currentIndexChanged(int)', self.onModelForCustomizationSelected)
        self.ui.ModelName_LineEdit.connect('textChanged(QString)', self.onModelNameChanged)
        self.ui.ColorPickerButton.connect("colorChanged(QColor)", self.onChangeColorClicked)
        
        self.ui.savingPath.connect('directorySelected(QString)', self.onSaveDirectoryChanged)
        self.ui.SaveData_Button.connect("clicked(bool)", self.onSaveDataButtonClicked)

        ### CONFIGURATION FILE
        self.ui.GDriveURL_LineEdit.connect('textChanged(QString)', self.onURLchanged)
        self.ui.ModelForGDrive_InputSelector.currentIndexChanged.connect(self.onModelForGDriveURLSelected)
        self.ui.LoadFromGDrive_RadioButton.connect('clicked(bool)', self.onLoadModelsFromGDrive)
        self.ui.LoadFromLocal_RadioButton.connect('clicked(bool)', self.onLoadModelsFromLocalStorage)
        self.ui.SaveConfigFile_Button.connect('clicked(bool)', self.onSaveConfigFileClicked)
        

        ### Collapse collapsible buttons and enable/unable buttons of interest
        self.ui.Initialization_CollapsibleButton.collapsed = False
        self.ui.Models_CollapsibleButton.collapsed = True
        self.ui.Models_CollapsibleButton.enabled = False
        self.ui.FinishAndCenter_Button.enabled = False
        self.ui.RemoveSelectedModel_Button.enabled = False
        self.ui.Positioning_CollapsibleButton.collapsed = True
        self.ui.Positioning_CollapsibleButton.enabled = False
        self.ui.CustomizeAndSave_CollapsibleButton.collapsed = True
        self.ui.CustomizeAndSave_CollapsibleButton.enabled = False
        self.ui.SaveConfigFile_CollapsibleButton.collapsed = True
        self.ui.SaveConfigFile_CollapsibleButton.enabled = False
        self.ui.GDriveConfig_CollapsibleButton.collapsed = False
        self.ui.GDriveConfig_CollapsibleButton.enabled = True

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()
        self.initializeGUI()             
       

        # Layout setup
        # show 3D View
        self.layoutManager= slicer.app.layoutManager()
        self.layoutManager.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUp3DView)
        # Center view in models
        threeDWidget = self.layoutManager.threeDWidget(0)
        threeDView = threeDWidget.threeDView()
        threeDView.resetFocalPoint()
        threeDView.lookFromAxis(ctk.ctkAxesWidget.Posterior)


    def initializeGUI(self):
        """
			initailize the save directory using settings
		"""
        settings = slicer.app.userSettings()
        if settings.value(self.logic.MODEL_PATH): # if the settings exists
            self.ui.Model_Path.setCurrentPath(settings.value(self.logic.MODEL_PATH))
        
        if settings.value(self.logic.SAVING_DIRECTORY): # if the settings exists
            self.ui.savingPath.directory = settings.value(self.logic.SAVING_DIRECTORY)
        
        ### If the images of the AR markers are set
        pathToImages = self._parameterNode.GetParameter(self.logic.UI_IMAGES_PATH)
        totalPath = slicer.util.getModule('EZAR_setup').path.replace("EZAR_setup.py", "") + pathToImages
        #Vuforia Image path
        vuforiaImageName = self._parameterNode.GetParameter(self.logic.VUFORIA_IMAGENAME)
        vuforiaImagePath = os.path.join(totalPath, vuforiaImageName)    
        pixmap = QPixmap(vuforiaImagePath)
        icon = QIcon(pixmap)
        self.ui.LoadVuforiaMarkerModel_Button.setIcon(icon)
        self.ui.LoadVuforiaMarkerModel_Button.setIconSize(QSize(150,150))  # Ajusta el tamaño del icono
        #QR Image path
        qrImageName = self._parameterNode.GetParameter(self.logic.QR_IMAGENAME)
        qrImagePath = os.path.join(totalPath, qrImageName)    
        pixmap = QPixmap(qrImagePath)
        icon = QIcon(pixmap)
        self.ui.LoadQRModel_Button.setIcon(icon)
        self.ui.LoadQRModel_Button.setIconSize(QSize(150,150))  # Ajusta el tamaño del icono

    def cleanup(self):
        """
        Called when the application closes and the module widget is destroyed.
        """
        self.removeObservers()

    def enter(self):
        """
        Called each time the user opens this module.
        """
        # Make sure parameter node exists and observed
        self.initializeParameterNode()    

    def onSceneStartClose(self, caller, event):
        """
        Called just before the scene is closed.
        """
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event):
        """
        Called just after the scene is closed.
        """
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def setCustomLayout(self):
      layoutLogic = self.layoutManager.layoutLogic()
      customLayout_1 = ("<layout type=\"horizontal\">"
      " <item>"
      "  <view class=\"vtkMRMLViewNode\" singletontag=\"1\">"
      "   <property name=\"viewlabel\" action=\"default\">1</property>"
      "  </view>"
      " </item>"
      "</layout>")
      customLayout_2 = ("<layout type=\"horizontal\" split=\"true\">"
      " <item>"
      "  <view class=\"vtkMRMLSliceNode\" singletontag=\"Yellow\">"
      "   <property name=\"orientation\" action=\"default\">Sagittal</property>"
      "   <property name=\"viewlabel\" action=\"default\">Y</property>"
      "   <property name=\"viewcolor\" action=\"default\">#F34A33</property>"
      "  </view>"
      " </item>"
      " <item>"
      "  <view class=\"vtkMRMLViewNode\" singletontag=\"1\">"
      "  <property name=\"viewlabel\" action=\"default\">T</property>"
      "  </view>"
      " </item>"
      "</layout>")
      customLayout_3 = ("<layout type=\"horizontal\">"
      " <item>"
      "  <view class=\"vtkMRMLSliceNode\" singletontag=\"Red\">"
      "   <property name=\"orientation\" action=\"default\">Axial</property>"
      "     <property name=\"viewlabel\" action=\"default\">R</property>"
      "     <property name=\"viewcolor\" action=\"default\">#F34A33</property>"
      "  </view>"
      " </item>"
      "</layout>")
      customLayout_4 = ("<layout type=\"horizontal\" split=\"false\">"
      " <item>"
      "  <view class=\"vtkMRMLViewNode\" singletontag=\"1\">"
      "  <property name=\"viewlabel\" action=\"default\">1</property>"
      "  </view>"
      " </item>"
      " <item>"
      "  <view class=\"vtkMRMLViewNode\" singletontag=\"2\">"
      "  <property name=\"viewlabel\" action=\"default\">2</property>"
      "  </view>"
      " </item>"
      "</layout>")
      self.customLayout_1_ID=996
      self.customLayout_2_ID=997
      self.customLayout_3_ID=998
      self.customLayout_4_ID=999
      layoutLogic.GetLayoutNode().AddLayoutDescription(self.customLayout_1_ID, customLayout_1)
      layoutLogic.GetLayoutNode().AddLayoutDescription(self.customLayout_2_ID, customLayout_2)
      layoutLogic.GetLayoutNode().AddLayoutDescription(self.customLayout_3_ID, customLayout_3)
      layoutLogic.GetLayoutNode().AddLayoutDescription(self.customLayout_4_ID, customLayout_4)

    #
    # UI functions
    #     
    def onQRSizeSpinBoxChanged(self, value):
        """
        Updates the parameter node with the the scaling factor of the QR code
        """
        parameterNode = self.logic.getParameterNode()
        parameterNode.SetParameter(self.logic.QR_MODEL_NEW_SIZE, str(value))

        self.updateGUIFromParameterNode()

    def onLoadQRModelFromFileClicked(self):
        '''
        Loads the QR model from the path
        '''
        # Get the path from the settings and initialize parameter node
        parameterNode = self.logic.getParameterNode()

        # Set the selected AR marker as the QR code:
        parameterNode.SetParameter(self.logic.AR_MARKER_SELECTED, "QR")
        
        # Define the path to the models
        arMarkerModelsPath = parameterNode.GetParameter(self.logic.QR_MODEL_PATH)
        totalPath = slicer.util.getModule('EZAR_setup').path.replace("EZAR_setup.py", "") + arMarkerModelsPath
        arMarkerWhite_name = parameterNode.GetParameter(self.logic.QR_MODEL_NAME_WHITE)
        arMarkerBlack_name = parameterNode.GetParameter(self.logic.QR_MODEL_NAME_BLACK)
        arMarkerWhiteModelFilePath = os.path.join(totalPath, arMarkerWhite_name + '.obj')
        arMarkerBlackModelFilePath = os.path.join(totalPath, arMarkerBlack_name + '.obj')
                
        # Load the models from file using previous information
        arMarker_white = self.logic.loadModelFromFile(arMarkerWhite_name, arMarkerWhiteModelFilePath, color=[1, 1, 1], visibility_bool=True)
        arMarker_black = self.logic.loadModelFromFile(arMarkerBlack_name, arMarkerBlackModelFilePath, color=[0, 0, 0], visibility_bool=True)
        
        # scale model according to QR size spinbox
        newQRSize = float(parameterNode.GetParameter(self.logic.QR_MODEL_NEW_SIZE))
        initialQRSize = float(parameterNode.GetParameter(self.logic.QR_MODEL_INITIAL_SIZE))
        self.logic.scaleQRModel(arMarker_white, initialQRSize, newQRSize)
        self.logic.scaleQRModel(arMarker_black, initialQRSize, newQRSize)

        # disable the button and collapse the menu
        self.ui.ARmarker_CollapsibleButton.collapsed = True
        self.ui.ARmarker_CollapsibleButton.enabled = False
        self.ui.Models_CollapsibleButton.collapsed = False
        self.ui.Models_CollapsibleButton.enabled = True
    
    def onLoadVuforiaMarkerModelFromFileClicked(self):
        '''
        Loads the AR marker model from the path (vuforia's one)
        '''
        # Get the path from the settings and initialize parameter node
        parameterNode = self.logic.getParameterNode()

        # Set the selected AR marker as Vuforia:
        self._parameterNode.SetParameter(self.logic.AR_MARKER_SELECTED, "Vuforia")
        
        # Define the path to the models
        arMarkerModelsPath = parameterNode.GetParameter(self.logic.AR_VUFORIA_MODEL_PATH)
        totalPath = slicer.util.getModule('EZAR_setup').path.replace("EZAR_setup.py", "") + arMarkerModelsPath
        arMarkerWhite_name = parameterNode.GetParameter(self.logic.AR_VUFORIA_NAME_WHITE)
        arMarkerBlack_name = parameterNode.GetParameter(self.logic.AR_VUFORIA_NAME_BLACK)
        arMarkerWhiteModelFilePath = os.path.join(totalPath, arMarkerWhite_name + '.stl')
        arMarkerBlackModelFilePath = os.path.join(totalPath, arMarkerBlack_name + '.stl')
                
        # Load the models from file using previous information
        arMarker_white = self.logic.loadModelFromFile(arMarkerWhite_name, arMarkerWhiteModelFilePath, color=[1, 1, 1], visibility_bool=True)
        arMarker_black = self.logic.loadModelFromFile(arMarkerBlack_name, arMarkerBlackModelFilePath, color=[0, 0, 0], visibility_bool=True)

        # disable the button and collapse the menu
        self.ui.ARmarker_CollapsibleButton.collapsed = True
        self.ui.ARmarker_CollapsibleButton.enabled = False
        self.ui.Models_CollapsibleButton.collapsed = False
        self.ui.Models_CollapsibleButton.enabled = True

    def onModelPathSelected(self, path):
        '''
        Updates the spine model path in the settings
        '''
        settings = slicer.app.userSettings()
        settings.setValue(self.logic.MODEL_PATH, path)
        # enable the button	
        self.ui.LoadModel_Button.enabled = True

    def onLoadModelFromFileClicked(self):
      """
      Load Models
      """
      settings = slicer.app.userSettings()
      print("Loading model...")
      modelPath = settings.value(self.logic.MODEL_PATH)
      print("Models Path: ", modelPath)
    
      if modelPath != "":
        model_name = self.logic.loadModels(modelPath)

        if model_name is not None:
          self.addModelToList(model_name)

        self.ui.RemoveSelectedModel_Button.enabled = True
        self.ui.FinishAndCenter_Button.enabled = True

      self.ui.ModelsCount_Label.text = 'Number of imported models:\n{}. \nModels remaining:\n{}.'.format(len(self.logic.MODELS_DICT), str(int(self.logic.MAX_NUMBER_OF_MODELS)-len(self.logic.MODELS_DICT))) # Write number of models already imported in ModelsCount_Label

    def onRemoveSelectedModelButtonClicked(self):
      """
      """
      try:
        selected_model_item = self.ui.modelsListWidget.selectedItems()[0]
        selected_model_name = selected_model_item.text()
        selected_model_item.delete()

        self.logic.removeModel(selected_model_name)

        print("Model {} has been removed.".format(selected_model_name))
        self.ui.ModelsCount_Label.text = 'Number of imported models: {}. \nModels remaining: {}.'.format(len(self.logic.MODELS_DICT), str(int(self.logic.MAX_NUMBER_OF_MODELS)-len(self.logic.MODELS_DICT))) # Write number of models already imported in ModelsCount_Label
        
        # Unable remove model and finish and center button if there are no models loaded
        if (len(self.logic.MODELS_DICT) == 0):
            self.ui.RemoveSelectedModel_Button.enabled = False
            self.ui.FinishAndCenter_Button.enabled = False


      except IndexError:
        pass
    
    def onMoveToOriginButton(self):
      """
      """
      parameterNode = self.logic.getParameterNode() 
      maxNumOfModels = int(parameterNode.GetParameter(self.logic.MAX_NUMBER_OF_MODELS))
      if (len(self.logic.MODELS_DICT) <= maxNumOfModels): # if all models are ok, then procceed
        self.logic.moveModelsToOrigin()
        # Update GUI
        self.ui.Initialization_CollapsibleButton.collapsed = True
        self.ui.Initialization_CollapsibleButton.enabled = False
        self.ui.Positioning_CollapsibleButton.collapsed = False
        self.ui.Positioning_CollapsibleButton.enabled = True
        
        # Add models in MODELS_DICT to ModelToCustomize_InputSelector
        self.AddModelsToInputSelector()

      else:
          errorMessage = 'Too many models selected. Please, select a maximum of {} models.'.format(maxNumOfModels)
          print(errorMessage)
          self.ui.ErrorInMaxNumOfModels_Label.text = errorMessage
      
    def AddModelsToInputSelector(self):
        self.arrayOfModels = []
        for i, model_name in enumerate(self.logic.MODELS_DICT.keys()):
            modelNode = self.logic.MODELS_DICT[model_name]["node"] 
            self.arrayOfModels.append(modelNode.GetName())           

        self.ui.ModelToCustomize_InputSelector.addItems(self.arrayOfModels)
        self.ui.ModelForGDrive_InputSelector.addItems(self.arrayOfModels)

    def addModelToList(self, model_name):
        """
        """
        self.ui.modelsListWidget.addItem(model_name)

    def onSavePosButton(self):
        self.ui.Positioning_CollapsibleButton.collapsed = True
        self.ui.Positioning_CollapsibleButton.enabled = False
        self.ui.CustomizeAndSave_CollapsibleButton.collapsed = False
        self.ui.CustomizeAndSave_CollapsibleButton.enabled = True

    def onResetPosButton(self):
        """
        """
        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

        self._parameterNode.SetParameter(self.logic.SCALE_LEVEL, str(100.0))
        self._parameterNode.SetParameter(self.logic.TRASLATION_LR_LEVEL, str(0.0))
        self._parameterNode.SetParameter(self.logic.TRASLATION_PA_LEVEL, str(0.0))
        self._parameterNode.SetParameter(self.logic.TRASLATION_IS_LEVEL, str(0.0))
        self._parameterNode.SetParameter(self.logic.ROTATION_LR_LEVEL, str(0.0))
        self._parameterNode.SetParameter(self.logic.ROTATION_PA_LEVEL, str(0.0))
        self._parameterNode.SetParameter(self.logic.ROTATION_IS_LEVEL, str(0.0))
        
        self._parameterNode.EndModify(wasModified)

        self.updateGUIFromParameterNode()
        self.logic.updateTransformFromParameterNode()

    def onModelForCustomizationSelected(self, selectedNodeNumber):
        '''
        This method is called when a new model is selected in the COLORS menu
        '''   
        
        selectedNode = slicer.util.getFirstNodeByName(self.arrayOfModels[selectedNodeNumber])
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        if selectedNode is None:
            self._parameterNode.SetNodeReferenceID(self.logic.MODEL_FOR_CUSTOMIZATION, "")
        else:
            self._parameterNode.SetNodeReferenceID(self.logic.MODEL_FOR_CUSTOMIZATION, selectedNode.GetID())

        self.updateGUIFromParameterNode()

    def onModelNameChanged(self, modelname):
        self.logic.ChangeNameAttributeOfTheSelectedModel(modelname)

    def onChangeColorClicked(self, selectedColor):
                
        self.logic.ChangeColorOfSelectedModel(selectedColor)

    def onSaveDataButtonClicked(self):
        """
		Run processing when user clicks "Save Data" button.
		"""
        self.logic.SaveColors()
        modelsOK = 0
        for i, model_name in enumerate(self.logic.MODELS_DICT.keys()):
                modelNode = self.logic.MODELS_DICT[model_name]["node"]
                modelName = modelNode.GetAttribute("Name")
                modelColor = modelNode.GetAttribute("Color")                
                if (modelName and modelColor):
                    modelsOK += 1
                else:                    
                    print("The customized name of: " + modelNode.GetName() + "is missing")
                    self.ui.SaveParametersWarning_Label.text = "The customized name of: " + modelNode.GetName() + " is missing"
                    
                 

        if (modelsOK == len(self.logic.MODELS_DICT)): # if all models are ok, then procceed
            # Change model names
            for i, model_name in enumerate(self.logic.MODELS_DICT.keys()):
                modelNode = self.logic.MODELS_DICT[model_name]["node"]
                modelName = modelNode.GetAttribute("Name")
                self.ui.SaveParametersWarning_Label.text = "" # Clean warning text

            self.updateParameterNodeFromGUI()

            with slicer.util.tryWithErrorDisplay("Failed to compute results.", waitCursor=True):
                # Compute output
                save_folder_path = self.logic.SaveData()
                # Update GUI
                self.ui.SaveParametersWarning_Label.setText("All files have been saved in:\n" + save_folder_path + ' at ' + time.strftime("%H:%M:%S"))
                self.ui.SaveData_Button.enabled = False
                self.ui.SaveConfigFile_CollapsibleButton.collapsed = False
                self.ui.SaveConfigFile_CollapsibleButton.enabled = True
                self.ui.CustomizeAndSave_CollapsibleButton.enabled = False
                self.ui.CustomizeAndSave_CollapsibleButton.collapsed = True
                
                
    def onLoadModelsFromGDrive(self):
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return
        self._parameterNode.SetNodeReferenceID(self.logic.LOCAL_OR_GDRIVE, "GDrive")

        self.ui.GDriveConfig_CollapsibleButton.enabled = True
        self.ui.GDriveConfig_CollapsibleButton.collapsed = False
        self.ui.GDriveConfig_CollapsibleButton.setStyleSheet("color: rgb(0,0,0);")#("color: rgb(255,255,255);")


    def onLoadModelsFromLocalStorage(self):
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return
        self._parameterNode.SetNodeReferenceID(self.logic.LOCAL_OR_GDRIVE, "Local")

        self.ui.GDriveConfig_CollapsibleButton.enabled = False
        self.ui.GDriveConfig_CollapsibleButton.collapsed = True
        self.ui.GDriveConfig_CollapsibleButton.setStyleSheet("color: rgb(255,255,255);")#("color: rgb(50,50,50);")

     
    def onModelForGDriveURLSelected(self, selectedNodeNumber):
        '''
        This method is called when a new model is selected in the COLORS menu
        '''   
        
        selectedNode = slicer.util.getFirstNodeByName(self.arrayOfModels[selectedNodeNumber])
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        if selectedNode is None:
            self._parameterNode.SetNodeReferenceID(self.logic.MODEL_FOR_GDRIVEURL, "")
        else:
            self._parameterNode.SetNodeReferenceID(self.logic.MODEL_FOR_GDRIVEURL, selectedNode.GetID())

        self.updateGUIFromParameterNode()
    
    def onURLchanged(self, driveurl):
        '''
        This method is called when the User ID field is updated
        '''
        self.logic.ChangeGDriveURLofSelectedModel(driveurl)
    
    		
    def onSaveDirectoryChanged(self, directory):
        """
		Run processing when user selects a new saving location.
		"""
		# update settings with the new directory
        settings = slicer.app.userSettings()
        settings.setValue(self.logic.SAVING_DIRECTORY, directory)

    def onSaveConfigFileClicked(self):
        '''
        This method is called when Save Config File button is clicked
        '''
        parameterNode = self.logic.getParameterNode()
        localOrGDrive = (self._parameterNode.GetNodeReference(self.logic.LOCAL_OR_GDRIVE))
        if localOrGDrive == 'Local':
            modelsOK = 0
            for i, model_name in enumerate(self.logic.MODELS_DICT.keys()):
                    modelNode = self.logic.MODELS_DICT[model_name]["node"]
                    modelURL = modelNode.GetAttribute("URL")            
                    if (modelURL):
                        modelsOK += 1
                    else:                    
                        print("The URL of: " + modelNode.GetName() + " is missing")
                        self.ui.SaveURL_Label.text = "The customized name of: " + modelNode.GetName() + " is missing"
        else:
            self._parameterNode.SetNodeReferenceID(self.logic.LOCAL_OR_GDRIVE, 'GDrive')
            numOfModels = len(self.logic.MODELS_DICT)
            modelsOK = numOfModels
            print('Models OK')

        if (modelsOK == len(self.logic.MODELS_DICT)): # if all models are ok, then procceed
            ## Save the configuration (json) file in the saving directory
            # Get the Save Directory from slicer settings
            settings = slicer.app.userSettings()
            save_folder_path = settings.value(self.logic.SAVING_DIRECTORY)
            self.logic.CreateJSONfileWithModelsInfo(save_folder_path)
            self.ui.GDriveConfig_CollapsibleButton.collapsed = True
            self.ui.GDriveConfig_CollapsibleButton.enabled = False
            self.ui.LoadFromLocal_RadioButton.enabled = False
            self.ui.LoadFromGDrive_RadioButton.enabled = False
            self.ui.LoadFromLocal_RadioButton.setStyleSheet("color: rgb(255,255,255);")#("color: rgb(50,50,50);")
            self.ui.LoadFromGDrive_RadioButton.setStyleSheet("color: rgb(255,255,255);")#("color: rgb(50,50,50);")

            if localOrGDrive == 'Local':
                furtherInstructions = '\nGo to the Windows Device Portal for Microsfot HoloLens 2 and upload this file to \nSystem > Local App Data > EZ-AR > LocalState > ConfigurationFiles.'
            else:
                furtherInstructions = '\nUpload this file to your Google Drive, set it''s accesibility to Anyone with the link and copy its sharing link. \nThen, paste it inside Configuration file url.txt. This file can be accessed through the Windows Device Portal for Microsoft HoloLens 2 at \nSystem > Local App Data > EZ-AR > LocalState > Configuration file url.txt.'
            
            self.ui.SaveURL_Label.text = "The configuration file has been correctly saved in " + save_folder_path + furtherInstructions

        
    #
	# Parameter node and GUI interaction
	# 

    def initializeParameterNode(self):
        """
        Ensure parameter node exists and observed.
        """
        #print("initializing parameter node")
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())
 

            
    def setParameterNode(self, inputParameterNode):
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if inputParameterNode:
            self.logic.setDefaultParameters(inputParameterNode)

            # Unobserve previously selected parameter node and add an observer to the newly selected.
            # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
            # those are reflected immediately in the GUI.
        if self._parameterNode is not None:
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        self._parameterNode = inputParameterNode
        if self._parameterNode is not None:
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

        # Initial GUI update
        self.updateGUIFromParameterNode()

    def updateGUIFromParameterNode(self, caller=None, event=None):
        """
		This method is called whenever parameter node is changed.
		The module GUI is updated to show the current state of the parameter node.
		"""
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

		# Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True

        		
		### if the qr code size is set
        if (self._parameterNode.GetParameter(self.logic.QR_MODEL_NEW_SIZE)):
			# update the qr size spin box
            newqrSize = float(self._parameterNode.GetParameter(self.logic.QR_MODEL_NEW_SIZE))
            self.ui.QRsize_SpinBox.value = newqrSize

        ### if the positioning values are set
        # scale
        if (self._parameterNode.GetParameter(self.logic.SCALE_LEVEL)):
            scaleValue = float(self._parameterNode.GetParameter(self.logic.SCALE_LEVEL))
            self.ui.scaleSliderWidget.value = scaleValue
        # traslation
        if (self._parameterNode.GetParameter(self.logic.TRASLATION_LR_LEVEL)):
            traslationLRvalue = float(self._parameterNode.GetParameter(self.logic.TRASLATION_LR_LEVEL))
            self.ui.lrTranslationSliderWidget.value = traslationLRvalue 
        if (self._parameterNode.GetParameter(self.logic.TRASLATION_PA_LEVEL)):
            traslationPAvalue = float(self._parameterNode.GetParameter(self.logic.TRASLATION_PA_LEVEL))
            self.ui.paTranslationSliderWidget.value = traslationPAvalue
        if (self._parameterNode.GetParameter(self.logic.TRASLATION_IS_LEVEL)):
            traslationISvalue = float(self._parameterNode.GetParameter(self.logic.TRASLATION_IS_LEVEL))
            self.ui.isTranslationSliderWidget.value = traslationISvalue
        # rotation
        if (self._parameterNode.GetParameter(self.logic.ROTATION_LR_LEVEL)):
            rotationLRvalue = float(self._parameterNode.GetParameter(self.logic.ROTATION_LR_LEVEL))
            self.ui.lrRotationSliderWidget.value = rotationLRvalue
        if (self._parameterNode.GetParameter(self.logic.ROTATION_PA_LEVEL)):
            rotationPAvalue = float(self._parameterNode.GetParameter(self.logic.ROTATION_PA_LEVEL))
            self.ui.paRotationSliderWidget.value = rotationPAvalue
        if (self._parameterNode.GetParameter(self.logic.ROTATION_IS_LEVEL)):
            rotationISvalue = float(self._parameterNode.GetParameter(self.logic.ROTATION_IS_LEVEL))
            self.ui.isRotationSliderWidget.value = rotationISvalue

        ### if a new model is selected for customization
        if (self._parameterNode.GetNodeReferenceID(self.logic.MODEL_FOR_CUSTOMIZATION)):
            selectedModel = (self._parameterNode.GetNodeReference(self.logic.MODEL_FOR_CUSTOMIZATION))
            current_color = selectedModel.GetModelDisplayNode().GetColor()
            qcolor = qt.QColor(current_color[0] * 255, current_color[1] * 255, current_color[2] * 255)
            self.ui.ColorPickerButton.setColor(qcolor) 

            name = selectedModel.GetAttribute("Name")
            if (name is None):
                self.ui.ModelName_LineEdit.text = ""
            else:
                self.ui.ModelName_LineEdit.text = name

        ### if a new model is selected for Config File URL generation
        if(self._parameterNode.GetNodeReferenceID(self.logic.MODEL_FOR_GDRIVEURL)):
            selectedModel = (self._parameterNode.GetNodeReference(self.logic.MODEL_FOR_GDRIVEURL))
            url = selectedModel.GetAttribute("URL")
            if (url is None):
                self.ui.GDriveURL_LineEdit.text = ""
            else:
                self.ui.GDriveURL_LineEdit.text = url

		
        ### All the GUI updates are done
        self._updatingGUIFromParameterNode = False

    def updateParameterNodeFromGUI(self, caller=None, event=None):
        """
		This method is called when the user makes any change in the GUI.
		The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
		"""
        
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return
        
        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

        # SLIDERS
        self._parameterNode.SetParameter(self.logic.SCALE_LEVEL, str(self.ui.scaleSliderWidget.value))
        self._parameterNode.SetParameter(self.logic.TRASLATION_LR_LEVEL, str(self.ui.lrTranslationSliderWidget.value))
        self._parameterNode.SetParameter(self.logic.TRASLATION_PA_LEVEL, str(self.ui.paTranslationSliderWidget.value))
        self._parameterNode.SetParameter(self.logic.TRASLATION_IS_LEVEL, str(self.ui.isTranslationSliderWidget.value))
        self._parameterNode.SetParameter(self.logic.ROTATION_LR_LEVEL, str(self.ui.lrRotationSliderWidget.value))
        self._parameterNode.SetParameter(self.logic.ROTATION_PA_LEVEL, str(self.ui.paRotationSliderWidget.value))
        self._parameterNode.SetParameter(self.logic.ROTATION_IS_LEVEL, str(self.ui.isRotationSliderWidget.value))

        self.logic.updateTransformFromParameterNode()

        self._parameterNode.EndModify(wasModified)
                


#
# EZAR_setupLogic
#

class EZAR_setupLogic(ScriptedLoadableModuleLogic, VTKObservationMixin):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """
    # AR marker info
    AR_MARKER_SELECTED = "Vuforia"
    UI_IMAGES_PATH = 'Resources/UI'
    VUFORIA_IMAGENAME = '2DMarker_IGT_DigitalImage.jpg'
    QR_IMAGENAME = 'QRcode_IGTweb.png'
    ## QR code
    QR_MODEL_PATH = "Resources/3DModels/QRcode"
    QR_MODEL_INITIAL_SIZE = '100'
    QR_MODEL_NEW_SIZE = 'NewQRSize'
    QR_MODEL_NAME_WHITE = 'QRcode_IGTweb_100mm_WhiteFragment' #Name of the White part of the QR model
    QR_MODEL_NAME_BLACK = 'QRcode_IGTweb_100mm_BlackFragment' #Name of the Black part of the QR model
    ## Vuforia marker
    AR_VUFORIA_MODEL_PATH = "Resources/3DModels/ARmarker_Vuforia" # Path to the AR marker model
    AR_VUFORIA_NAME_WHITE = '2DMarker_IGTVuforia_White' #Name of the White part of the AR marker model
    AR_VUFORIA_NAME_BLACK = '2DMarker_IGTVuforia_Black' #Name of the Black part of the AR marker model
    # Models info
    MODEL_PATH = 'EZAR_setup/ModelPath'
    MODELS_DICT = dict()
    color_code_i = 0
    MODELS_TRANSFORM = 'Models_T'  
    MAX_NUMBER_OF_MODELS = '8' #Maximum number of models allowed in the Unity app (and hence, the config file) 
    # Sliders info
    SCALE_LEVEL = "Scale level"
    TRASLATION_LR_LEVEL = "Traslation LR level"
    TRASLATION_PA_LEVEL = "Traslation PA level"
    TRASLATION_IS_LEVEL = "Traslation IS level"
    ROTATION_LR_LEVEL = "Rotation LR level"
    ROTATION_PA_LEVEL = "Rotation PA level"
    ROTATION_IS_LEVEL = "Rotation IS level"
    CENTER_MODELS_TRANSFORM = 'CenterModels_T'
    # Customization info
    MODEL_FOR_CUSTOMIZATION = 'Customize this model'
    MODEL_FOR_GDRIVEURL = 'Model URL in Google Drive'
    # Saving path
    SAVING_DIRECTORY = 'savingPath'
    # Saving Config file modality
    LOCAL_OR_GDRIVE = 'Local or GDrive'

    def __init__(self):
        """
        Called when the logic class is instantiated. Can be used for initializing member variables.
        """
        ScriptedLoadableModuleLogic.__init__(self)
        
    def setDefaultParameters(self, parameterNode):
        """
		Initialize parameter node with default settings.
		"""
        # Set AR marker selected
        if not parameterNode.GetParameter(self.AR_MARKER_SELECTED):
            parameterNode.SetParameter(self.AR_MARKER_SELECTED, self.AR_MARKER_SELECTED)
        # Set path to the QR model
        if not parameterNode.GetParameter(self.QR_MODEL_PATH):
            parameterNode.SetParameter(self.QR_MODEL_PATH, self.QR_MODEL_PATH)

        # Set path to images
        if not parameterNode.GetParameter(self.UI_IMAGES_PATH):
            parameterNode.SetParameter(self.UI_IMAGES_PATH, self.UI_IMAGES_PATH)            
        # Vuforia Image
        if not parameterNode.GetParameter(self.VUFORIA_IMAGENAME):
            parameterNode.SetParameter(self.VUFORIA_IMAGENAME, self.VUFORIA_IMAGENAME)
        # QR code image
        if not parameterNode.GetParameter(self.QR_IMAGENAME):
            parameterNode.SetParameter(self.QR_IMAGENAME, self.QR_IMAGENAME)

        # Set path to the AR marker model
        if not parameterNode.GetParameter(self.AR_VUFORIA_MODEL_PATH):
            parameterNode.SetParameter(self.AR_VUFORIA_MODEL_PATH, self.AR_VUFORIA_MODEL_PATH)

        # Set initial size of the QR code
        if not parameterNode.GetParameter(self.QR_MODEL_INITIAL_SIZE):
            parameterNode.SetParameter(self.QR_MODEL_INITIAL_SIZE, self.QR_MODEL_INITIAL_SIZE)

        # Set temptative new size of the QR code
        if not parameterNode.GetParameter(self.QR_MODEL_NEW_SIZE):
            parameterNode.SetParameter(self.QR_MODEL_NEW_SIZE, self.QR_MODEL_INITIAL_SIZE)

        # Set  the name of the QR model: White
        if not parameterNode.GetParameter(self.QR_MODEL_NAME_WHITE):
            parameterNode.SetParameter(self.QR_MODEL_NAME_WHITE, self.QR_MODEL_NAME_WHITE)
        # Set  the name of the QR model: Black
        if not parameterNode.GetParameter(self.QR_MODEL_NAME_BLACK):
            parameterNode.SetParameter(self.QR_MODEL_NAME_BLACK, self.QR_MODEL_NAME_BLACK)

        # Set  the name of the QR model: White
        if not parameterNode.GetParameter(self.AR_VUFORIA_NAME_WHITE):
            parameterNode.SetParameter(self.AR_VUFORIA_NAME_WHITE, self.AR_VUFORIA_NAME_WHITE)
        # Set  the name of the QR model: Black
        if not parameterNode.GetParameter(self.AR_VUFORIA_NAME_BLACK):
            parameterNode.SetParameter(self.AR_VUFORIA_NAME_BLACK, self.AR_VUFORIA_NAME_BLACK)

        # Max number of models
        if not parameterNode.GetParameter(self.MAX_NUMBER_OF_MODELS):
            parameterNode.SetParameter(self.MAX_NUMBER_OF_MODELS, self.MAX_NUMBER_OF_MODELS)
        
        # Set Translate LR
        if not parameterNode.GetParameter(self.SCALE_LEVEL):
            parameterNode.SetParameter(self.SCALE_LEVEL, "100.0")
        # Set Translate LR
        if not parameterNode.GetParameter(self.TRASLATION_LR_LEVEL):
            parameterNode.SetParameter(self.TRASLATION_LR_LEVEL, "0.0")
        # Set Translate PA
        if not parameterNode.GetParameter(self.TRASLATION_PA_LEVEL):
            parameterNode.SetParameter(self.TRASLATION_PA_LEVEL, "0.0")
        # Set Translate IS
        if not parameterNode.GetParameter(self.TRASLATION_IS_LEVEL):
            parameterNode.SetParameter(self.TRASLATION_IS_LEVEL, "0.0")
        # Set Rotate LR
        if not parameterNode.GetParameter(self.ROTATION_LR_LEVEL):
            parameterNode.SetParameter(self.ROTATION_LR_LEVEL, "0.0")
        # Set Rotate PA
        if not parameterNode.GetParameter(self.ROTATION_PA_LEVEL):
            parameterNode.SetParameter(self.ROTATION_PA_LEVEL, "0.0")
        # Set Rotate IS
        if not parameterNode.GetParameter(self.ROTATION_IS_LEVEL):
            parameterNode.SetParameter(self.ROTATION_IS_LEVEL, "0.0")

        # Set Config file configuration
        if not parameterNode.GetParameter(self.LOCAL_OR_GDRIVE):
            parameterNode.SetParameter(self.LOCAL_OR_GDRIVE, "GDrive")
                                
        pass
    
    def setupScene(self):
        """
        Set up the scene
        """
        parameterNode = self.getParameterNode()

        # If modelsTransform is not in the scene, create and add it
        modelsTransform = slicer.util.getFirstNodeByName(self.MODELS_TRANSFORM)  # ***
        if modelsTransform is None:
            modelsTransform = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLinearTransformNode', self.MODELS_TRANSFORM)
            parameterNode.SetNodeReferenceID(self.MODELS_TRANSFORM, modelsTransform.GetID())

        centermodelsTransform = slicer.util.getFirstNodeByName(self.CENTER_MODELS_TRANSFORM)  # ***
        if centermodelsTransform is None:
            centermodelsTransform = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLinearTransformNode', self.CENTER_MODELS_TRANSFORM)
            parameterNode.SetNodeReferenceID(self.CENTER_MODELS_TRANSFORM, centermodelsTransform.GetID())

    def process(self,
                inputVolume: vtkMRMLScalarVolumeNode,
                outputVolume: vtkMRMLScalarVolumeNode,
                imageThreshold: float,
                invert: bool = False,
                showResult: bool = True) -> None:
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """

        if not inputVolume or not outputVolume:
            raise ValueError("Input or output volume is invalid")

        import time
        startTime = time.time()
        logging.info('Processing started')

        # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
        cliParams = {
            'InputVolume': inputVolume.GetID(),
            'OutputVolume': outputVolume.GetID(),
            'ThresholdValue': imageThreshold,
            'ThresholdType': 'Above' if invert else 'Below'
        }
        cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
        # We don't need the CLI module node anymore, remove it to not clutter the scene with it
        slicer.mrmlScene.RemoveNode(cliNode)

        stopTime = time.time()
        logging.info(f'Processing completed in {stopTime-startTime:.2f} seconds')

    def LoadModelFromFile(self, modelFilePath, modelFileName, colorRGB_array, visibility_bool):
        """
        Load the model "modelFileName" from the specified folder. Set its color to colorRGB_array and enable its visibility according to visibility_bool
        """
        # get the path fro msettings 
        settings = slicer.app.userSettings()
        try:
          node = slicer.util.getNode(modelFileName)
        except:
          node = slicer.util.loadModel(os.path.join(modelFilePath, modelFileName))
          node.GetModelDisplayNode().SetColor(colorRGB_array)
          node.GetModelDisplayNode().SetVisibility(visibility_bool)
          #print (modelFileName + ' model loaded')
        return node
    
    def loadModels(self, modelPath):
      """
      Load Models into scene
      """
      model_name = modelPath.split("/")[-1]

      if model_name not in self.MODELS_DICT.keys():
        self.MODELS_DICT[model_name] = dict()

        self.MODELS_DICT[model_name]["path"] = modelPath

        self.MODELS_DICT[model_name]["node"] = self.loadNewModel(modelPath, color_code=self.color_code())
      
        # Center 3D view
        self.center3DView()

        print("New Model loaded.")

        return model_name

      else:
        print("Model already loaded.")
        self.ui.ErrorInMaxNumOfModels_Label.text = "Model already loaded"
        return None

    def scaleQRModel(self, model, initialSize, newSize):
        scaleTransformName = "QRScale_T"
        scaleFactor = newSize/initialSize
        print("Scale factor: " + str(scaleFactor))

        # Create scaling matrix
        scaleMatrix = vtk.vtkMatrix4x4()
        scaleMatrix.Identity()
        scaleMatrix.SetElement(0, 0, scaleFactor)
        scaleMatrix.SetElement(1, 1, scaleFactor)
        scaleMatrix.SetElement(2, 2, scaleFactor)
 
        # Set the matrix to the transform
        scaleTransform = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLinearTransformNode', scaleTransformName)
        scaleTransform.SetMatrixTransformToParent(scaleMatrix)

        self.ApplyTransformToObject(model, scaleTransformName)
        model.HardenTransform()
        #slicer.mrmlScene.RemoveNode(slicer.util.getNode(scaleTransformName))
    
    def loadNewModel(self, path, color_code=[0,0.5,0]):
      """
      """
      try:
        model = slicer.util.loadModel(path)
        model.GetModelDisplayNode().SetColor(color_code)
      except:
        print("[LOADMODEL]ERROR: Path do not exist: {}".format(path))
        model = None

      return model

    def removeModel(self, model_name):
      """
      """
      if model_name in self.MODELS_DICT.keys():
        model_node = self.MODELS_DICT[model_name]["node"]
        slicer.mrmlScene.RemoveNode(model_node)
        self.MODELS_DICT.pop(model_name, None)
        self.center3DView()

    def moveModelsToOrigin(self):
      """
      Move models to origin
      """
      parameterNode = self.getParameterNode()

      # Get Centermodelstransform from parameternode
      centerModelsTransform = parameterNode.GetNodeReference(self.CENTER_MODELS_TRANSFORM)

      box = np.zeros(6)

      # Get Bounding box of all models
      for i, model_name in enumerate(self.MODELS_DICT.keys()):
        modelNode = self.MODELS_DICT[model_name]["node"]
        a = np.zeros(6)
        modelNode.GetRASBounds(a)
        if i == 0:
          box = a
        else:
          minimums = np.minimum(box, a)
          maximums = np.maximum(box, a)
          box[[0,2,4]] = minimums[[0,2,4]]
          box[[1,3,5]] = maximums[[1,3,5]]
        print(a)
        modelNode.SetAndObserveTransformNodeID(centerModelsTransform.GetID())
      print(box)

      # Create Move to Origin Transform from box
      center = self.get_center_from_box(box)
      vTransform = vtk.vtkTransform()
      vTransform.Translate(-center[0],-center[1],-center[2]) 
      centerModelsTransform.SetMatrixTransformToParent(vTransform.GetMatrix())

      # Harden models
      for i, model_name in enumerate(self.MODELS_DICT.keys()):
        modelNode = self.MODELS_DICT[model_name]["node"]
        modelNode.HardenTransform()

      # Move models within MODELS_TRANSFORM
      modelsTransformNode = parameterNode.GetNodeReference(self.MODELS_TRANSFORM)
      modelsTrasnformName = modelsTransformNode.GetName()
      self.ApplyTransformToAllModels(modelsTrasnformName)

      # Center 3D view
      self.center3DView()
     
    def get_center_from_box(self, box):
        center = [0.0, 0.0, 0.0]
        center[0] = box[[0,1]].mean()
        center[1] = box[[2,3]].mean()
        center[2] = box[[4,5]].mean()
        return center

    def ApplyTransformToAllModels(self, transformName):
        """
        """
        for i, model_name in enumerate(self.MODELS_DICT.keys()):
            modelNode = self.MODELS_DICT[model_name]["node"]
            self.ApplyTransformToObject(modelNode, transformName)
    
    def updateTransformFromParameterNode(self):
        """
        Update the transform from the parameter node
        """
        parameterNode = self.getParameterNode()

        # apply the translation and rotation in the world frame: ROTATION_LR_LEVEL, ROTATION_PA_LEVEL, ROTATION_IS_LEVEL
        modelsTransform = vtk.vtkTransform()
        modelsTransform.Scale(((float(parameterNode.GetParameter(self.SCALE_LEVEL)))/100),
                             ((float(parameterNode.GetParameter(self.SCALE_LEVEL)))/100),
                             ((float(parameterNode.GetParameter(self.SCALE_LEVEL)))/100))
        modelsTransform.Translate(float(parameterNode.GetParameter(self.TRASLATION_LR_LEVEL)),
                             float(parameterNode.GetParameter(self.TRASLATION_PA_LEVEL)),
                             float(parameterNode.GetParameter(self.TRASLATION_IS_LEVEL)))
        modelsTransform.RotateX(float(parameterNode.GetParameter(self.ROTATION_LR_LEVEL)))
        modelsTransform.RotateY(float(parameterNode.GetParameter(self.ROTATION_PA_LEVEL))) 
        modelsTransform.RotateZ(float(parameterNode.GetParameter(self.ROTATION_IS_LEVEL)))
        
        # Set the transform to the parameter node        
        modelsTransformNode = parameterNode.GetNodeReference(self.MODELS_TRANSFORM)
        if modelsTransformNode is not None:
            modelsTransformNode.SetAndObserveTransformToParent(modelsTransform)
        else:
            logging.warning("Models transform not selected yet")

    def center3DView(self):
        """
        """
        # Center 3D view
        layoutManager = slicer.app.layoutManager()
        threeDWidget = layoutManager.threeDWidget(0)
        threeDView = threeDWidget.threeDView()
        threeDView.resetFocalPoint()

    def SaveModels(self, save_folder_path):
        """
        """
        for i, model_name in enumerate(self.MODELS_DICT.keys()):
            modelNode = self.MODELS_DICT[model_name]["node"]
            # make a copy of the model and apply the transforms
            modelNode_copy,hardened_transform = self.copyAndHardenModel(modelNode)
            # save model
            modelName = modelNode.GetAttribute("Name")
            file_name = "{}.obj".format(modelName.split(".")[0])      
            path_aux = os.path.join(save_folder_path, file_name)
            slicer.util.saveNode(modelNode_copy, path_aux)
            # undo transforms in model
            hardened_transform.Inverse()
            modelNode_copy.SetAndObserveTransformNodeID(hardened_transform.GetID())
            modelNode_copy.HardenTransform()
            slicer.mrmlScene.RemoveNode(modelNode_copy)
            slicer.mrmlScene.RemoveNode(hardened_transform)

        print('All models have been saved.')
    
    def copyAndHardenModel(self, originalModel):
        # copy model
        outputModel = slicer.vtkMRMLModelNode()
        fullPolyData = originalModel.GetPolyData()
        outputModel.SetAndObservePolyData(fullPolyData)
        md2 = slicer.vtkMRMLModelDisplayNode()
        slicer.mrmlScene.AddNode(outputModel)
        slicer.mrmlScene.AddNode(md2)
        outputModel.SetAndObserveDisplayNodeID(md2.GetID())
        md2.SetVisibility(0)
        # apply transforms tree to copied model
        parent_transform = originalModel.GetParentTransformNode()
        try:
            t = slicer.util.getNode('DefinedTransform')
            identityTransform = vtk.vtkMatrix4x4()
            t.SetMatrixTransformToParent(identityTransform)
        except:
            t=slicer.vtkMRMLLinearTransformNode()
            t.SetName('DefinedTransform')
            slicer.mrmlScene.AddNode(t)
        t.SetAndObserveTransformNodeID(parent_transform.GetID())
        t.HardenTransform()
        outputModel.SetAndObserveTransformNodeID(t.GetID())
        outputModel.HardenTransform()
        return outputModel,t

    def saveDataNode(self, node_name, folder_path, file_name):
        # Save node to path
        node = slicer.util.getNode(node_name)
        path = os.path.join(folder_path, file_name)
        return slicer.util.saveNode(node, path)

    def color_code(self):
        color_code, reset = self.get_color_code(self.color_code_i)

        if reset:
            self.color_code_i = 0
        else:
            self.color_code_i += 1

        return color_code

    def get_color_code(self, id):
        reset = False
        color_codes = [
        [0.5, 0.0, 0.0],
        [0.0, 0.5, 0.0],
        [0.0, 0.0, 0.5],
        [0.5, 0.5, 0.0],
        [0.0, 0.5, 0.5],
        [0.5, 0.0, 0.5],
        [0.5, 0.5, 0.5]
        ]
        if id == (len(color_codes)-1):
            reset = True

        return color_codes[id], reset
         
    def hardenAllModels(self):
        for i, model_name in enumerate(self.MODELS_DICT.keys()):
            modelNode = self.MODELS_DICT[model_name]["node"]
            modelNode.HardenTransform()
        
    def ApplyTransformToObject(self, object, transformName):
        """
		Apply "transformName" transform to "object"
		"""

		# Get transform
        transform  = self.getOrCreateTransform(transformName)
        
        object.SetAndObserveTransformNodeID(transform.GetID())
        
        print ('Transform ' + transformName + ' applied to ' + object.GetName())
        
        return transform
    
    def getOrCreateTransform(self, transformName):
        """
        Gets existing tranform or create new transform containing the identity matrix.
        """
        try:
            transformNode = slicer.util.getNode(transformName)
        except:
            print('ERROR: Transformation node {} was not found. Creating node as identity...'.format(transformName))
            transformNode = slicer.vtkMRMLLinearTransformNode()
            transformNode.SetName(transformName)
            slicer.mrmlScene.AddNode(transformNode)

        return transformNode

    def loadModelFromFile(self, modelName, modelFilePath, color=None, visibility_bool=True):
        if color is None:
            color = [0, 0, 0]

        try:
            modelNode = slicer.util.getNode(modelName)
        except:
            try:
                modelNode = slicer.util.loadModel(modelFilePath)

                modelNode.GetModelDisplayNode().SetColor(color)
                modelNode.GetModelDisplayNode().SetVisibility(visibility_bool)
                print('Model loaded: {}'.format(modelName))
            except:
                print('ERROR: {} model not found in path: {}'.format(modelName, modelFilePath))
                modelNode = None
        return modelNode

    def ChangeColorOfSelectedModel(self, selectedColor):
        """
		Change color of the selected model.
		"""
        parameterNode = self.getParameterNode()
        selectedModelNode = parameterNode.GetNodeReference(self.MODEL_FOR_CUSTOMIZATION)
        colorRGB = [selectedColor.redF(), selectedColor.greenF(), selectedColor.blueF()]
        selectedModelNode.GetModelDisplayNode().SetColor(colorRGB)
            
    def SaveColors(self):
        for i, model_name in enumerate(self.MODELS_DICT.keys()):
            modelNode = self.MODELS_DICT[model_name]["node"]
            current_color = modelNode.GetModelDisplayNode().GetColor()
            modelColor = str(qt.QColor(current_color[0] * 255, current_color[1] * 255, current_color[2] * 255))
            modelNode.SetAttribute("Color", modelColor)
    
    def ChangeNameAttributeOfTheSelectedModel(self, modelName):
        """
		Change name attribute of the selected model.
		"""
        parameterNode = self.getParameterNode()
        selectedModelNode = parameterNode.GetNodeReference(self.MODEL_FOR_CUSTOMIZATION)
        selectedModelNode.SetAttribute("Name", modelName)
        selectedModelNode.SetAttribute("URL", "")

    def ChangeGDriveURLofSelectedModel(self, driveurl):
        """
		Change google drive url of the selected model and add it as attribute.
		"""
        parameterNode = self.getParameterNode()
        selectedModelNode = parameterNode.GetNodeReference(self.MODEL_FOR_GDRIVEURL)
        selectedModelNode.SetAttribute("URL", driveurl)

    def SaveData(self):
        """
		Save the data in the scene.
		"""
        parameterNode = self.getParameterNode()

		# Get the Save Directory from slicer settings
        settings = slicer.app.userSettings()
        save_folder_path = settings.value(self.SAVING_DIRECTORY)
        
		# Extract data data
        currentDate = time.strftime("%Y-%m-%d_%H-%M-%S")
				
		# Create the saving folder if it doesn't exist
        if not (os.path.exists(save_folder_path)):
            os.makedirs(save_folder_path)


		## Save the scene
		# Generate file name
        sceneName = "{}_{}".format(currentDate, "3DSlicerScene")
        sceneSaveFilename = os.path.join(save_folder_path, sceneName + ".mrb")
		# Save scene
        if slicer.util.saveScene(sceneSaveFilename):
            logging.info("Scene saved to: {0}".format(sceneSaveFilename))
        else:
            logging.error("Scene saving failed")

        ## Save transform
        self.SavePoseTransformDataNode(save_folder_path) 

        ## Save models all biomodels
        self.SaveModels(save_folder_path)

        ## Save QR code models
        #self.SaveQRModels(save_folder_path)

        return save_folder_path

    def CreateJSONfileWithModelsInfo(self, save_folder_path):

        parameterNode = self.getParameterNode()

        ### MODELS TRANSFORM
        #modelsTransformNode = parameterNode.GetNodeReference(self.MODELS_TRANSFORM)
        #fromModelToMarkerTransformArray = self.GetArrayFromTransform(self.finalTransform)

        ### Will the models be saved locally or via Google Drive?
        localOrGDrive = parameterNode.GetNodeReference(self.LOCAL_OR_GDRIVE)

        ### CREATE JSON FILE
        json_path = os.path.join(save_folder_path, 'ConfigurationFile.json')
        with open(json_path, 'w') as json_file:
            json_data = {}  # Create a dictionary to store all lines

            # Save models transform array into the json file
            #json_data["model_position_with_respect_to_qr_code"] = fromModelToMarkerTransformArray ## We are not saving the transform anymore
            # Save the selected AR marker option (either QR or Vuforia)
            ar_marker_selected = parameterNode.GetParameter(self.AR_MARKER_SELECTED)
            json_data["tracking_option"] = ar_marker_selected
            # Save models intrinsic parameters (name, color and url) into the json file
            for i, model_name in enumerate(self.MODELS_DICT.keys()):
                modelNode = self.MODELS_DICT[model_name]["node"]
                modelName = modelNode.GetAttribute("Name")
                modelColor = modelNode.GetAttribute("Color")
                if (localOrGDrive == "GDrive"): # If the models are uploaded to GDrive, find their URL
                    modelURL = modelNode.GetAttribute("URL")
                    downloadLink = self.DirectDownloadLinkGenerator(modelURL)
                else: # If the models are uploaded locally, create a fake text to place in the JSON file within the URL category to prevent crashes in the app
                    modelURL = "ModelURL"
                    downloadLink = "ThisIsAnAuxNonSenseTextDontErase"    

                if (modelName and modelColor and modelURL):
                    # Create dictionary entries for each model
                    model_data = {
                        f"model{i+1}_url": downloadLink,
                        f"model{i+1}_name": modelName,
                        f"model{i+1}_material_color": modelColor
                    }
                    json_data.update(model_data)
                else:
                    print("Some data is missing in the node: " + modelNode.GetName())

            # Fill out the remaining entries (up to MAX_NUMBER_OF_MODELS) with empty data
            maxNumOfModels = int(parameterNode.GetParameter(self.MAX_NUMBER_OF_MODELS))
            for index in range(i+2, maxNumOfModels + 1): # add +2 to the i so that it starts in the correct point and +1 to the maxNumOfModels so that the las iteration is when index=maxNumOfModels
                model_data = {
                f"model{index}_url": "",
                f"model{index}_name": "",
                f"model{index}_material_color": ""
                }
                json_data.update(model_data)

            # Write the entire dictionary to the JSON file
            json.dump(json_data, json_file, indent=2)  # Add indent for better readability

            # No need to close the file explicitly; it's closed automatically when the 'with' block exits

    def SavePoseTransformDataNode(self, save_folder_path):
        # Create a new transform with the overall transform
        # Introduce it within centerModelsTransform and that one within MODELS_TRANSFORM. Finally, Harden it to save the overall pose of the models
        parameterNode = self.getParameterNode()

        # get transforms from parameter node
        modelsTransformNode = parameterNode.GetNodeReference(self.MODELS_TRANSFORM) # get models transform
        centerModelsTransformNode = parameterNode.GetNodeReference(self.CENTER_MODELS_TRANSFORM) # get center models transform

        # Create the final transform node
        finalTransformName = "fromModelToMarkerTransform.h5"
        # if a previous node with the same name exists, delete it
        try:
            previousFinalTransform = slicer.util.getNode(finalTransformName)
            previousFinalTransform.delete()
        except:
            pass            

        # now, create it and add it to the scene
        self.finalTransform = slicer.vtkMRMLTransformNode() # create a new transform that will represent the overall transform of the models from their first import to the final pose
        slicer.mrmlScene.AddNode(self.finalTransform)
        self.finalTransform.SetAndObserveTransformNodeID(centerModelsTransformNode.GetID()) # introduce this transform as a child of the centermodelstransform
        centerModelsTransformNode.SetAndObserveTransformNodeID(modelsTransformNode.GetID()) # introduce this transform as a child of the modelstransform
        self.finalTransform.HardenTransform() # harden everything        
        self.finalTransform.SetName(finalTransformName.split('.')[0])
        # Save the data node
        self.saveDataNode(self.finalTransform.GetName(), save_folder_path, finalTransformName)                    
    
    def SaveQRModels(self, save_folder_path):
        parameterNode = self.getParameterNode()
        
        qrSize = str(parameterNode.GetParameter(self.QR_MODEL_NEW_SIZE)) # Get scaling factor to add it in the name of the models
        # Save white QR model
        qrCodeWhite_Name = parameterNode.GetParameter(self.QR_MODEL_NAME_WHITE)
        qrCodeWhite_fileName = "QRcodeWhite_{}mm.obj".format(qrSize)
        self.saveDataNode(qrCodeWhite_Name, save_folder_path, qrCodeWhite_fileName)
        # Save black QR model
        qrCodeBlack_Name = parameterNode.GetParameter(self.QR_MODEL_NAME_BLACK)
        qrCodeBlack_fileName = "QRcodeBlack_{}mm.obj".format(qrSize)
        self.saveDataNode(qrCodeBlack_Name, save_folder_path, qrCodeBlack_fileName)


    def GetArrayFromTransform(self, transform_node):
        transf_list = []
        transform_matrix = vtk.vtkMatrix4x4()
        transform_node.GetMatrixTransformToWorld(transform_matrix)
        for row in np.arange(4):
            for column in np.arange(4):
                transf_list.append(transform_matrix.GetElement(row,column))
        list2str = str(transf_list)
        clearlist = list2str.replace(',','')
        final_file_content = clearlist[1:-1]
        return final_file_content
    
    def DirectDownloadLinkGenerator(self, input_link):
        input_link = input_link[32:]
        end = input_link.index('/')
        ID = input_link[:end]
        download_link = 'https://drive.google.com/uc?export=download&id='+ID
        return download_link