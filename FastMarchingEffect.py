import os
from __main__ import vtk, qt, ctk, slicer
import EditorLib
from EditorLib.EditOptions import HelpButton
from EditorLib.EditOptions import EditOptions
from EditorLib import EditUtil
from EditorLib import Effect

#
# The Editor Extension itself.
#
# This needs to define the hooks to be come an editor effect.
#

#
# FastMarchingEffectOptions - see LabelEffect, EditOptions and Effect for superclasses
#

class FastMarchingEffectOptions(Effect.EffectOptions):
  """ FastMarchingEffect-specfic gui
  """

  def __init__(self, parent=0):
    super(FastMarchingEffectOptions,self).__init__(parent)

    # self.attributes should be tuple of options:
    # 'MouseTool' - grabs the cursor
    # 'Nonmodal' - can be applied while another is active
    # 'Disabled' - not available
    # self.attributes = ('MouseTool')
    self.displayName = 'FastMarchingEffect Effect'

  def __del__(self):
    super(FastMarchingEffectOptions,self).__del__()

  def create(self):
    super(FastMarchingEffectOptions,self).create()

    self.marcherLabel = qt.QLabel('March:',self.frame)
    self.marcherLabel.setToolTip('March over the front propagation timeline')
    self.frame.layout().addWidget(self.marcherLabel)
    self.widgets.append(self.marcherLabel)

    self.marcher = ctk.ctkSliderWidget(self.frame)
    self.marcher.minimum = 0
    self.marcher.maximum = 1
    self.marcher.singleStep = 0.01
    self.frame.layout().addWidget(self.marcher)
    self.widgets.append(self.marcher)
    self.marcher.connect('valueChanged(double)',self.onMarcherChanged)

    self.apply = qt.QPushButton("Apply", self.frame)
    self.apply.setToolTip("Apply the extension operation")
    self.frame.layout().addWidget(self.apply)
    self.widgets.append(self.apply)

    HelpButton(self.frame, "This is a sample with no real functionality.")

    self.apply.connect('clicked()', self.onApply)

    # Add vertical spacer
    self.frame.layout().addStretch(1)

  def destroy(self):
    super(FastMarchingEffectOptions,self).destroy()

  # note: this method needs to be implemented exactly as-is
  # in each leaf subclass so that "self" in the observer
  # is of the correct type
  def updateParameterNode(self, caller, event):
    node = EditUtil.EditUtil().getParameterNode()
    if node != self.parameterNode:
      if self.parameterNode:
        node.RemoveObserver(self.parameterNodeTag)
      self.parameterNode = node
      self.parameterNodeTag = node.AddObserver(vtk.vtkCommand.ModifiedEvent, self.updateGUIFromMRML)

  def setMRMLDefaults(self):
    super(FastMarchingEffectOptions,self).setMRMLDefaults()

  def updateGUIFromMRML(self,caller,event):
    super(FastMarchingEffectOptions,self).updateGUIFromMRML(caller,event)
    self.disconnectWidgets()
    # TODO: get the march parameter from the node
    # march = float(self.parameterNode.GetParameter

    self.connectWidgets()

  def onApply(self):
    print('This is just an example - nothing here yet')

    try:
      tool = self.tools[0]
      tool.apply()
    except IndexError:
      print('No tools available!')
      pass
    
    self.defaultEffect()

  def onMarcherChanged(self,value):
    print('Marcher changed!')
    try:
      tool = self.tools[0]
      tool.updateLabel(value)
    except IndexError:
      print('No tools available!')
      pass

  def updateMRMLFromGUI(self):
    if self.updatingGUI:
      return
    disableState = self.parameterNode.GetDisableModifiedEvent()
    self.parameterNode.SetDisableModifiedEvent(1)
    super(FastMarchingEffectOptions,self).updateMRMLFromGUI()
    self.parameterNode.SetDisableModifiedEvent(disableState)
    if not disableState:
      self.parameterNode.InvokePendingModifiedEvent()


#
# FastMarchingEffectTool
#

class FastMarchingEffectTool(Effect.EffectTool):
  """
  One instance of this will be created per-view when the effect
  is selected.  It is responsible for implementing feedback and
  label map changes in response to user input.
  This class observes the editor parameter node to configure itself
  and queries the current view for background and label volume
  nodes to operate on.
  """

  def __init__(self, sliceWidget):
    super(FastMarchingEffectTool,self).__init__(sliceWidget)

    self.fm = None

  def cleanup(self):
    super(FastMarchingEffectTool,self).cleanup()

  def processEvent(self, caller=None, event=None):
    """
    handle events from the render window interactor
    """
    pass

    if event == "LeftButtonPressEvent":
      xy = self.interactor.GetEventPosition()
      sliceLogic = self.sliceWidget.sliceLogic()
      logic = FastMarchingEffectLogic(sliceLogic)
      logic.apply(xy)
      print("Got a %s at %s in %s", (event,str(xy),self.sliceWidget.sliceLogic().GetSliceNode().GetName()))
      self.abortEvent(event)
    else:
      pass

  def apply(self):

    # allocate a new filter each time apply is hit
    bgImage = self.editUtil.getBackgroundImage()
    labelImage = self.editUtil.getLabelImage()

    # collect seeds
    dim = bgImage.GetWholeExtent()
    print('Image extent: '+str(dim))
    seeds = []
    seeds = [ [141,128,63], [147,128,68], [142,128,55] ]
    '''
    for i in range(dim[1]+1):
      for j in range(dim[3]+1):
        for k in range(dim[5]+1):
          labelValue = labelImage.GetScalarComponentAsFloat(i,j,k,0)
          if labelValue:
            print('Adding seed at ('+str(i)+','+str(j)+','+str(k)+')')
            seeds.append([i,j,k])
    '''

    # initialize the filter
    self.fm = slicer.logic.vtkPichonFastMarching()
    scalarRange = bgImage.GetScalarRange()
    depth = scalarRange[1]-scalarRange[0]
    print('Input scalar range: '+str(depth))
    self.fm.init(dim[1]+1, dim[3]+1, dim[5]+1, depth, 1, 1, 1)
    self.fm.SetInput(bgImage)
    self.fm.SetOutput(labelImage)

    self.fm.setNPointsEvolution(100000)
    print('Setting active label to '+str(self.editUtil.getLabel()))
    self.fm.setActiveLabel(self.editUtil.getLabel())

    # use all initialized points in the label volume as seeds
    for s in seeds:
      print('FM adds seed '+str(s))
      self.fm.addSeedIJK(s[0],s[1],s[2])

    self.fm.Modified()
    self.fm.Update()

    self.fm.show(1)
    self.fm.Modified()
    self.fm.Update()

    output = self.fm.GetOutput()
    print('FastMarching output image: '+str(output))
    
    print('FastMarching apply update completed')

  def updateLabel(self,value):
    if not self.fm:
      return
    self.fm.show(value)
    self.fm.Modified()
    self.fm.Update()

    print('FastMarching updated!')

#
# FastMarchingEffectLogic
#

class FastMarchingEffectLogic(Effect.EffectLogic):
  """
  This class contains helper methods for a given effect
  type.  It can be instanced as needed by an FastMarchingEffectTool
  or FastMarchingEffectOptions instance in order to compute intermediate
  results (say, for user feedback) or to implement the final
  segmentation editing operation.  This class is split
  from the FastMarchingEffectTool so that the operations can be used
  by other code without the need for a view context.
  """

  def __init__(self,sliceLogic):
    self.sliceLogic = sliceLogic

  def apply(self,xy):
    pass


#
# The FastMarchingEffectExtension class definition
#

class FastMarchingEffectExtension(Effect.Effect):
  """Organizes the Options, Tool, and Logic classes into a single instance
  that can be managed by the EditBox
  """

  def __init__(self):
    # name is used to define the name of the icon image resource (e.g. FastMarchingEffect.png)
    self.name = "FastMarchingEffect"
    # tool tip is displayed on mouse hover
    self.toolTip = "Paint: circular paint brush for label map editing"

    self.options = FastMarchingEffectOptions
    self.tool = FastMarchingEffectTool
    self.logic = FastMarchingEffectLogic

""" Test:

sw = slicer.app.layoutManager().sliceWidget('Red')
import EditorLib
pet = EditorLib.FastMarchingEffectTool(sw)

"""

#
# FastMarchingEffect
#

class FastMarchingEffect:
  """
  This class is the 'hook' for slicer to detect and recognize the extension
  as a loadable scripted module
  """
  def __init__(self, parent):
    parent.title = "Editor FastMarchingEffect Effect"
    parent.categories = ["Developer Tools.Editor Extensions"]
    parent.contributors = ["Andrey Fedorov (BWH)"] # insert your name in the list
    parent.helpText = """
    FastMarching segmentation based on work of Eric Pichon.
    """
    parent.acknowledgementText = """
    This editor extension was developed by
    <Author>, <Institution>
    based on work by:
    Steve Pieper, Isomics, Inc.
    based on work by:
    Jean-Christophe Fillion-Robin, Kitware Inc.
    and was partially funded by NIH grant 3P41RR013218.
    """

    # TODO:
    # don't show this module - it only appears in the Editor module
    #parent.hidden = True

    # Add this extension to the editor's list for discovery when the module
    # is created.  Since this module may be discovered before the Editor itself,
    # create the list if it doesn't already exist.
    try:
      slicer.modules.editorExtensions
    except AttributeError:
      slicer.modules.editorExtensions = {}
    slicer.modules.editorExtensions['FastMarchingEffect'] = FastMarchingEffectExtension

#
# FastMarchingEffectWidget
#

class FastMarchingEffectWidget:
  def __init__(self, parent = None):
    self.parent = parent

  def setup(self):
    # don't display anything for this widget - it will be hidden anyway
    pass

  def enter(self):
    pass

  def exit(self):
    pass


