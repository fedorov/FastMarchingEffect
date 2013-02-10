
# assume i is the input volume, l is the output label image
# assume seeds is the list of seed points

volumes = slicer.mrmlScene.GetNodesByClass('vtkMRMLScalarVolumeNode')
v = volumes.GetItemAsObject(0)
i = v.GetImageData()
vl = slicer.modules.volumes.logic().CreateAndAddLabelVolume(slicer.mrmlScene, v, v.GetName()+'fm_label')
l = vl.GetImageData()

seeds = [ [141,128,63], [147,128,68], [142,128,55] ]

fm = slicer.logic.vtkPichonFastMarching()
scalarRange = i.GetScalarRange()
spacing = i.GetSpacing()
dim = i.GetWholeExtent()
depth = scalarRange[1]-scalarRange[0]
fm.init(dim[1]+1, dim[3]+1, dim[5]+1, depth, 1, 1, 1)
fm.SetInput(i)
fm.SetOutput(l)

fm.setNPointsEvolution(100000)
fm.setActiveLabel(1)
for s in seeds:
  fm.addSeedIJK(s[0],s[1],s[2])

fm.Modified()
fm.Update()

fm.show(1)
fm.Modified()
fm.Update()


