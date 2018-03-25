#(c) 2016 R. T. LGPL: part of Flamingo tools w.b. for FreeCAD

__title__="pypeTools objects"
__author__="oddtopus"
__url__="github.com/oddtopus/flamingo"
__license__="LGPL 3"
objs=['Pipe','Elbow','Reduct','Cap','Flange','Ubolt']
metaObjs=['PypeLine','PypeBranch']

import FreeCAD, Part, frameCmd, pipeCmd

################ CLASSES ###########################

class pypeType(object):
  def __init__(self,obj):
    obj.Proxy = self
    obj.addProperty("App::PropertyString","PType","PBase","Type of tubeFeature").PType
    obj.addProperty("App::PropertyString","PRating","PBase","Rating of pipeFeature").PRating
    obj.addProperty("App::PropertyString","PSize","PBase","Nominal diameter").PSize
    obj.addProperty("App::PropertyVectorList","Ports","PBase","Ports position relative to the origin of Shape")
    obj.addProperty("App::PropertyFloat","Kv","PBase","Flow factor (m3/h/bar)").Kv

class Pipe(pypeType):
  '''Class for object PType="Pipe"
  Pipe(obj,[PSize="DN50",OD=60.3,thk=3, H=100])
    obj: the "App::FeaturePython object"
    PSize (string): nominal diameter
    OD (float): outside diameter
    thk (float): shell thickness
    H (float): length of pipe'''
  def __init__(self, obj,DN="DN50",OD=60.3,thk=3, H=100):
    # initialize the parent class
    super(Pipe,self).__init__(obj)
    # define common properties
    obj.PType="Pipe"
    obj.PRating="SCH-STD"
    obj.PSize=DN
    # define specific properties
    obj.addProperty("App::PropertyLength","OD","Pipe","Outside diameter").OD=OD
    obj.addProperty("App::PropertyLength","thk","Pipe","Wall thickness").thk=thk
    obj.addProperty("App::PropertyLength","ID","Pipe","Inside diameter").ID=obj.OD-2*obj.thk
    obj.addProperty("App::PropertyLength","Height","Pipe","Length of tube").Height=H
    obj.addProperty("App::PropertyString","Profile","Pipe","Section dim.").Profile=str(obj.OD)+"x"+str(obj.thk)
  def onChanged(self, fp, prop):
    if prop=='ID' and fp.ID<fp.OD:
      fp.thk=(fp.OD-fp.ID)/2
  def execute(self, fp):
    if fp.thk>fp.OD/2:
      fp.thk=fp.OD/2
    fp.ID=fp.OD-2*fp.thk
    fp.Profile=str(fp.OD)+"x"+str(fp.thk)
    if fp.ID:
      fp.Shape = Part.makeCylinder(fp.OD/2,fp.Height).cut(Part.makeCylinder(fp.ID/2,fp.Height))
    else:
      fp.Shape = Part.makeCylinder(fp.OD/2,fp.Height)
    fp.Ports=[FreeCAD.Vector(),FreeCAD.Vector(0,0,float(fp.Height))]
    
class Elbow(pypeType):
  '''Class for object PType="Elbow"
  Elbow(obj,[PSize="DN50",OD=60.3,thk=3,BA=90,BR=45.225])
    obj: the "App::FeaturePython" object
    PSize (string): nominal diameter
    OD (float): outside diameter
    thk (float): shell thickness
    BA (float): bend angle
    BR (float): bend radius'''
  def __init__(self, obj,DN="DN50",OD=60.3,thk=3,BA=90,BR=45.225):
    # initialize the parent class
    super(Elbow,self).__init__(obj)
    # define common properties
    obj.PType="Elbow"
    obj.PRating="SCH-STD"
    obj.PSize=DN
    # define specific properties
    obj.addProperty("App::PropertyLength","OD","Elbow","Outside diameter").OD=OD
    obj.addProperty("App::PropertyLength","thk","Elbow","Wall thickness").thk=thk
    obj.addProperty("App::PropertyLength","ID","Elbow","Inside diameter").ID=obj.OD-2*obj.thk
    obj.addProperty("App::PropertyAngle","BendAngle","Elbow","Bend Angle").BendAngle=BA
    obj.addProperty("App::PropertyLength","BendRadius","Elbow","Bend Radius").BendRadius=BR
    obj.addProperty("App::PropertyString","Profile","Elbow","Section dim.").Profile=str(obj.OD)+"x"+str(obj.thk)
    #obj.Ports=[FreeCAD.Vector(1,0,0),FreeCAD.Vector(0,1,0)]
    self.execute(obj)
  def onChanged(self, fp, prop):
    if prop=='ID' and fp.ID<fp.OD:
      fp.thk=(fp.OD-fp.ID)/2
  def execute(self, fp):
    if fp.BendAngle<180:
      if fp.thk>fp.OD/2:
        fp.thk=fp.OD/2
      fp.ID=fp.OD-2*fp.thk
      fp.Profile=str(fp.OD)+"x"+str(fp.thk)
      CenterOfBend=FreeCAD.Vector(fp.BendRadius,fp.BendRadius,0)
      ## make center-line ##
      R=Part.makeCircle(fp.BendRadius,CenterOfBend,FreeCAD.Vector(0,0,1),225-float(fp.BendAngle)/2,225+float(fp.BendAngle)/2)
      ## move the cl so that Placement.Base is the center of elbow ##
      from math import pi, cos, sqrt
      d=(fp.BendRadius*sqrt(2)-fp.BendRadius/cos(fp.BendAngle/180*pi/2))
      P=FreeCAD.Vector(-d*cos(pi/4),-d*cos(pi/4),0)
      R.translate(P)
      ## calculate Ports position ##
      fp.Ports=[R.valueAt(R.FirstParameter),R.valueAt(R.LastParameter)]
      ## make the shape of the elbow ##
      c=Part.makeCircle(fp.OD/2,fp.Ports[0],R.tangentAt(R.FirstParameter)*-1)
      b=Part.makeSweepSurface(R,c)
      p1=Part.Face(Part.Wire(c))
      p2=Part.Face(Part.Wire(Part.makeCircle(fp.OD/2,fp.Ports[1],R.tangentAt(R.LastParameter))))
      sol=Part.Solid(Part.Shell([b,p1,p2]))
      planeFaces=[f for f in sol.Faces if type(f.Surface)==Part.Plane]
      #elbow=sol.makeThickness(planeFaces,-fp.thk,1.e-3)
      #fp.Shape = elbow
      if fp.thk<fp.OD/2:
        fp.Shape=sol.makeThickness(planeFaces,-fp.thk,1.e-3)
      else:
        fp.Shape=sol

class Flange(pypeType):
  '''Class for object PType="Flange"
  Flange(obj,[PSize="DN50",FlangeType="SO", D=160, d=60.3,df=132, f=14 t=15,n=4])
    obj: the "App::FeaturePython" object
    PSize (string): nominal diameter
    FlangeType (string): type of Flange
    D (float): flange diameter
    d (float): bore diameter
    df (float): bolts holes distance
    f (float): bolts holes diameter
    t (float): flange thickness
    n (int): nr. of bolts
  '''
  def __init__(self, obj,DN="DN50",FlangeType="SO",D=160,d=60.3,df=132,f=14, t=15, n=4):
    # initialize the parent class
    super(Flange,self).__init__(obj)
    # define common properties
    obj.PType="Flange"
    obj.PRating="DIN-PN16"
    obj.PSize=DN
    # define specific properties
    obj.addProperty("App::PropertyString","FlangeType","Flange","Type of flange").FlangeType=FlangeType
    obj.addProperty("App::PropertyLength","D","Flange","Flange diameter").D=D
    obj.addProperty("App::PropertyLength","d","Flange","Bore diameter").d=d
    obj.addProperty("App::PropertyLength","df","Flange","Bolts distance").df=df
    obj.addProperty("App::PropertyLength","f","Flange","Bolts hole diameter").f=f
    obj.addProperty("App::PropertyLength","t","Flange","Thickness of flange").t=t
    obj.addProperty("App::PropertyInteger","n","Flange","Nr. of bolts").n=n
  def onChanged(self, fp, prop):
    return None
  def execute(self, fp):
    base=Part.Face(Part.Wire(Part.makeCircle(fp.D/2)))
    if fp.d>0:
      base=base.cut(Part.Face(Part.Wire(Part.makeCircle(fp.d/2))))
    if fp.n>0:
      hole=Part.Face(Part.Wire(Part.makeCircle(fp.f/2,FreeCAD.Vector(fp.df/2,0,0),FreeCAD.Vector(0,0,1))))
      hole.rotate(FreeCAD.Vector(0,0,0),FreeCAD.Vector(0,0,1),360.0/fp.n/2)
      for i in list(range(fp.n)):
        base=base.cut(hole)
        hole.rotate(FreeCAD.Vector(0,0,0),FreeCAD.Vector(0,0,1),360.0/fp.n)
    fp.Shape = base.extrude(FreeCAD.Vector(0,0,fp.t))
    fp.Ports=[FreeCAD.Vector(),FreeCAD.Vector(0,0,float(fp.t))]

class Reduct(pypeType):
  '''Class for object PType="Reduct"
  Reduct(obj,[PSize="DN50",OD=60.3, OD2= 48.3, thk=3, thk2=None, H=None, conc=True])
    obj: the "App::FeaturePython object"
    PSize (string): nominal diameter (major)
    OD (float): major outside diameter
    OD2 (float): minor outside diameter
    thk (float): major shell thickness
    thk2 (float): minor shell thickness
    H (float): length of reduction
    conc (bool): True for a concentric reduction, False for eccentric
  If thk2 is None or 0, the same thickness is used at both ends.
  If H is None or 0, the length of the reduction is calculated as 3x(OD-OD2).
    '''
  def __init__(self, obj,DN="DN50",OD=60.3,OD2=48.3,thk=3, thk2=None, H=None, conc=True):
    # initialize the parent class
    super(Reduct,self).__init__(obj)
    # define common properties
    obj.PType="Reduct"
    obj.PRating="SCH-STD"
    obj.PSize=DN
    # define specific properties
    obj.addProperty("App::PropertyLength","OD","Reduct","Major diameter").OD=OD
    obj.addProperty("App::PropertyLength","OD2","Reduct","Minor diameter").OD2=OD2
    obj.addProperty("App::PropertyLength","thk","Reduct","Wall thickness").thk=thk
    obj.addProperty("App::PropertyLength","thk2","Reduct","Wall thickness")
    if not thk2:
      obj.thk2=thk
    else:
      obj.thk2=thk2
    obj.addProperty("App::PropertyBool","calcH","Reduct","Make the lenght variable")
    obj.addProperty("App::PropertyLength","Height","Reduct","Length of reduct")
    if not H:
      obj.calcH=True
      obj.Height=3*(obj.OD-obj.OD2)
    else:
      obj.calcH=False
      obj.Height=float(H)
    obj.addProperty("App::PropertyString","Profile","Reduct","Section dim.").Profile=str(obj.OD)+"x"+str(obj.OD2)
    obj.addProperty("App::PropertyBool","conc","Reduct","Concentric or Eccentric").conc=conc
  def onChanged(self, fp, prop):
    return None
  def execute(self, fp):
    if fp.OD>fp.OD2:
      if fp.thk>fp.OD/2:
        fp.thk=fp.OD/2.1
      if fp.thk2>fp.OD2/2:
        fp.thk2=fp.OD2/2.1
      if fp.calcH or fp.Height==0:
        fp.Height=3*(fp.OD-fp.OD2)
      fp.Profile=str(fp.OD)+"x"+str(fp.OD2)
      if fp.conc:
        fp.Shape = Part.makeCone(fp.OD/2,fp.OD2/2,fp.Height).cut(Part.makeCone(fp.OD/2-fp.thk,fp.OD2/2-fp.thk2,fp.Height))
        fp.Ports=[FreeCAD.Vector(),FreeCAD.Vector(0,0,float(fp.Height))]
      else:
        C=Part.makeCircle(fp.OD/2,FreeCAD.Vector(0,0,0),FreeCAD.Vector(0,0,1))
        c=Part.makeCircle(fp.OD2/2,FreeCAD.Vector(0,0,0),FreeCAD.Vector(0,0,1))
        c.translate(FreeCAD.Vector((fp.OD-fp.OD2)/2,0,fp.Height))
        sol=Part.makeLoft([c,C],True)
        #planeFaces=[f for f in sol.Faces if type(f.Surface)==Part.Plane]
        #fp.Shape= sol.makeThickness(planeFaces,-fp.thk,1.e-3)
        C=Part.makeCircle(fp.OD/2-fp.thk,FreeCAD.Vector(0,0,0),FreeCAD.Vector(0,0,1))
        c=Part.makeCircle(fp.OD2/2-fp.thk2,FreeCAD.Vector(0,0,0),FreeCAD.Vector(0,0,1))
        c.translate(FreeCAD.Vector((fp.OD-fp.OD2)/2,0,fp.Height))
        fp.Shape=sol.cut(Part.makeLoft([c,C],True))
        fp.Ports=[FreeCAD.Vector(),FreeCAD.Vector((fp.OD-fp.OD2)/2,0,float(fp.Height))]
    
class Cap(pypeType):
  '''Class for object PType="Cap"
  Cap(obj,[PSize="DN50",OD=60.3,thk=3])
    obj: the "App::FeaturePython object"
    PSize (string): nominal diameter
    OD (float): outside diameter
    thk (float): shell thickness'''
  def __init__(self, obj,DN="DN50",OD=60.3,thk=3):
    # initialize the parent class
    super(Cap,self).__init__(obj)
    # define common properties
    obj.PType="Cap"
    obj.PRating="SCH-STD"
    obj.PSize=DN
    # define specific properties
    obj.addProperty("App::PropertyLength","OD","Cap","Outside diameter").OD=OD
    obj.addProperty("App::PropertyLength","thk","Cap","Wall thickness").thk=thk
    obj.addProperty("App::PropertyLength","ID","Cap","Inside diameter").ID=obj.OD-2*obj.thk
    obj.addProperty("App::PropertyString","Profile","Cap","Section dim.").Profile=str(obj.OD)+"x"+str(obj.thk)
  def onChanged(self, fp, prop):
    return None
  def execute(self, fp):
    if fp.thk>fp.OD/2:
      fp.thk=fp.OD/2.1
    fp.ID=fp.OD-2*fp.thk
    fp.Profile=str(fp.OD)+"x"+str(fp.thk)
    D=float(fp.OD)
    s=float(fp.thk)
    sfera=Part.makeSphere(0.8*D,FreeCAD.Vector(0,0,-(0.55*D-6*s)))
    cilindro=Part.makeCylinder(D/2,D*1.7,FreeCAD.Vector(0,0,-(0.55*D-6*s+1)),FreeCAD.Vector(0,0,1))
    common=sfera.common(cilindro)
    fil=common.makeFillet(D/6.5,common.Edges)
    cut=fil.cut(Part.makeCylinder(D*1.1,D*2,FreeCAD.Vector(0,0,0),FreeCAD.Vector(0,0,-1)))
    cap=cut.makeThickness([f for f in cut.Faces if type(f.Surface)==Part.Plane],-s,1.e-3)
    fp.Shape = cap
    fp.Ports=[FreeCAD.Vector()]
    
class PypeLine2(pypeType):
  '''Class for object PType="PypeLine2"
  This object represent a collection of objects "PType" that are updated with the 
  methods defined in the Python class.
  At present time it creates, with the method obj.Proxy.update(,obj,[edges]), pipes and curves over 
  the given edges and collect them in a group named according the object's .Label.
  PypeLine2 features also the optional attribute ".Base":
  - Base can be a Wire or a Sketch or any object which has edges in its Shape.
  - Running "obj.Proxy.update(obj)", without any [edges], the class attempts to render the pypeline 
  (Pipe and Elbow objects) on the "obj.Base" edges: for well defined geometries 
  and open paths, this usually leads to acceptable results.
  - Running "obj.Proxy.purge(obj)" deletes from the model all Pipes and Elbows 
  that belongs to the pype-line.  
  - It's possible to add other objects afterwards (such as Flange, Reduct...) 
  using the relevant insertion dialogs but remember that these won't be updated 
  when the .Base is changed and won't be deleted if the pype-line is purged.
  - If Base is None, PypeLine2 behaves like a bare container of objects, 
  with possibility to group them automatically and extract the part-list. 
  '''
  def __init__(self, obj,DN="DN50",PRating="SCH-STD",OD=60.3,thk=3,BR=None, lab=None):
    # initialize the parent class
    super(PypeLine2,self).__init__(obj)
    # define common properties
    obj.PType="PypeLine"
    obj.PSize=DN
    obj.PRating=PRating
    if lab:
      obj.Label=lab
    # define specific properties
    if not BR:
      BR=0.75*OD
    obj.addProperty("App::PropertyLength","BendRadius","PypeLine2","the radius of bending").BendRadius=BR
    obj.addProperty("App::PropertyLength","OD","PypeLine2","Outside diameter").OD=OD
    obj.addProperty("App::PropertyLength","thk","PypeLine2","Wall thickness").thk=thk
    obj.addProperty("App::PropertyString","Group","PypeLine2","The group.").Group=obj.Label+"_pieces"
    group=FreeCAD.activeDocument().addObject("App::DocumentObjectGroup",obj.Group)
    group.addObject(obj)
    FreeCAD.Console.PrintWarning("Created group "+obj.Group+"\n")
    obj.addProperty("App::PropertyLink","Base","PypeLine2","the edges")
  def onChanged(self, fp, prop):
    if prop=='Label' and len(fp.InList):
      fp.InList[0].Label=fp.Label+"_pieces"
      fp.Group=fp.Label+"_pieces"
    if hasattr(fp,'Base') and prop=='Base' and fp.Base:
      FreeCAD.Console.PrintWarning(fp.Label+' Base has changed to '+fp.Base.Label+'\n')
    if prop=='OD':
      fp.BendRadius=0.75*fp.OD
  def purge(self,fp):
    group=FreeCAD.activeDocument().getObjectsByLabel(fp.Group)[0]
    for o in group.OutList:
      if hasattr(o,'PType') and o.PType in ['Pipe','Elbow']:
        FreeCAD.activeDocument().removeObject(o.Name)
  def update(self,fp,edges=None):
    import pipeCmd, frameCmd
    from DraftVecUtils import rounded
    from math import degrees
    if not edges and hasattr(fp.Base,'Shape'):
      edges=fp.Base.Shape.Edges
      if not edges:
        FreeCAD.Console.PrintError('Base has not valid edges\n')
        return
    pipes=list()
    for e in edges:
      #---Create the tube---
      p=pipeCmd.makePipe([fp.PSize,fp.OD,fp.thk,e.Length],pos=e.valueAt(0),Z=e.tangentAt(0))
      p.PRating=fp.PRating
      p.PSize=fp.PSize
      pipeCmd.moveToPyLi(p,fp.Label)
      pipes.append(p)
      n=len(pipes)-1
      if n and not frameCmd.isParallel(frameCmd.beamAx(pipes[n]),frameCmd.beamAx(pipes[n-1])):
        #---Create the curve---
        propList=[fp.PSize,fp.OD,fp.thk,90,fp.BendRadius]
        c=pipeCmd.makeElbowBetweenThings(edges[n],edges[n-1],propList)
        portA,portB=[c.Placement.multVec(port) for port in c.Ports]
        #---Trim the tube---
        p1,p2=pipes[-2:]
        frameCmd.extendTheBeam(p1,portA)
        frameCmd.extendTheBeam(p2,portB)
        pipeCmd.moveToPyLi(c,fp.Label)
  def execute(self, fp):
    return None

class ViewProviderPypeLine:
  def __init__(self,vobj):
    vobj.Proxy = self
  def getIcon(self):
    from os.path import join, dirname, abspath
    return join(dirname(abspath(__file__)),"icons","pypeline.svg")
  def attach(self, vobj):
    self.ViewObject = vobj
    self.Object = vobj.Object

class Ubolt():
  '''Class for object PType="Clamp"
  UBolt(obj,[PSize="DN50",ClampType="U-bolt", C=76, H=109, d=10])
    obj: the "App::FeaturePython" object
    PSize (string): nominal diameter
    ClampType (string): the clamp type or standard
    C (float): the diameter of the U-bolt
    H (float): the total height of the U-bolt
    d (float): the rod diameter
  '''
  def __init__(self, obj,DN="DN50",ClampType="DIN-UBolt", C=76, H=109, d=10):
    obj.Proxy = self
    obj.addProperty("App::PropertyString","PType","Ubolt","Type of pipeFeature").PType="Clamp"
    obj.addProperty("App::PropertyString","ClampType","Ubolt","Type of clamp").ClampType=ClampType
    obj.addProperty("App::PropertyString","PSize","Ubolt","Size of clamp").PSize=DN
    obj.addProperty("App::PropertyLength","C","Ubolt","Arc diameter").C=C
    obj.addProperty("App::PropertyLength","H","Ubolt","Overall height").H=H
    obj.addProperty("App::PropertyLength","d","Ubolt","Rod diameter").d=d
    obj.addProperty("App::PropertyString","thread","Ubolt","Size of thread").thread="M"+str(d)
  def onChanged(self, fp, prop):
    return None
  def execute(self, fp):
    fp.thread="M"+str(float(fp.d))
    c=Part.makeCircle(fp.C/2,FreeCAD.Vector(0,0,0),FreeCAD.Vector(0,0,1),0,180)
    l1=Part.makeLine((fp.C/2,0,0),(fp.C/2,fp.C/2-fp.H,0))
    l2=Part.makeLine((-fp.C/2,0,0),(-fp.C/2,fp.C/2-fp.H,0))
    p=Part.Face(Part.Wire(Part.makeCircle(fp.d/2,c.valueAt(c.FirstParameter),c.tangentAt(c.FirstParameter))))
    path=Part.Wire([c,l1,l2])
    fp.Shape=path.makePipe(p)

class Shell():
  '''
  Class for a lateral-shell-of-tank object
      *** prototype object ***
  Shell(obj[,L=800,W=400,H=500,thk=6])
    obj: the "App::FeaturePython" object
    L (float): the length
    W (float): the width
    H (float): the height
    thk (float): the plate's thickness
  '''
  def __init__(self,obj,L=800,W=400,H=500,thk=6):
    obj.Proxy=self
    obj.addProperty("App::PropertyLength","L","Tank","Tank's length").L=L
    obj.addProperty("App::PropertyLength","W","Tank","Tank's width").W=W
    obj.addProperty("App::PropertyLength","H","Tank","Tank's height").H=H
    obj.addProperty("App::PropertyLength","thk","Tank","Thikness of tank's shell").thk=thk
  def onChanged(self, fp, prop):
    return None
  def execute(self, fp):
    O=FreeCAD.Vector(0,0,0)
    vectL=FreeCAD.Vector(fp.L,0,0)
    vectW=FreeCAD.Vector(0,fp.W,0)
    vectH=FreeCAD.Vector(0,0,fp.H)
    base=[vectL,vectW,vectH]
    outline=[]
    for i in range(3):
      f1=Part.Face(Part.makePolygon([O,base[0],base[0]+base[1],base[1],O]))
      outline.append(f1)
      f2=f1.copy()
      f2.translate(base[2])
      outline.append(f2)
      base.append(base.pop(0))
    box=Part.Solid(Part.Shell(outline))
    tank=box.makeThickness([box.Faces[0],box.Faces[2]],-fp.thk,1.e-3)
    fp.Shape=tank
    
class PypeBranch(pypeType): # single-branch PypeLine
  '''Class for object PType="PypeBranch"
  Like PypeLine2 but attempting to make automatic update
  '''
  def __init__(self, obj,base,DN="DN50",PRating="SCH-STD",OD=60.3,thk=3,BR=None):
    print "*** Invoking .__init__() ***"
    # initialize the parent class
    super(PypeBranch,self).__init__(obj)
    # define common properties
    #self.Object=obj
    obj.PType="PypeBranch"
    obj.PSize=DN
    obj.PRating=PRating
    # define specific properties
    obj.addProperty("App::PropertyLink","Base","PypeBranch","The path.")
    if hasattr(base,"Shape") and base.Shape.Edges: 
      obj.Base=base
    else:
      FreeCAD.Console.PrintError('Base not valid\n')
    obj.addProperty("App::PropertyLinkList","Tubes","PypeBranch","The tubes of the branch.")
    obj.addProperty("App::PropertyLinkList","Curves","PypeBranch","The curves of the branch.")
    # draw elements
    self.redraw(obj,OD,thk,BR)
  def onChanged(self, fp, prop):
    print "*** Invoking .onChanged() ***"
  def execute(self, fp):
    print "*** Invoking .execute() ***"
    tubes=fp.Tubes
    curves=fp.Curves
    edges=fp.Base.Shape.Edges
    from math import degrees
    from DraftVecUtils import rounded
    from frameCmd import bisect, beamAx, extendTheBeam, ortho
    i=0
    L=0
    portA,portB=[FreeCAD.Vector()]*2
    while i<len(curves) and i<len(edges):
      v1,v2=[e.tangentAt(0) for e in edges[i:i+2]]
      P=frameCmd.intersectionCLines(*edges[i:i+2])
      pipeCmd.placeTheElbow(curves[i],v1,v2,P)
      #e1,e2=edges[i:i+2]
      #P=e2.valueAt(0)
      #curves[i].Placement.Base=P
      #d1,d2=[rounded(e.CenterOfMass-P) for e in [e1,e2]]
      #curves[i].BendAngle=180-degrees(d1.getAngle(d2))
      #Z=rounded(ortho(d1,d2))  #if not rounded makes the program loop
      #rot1=FreeCAD.Rotation(curves[i].Placement.Rotation.multVec(FreeCAD.Vector(0,0,1)),Z)
      #curves[i].Placement.Rotation=rot1.multiply(curves[i].Placement.Rotation)
      #edgesBisectb=bisect(d1,d2)
      #elbBisect=rounded(beamAx(curves[i],FreeCAD.Vector(1,1,0))) #if not rounded, fail in plane xz
      #rot2=FreeCAD.Rotation(elbBisect,edgesBisectb)
      #curves[i].Placement.Rotation=rot2.multiply(curves[i].Placement.Rotation)
      if not i:
        tubes[i].Placement.Base=edges[i].valueAt(0)
      else:
        tubes[i].Placement.Base=pipeCmd.portsPos(curves[i-1])[1]
      tubes[i].Placement.Rotation=FreeCAD.Rotation(FreeCAD.Vector(0,0,1),edges[i].tangentAt(0))
      #L=tubes[i].Placement.Base-pipeCmd.portsPos(curves[i])[0]
      L=min([(tubes[i].Placement.Base-port).Length for port in pipeCmd.portsPos(curves[i])])
      tubes[i].Height=L #.Length
      #if i: extendTheBeam(tubes[i],e1.valueAt(0)+e1.tangentAt(0)*L)
      #L=curves[i].Ports[0].Length
      #extendTheBeam(tubes[i],P-e1.tangentAt(0)*L)
      i+=1
    tubes[-1].Placement.Base=pipeCmd.portsPos(curves[-1])[1]
    tubes[-1].Placement.Rotation=FreeCAD.Rotation(FreeCAD.Vector(0,0,1),edges[-1].tangentAt(0))
    L=tubes[-1].Placement.Base-edges[i].valueAt(edges[i].LastParameter)
    tubes[-1].Height=L.Length
    #tubes[-1].Height=edges[-1].Length
    #extendTheBeam(tubes[-1],edges[-1].valueAt(0)+edges[-1].tangentAt(0)*L)
  def redraw(self,fp,OD=60.3,thk=3,BR=None):
    print "*** Invoking .redraw() ***"
    if not BR: BR=0.75*OD
    edges=fp.Base.Shape.Edges
    from pipeCmd import makePipe, makeElbowBetweenThings
    #---Create the tubes---
    tubes=list()
    for e in edges:
      t=makePipe([fp.PSize,OD,thk,e.Length],pos=e.valueAt(0),Z=e.tangentAt(0))
      t.PRating=fp.PRating
      t.PSize=fp.PSize
      tubes.append(t)
    fp.Tubes=tubes
    #---Create the curves---
    curves=list()
    for t in range(len(edges)-1):
      c=makeElbowBetweenThings(edges[t],edges[t+1],[fp.PSize,OD,thk,90,BR])
      c.PRating=fp.PRating
      c.PSize=fp.PSize
      curves.append(c)
    fp.Curves=curves
  def purge(self,fp):
    print "*** Invoking .purge() ***"
    from copy import copy
    delTubes=copy(fp.Tubes)
    delCurves=copy(fp.Curves)
    fp.Tubes=[]
    fp.Curves=[]
    for o in delTubes+delCurves: FreeCAD.ActiveDocument.removeObject(o.Name)
    
class ViewProviderPypeBranch:
  def __init__(self,vobj):
    vobj.Proxy = self
  def getIcon(self):
    from os.path import join, dirname, abspath
    return join(dirname(abspath(__file__)),"icons","branch.svg")
  def attach(self, vobj):
    self.ViewObject = vobj
    self.Object = vobj.Object
  def setEdit(self,vobj,mode):
    return False
  def unsetEdit(self,vobj,mode):
    return
  def __getstate__(self):
    return None
  def __setstate__(self,state):
    return None
  def claimChildren(self):
    return self.Object.Tubes + self.Object.Curves
  def onDelete(self, feature, subelements): # subelements is a tuple of strings
    #try:
      #for f in self.Object.Tubes+self.Object.Curves:
          #f.ViewObject.show()
    #except Exception as err:
      #App.Console.PrintError("Error in onDelete: " + err.message)
    return True

