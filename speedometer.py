import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds

def maya_useNewAPI():
    pass
    
class speedometer(om.MPxNode):
    
    # Node Data
    TYPE_NAME = "speedometer"
    TYPE_ID = om.MTypeId(0x0007F7F8)
    
    # Main Attrs
    time_input = None
    input_obj = None
    input_mtx = None
    speed = None
    speed_unit = None
    method = None
    distance = None
    framerate = None
    working_units = None
    activated = None
    
    # Separator Attrs (ChannelBox Only)
    separator_00 = None
    separator_01 = None
    separator_02 = None
    
    speed_units = {
        0:["km/h", 3.6],
        1:["mph", 2.23694],
        2:["m/s", 1.0],
        3:["f/s", 3.28084],
        }

    
    def __init__(self):
        super(speedometer, self).__init__()
       
    def compute(self, plug, data):

        if not plug == speedometer.speed:
            data.setClean(plug)
            return

        if plug == speedometer.speed:
            
            """
            The formula to calculate the speed in m/s is speed = distance / time.
            In our case, the base we want to calcualte is is meters per second.
            Therefore, we need to know how much distance (m) our object traveles
            in 1 second (fps).
            
            Depending on the unit the user chooses, the speed in m/s is converted
            with the according "speed unit" factor.
            
            The user can choose a method/input that should be used. The node can 
            either calculate the speed from an input matrix or input double (distance).
            
            The distance can be used for motion path setups where we are working 
            with distance values instead of u value. This will give us a more stable
            result than working with the worldMatrix of an object.
            
            """
            
            # Check if node is activated
            if not data.inputValue(speedometer.activated).asBool():
                product_data_handle = data.outputValue(speedometer.speed)
                product_data_handle.setDouble(0.0)
                return
                
            # Define this node
            this_node = self.thisMObject()
                
            # Check if plugs are connected
            method = data.inputValue(speedometer.method).asInt()
            
            if method == 0:
                matrix_plug = om.MPlug(this_node, self.input_mtx)
                source = matrix_plug.source().name()
                
            elif method == 1:
                distance_plug = om.MPlug(this_node, self.distance)
                source = distance_plug.source().name()
                
            if not source:
                product_data_handle = data.outputValue(speedometer.speed)
                product_data_handle.setDouble(0.0)
                return

            # Read Constants
            framerate = data.inputValue(speedometer.framerate).asDouble()
            working_units = data.inputValue(speedometer.working_units).asDouble()

            # Define the speed unit
            unit_index = data.inputValue(speedometer.speed_unit).asInt()
            
            # Query current time value
            current_frame = oma.MAnimControl.currentTime().asUnits(om.MTime.uiUnit())
            
            # Query if distance or matrix is used
            method = data.inputValue(speedometer.method).asInt()

            # Define the past dg context
            current_context = om.MDGContext(om.MTime(current_frame))
            past_context = om.MDGContext(om.MTime(current_frame-1))

            if method == 1:
                # Get the current and past distance
                distance_plug = om.MPlug(this_node, self.distance)
                current_distance = distance_plug.asMDataHandle(current_context).asDouble()
                past_distance = distance_plug.asMDataHandle(past_context).asDouble()

                distance = current_distance - past_distance
                
                if distance < 0:
                    distance = distance * -1
                
            else:
                # Get the current matrix
                current_matrix = matrix_plug.asMDataHandle(current_context).asFloatMatrix()
                current_translations = list(current_matrix)[-4:-1]
                current_vector = om.MVector(current_translations[0], current_translations[1], current_translations[2])

                # Get the past matrix
                past_matrix = matrix_plug.asMDataHandle(past_context).asFloatMatrix()
                past_translations = list(past_matrix)[-4:-1]
                past_vector = om.MVector(past_translations[0], past_translations[1], past_translations[2])

                # Calculate the new vector
                new_vector = past_vector - current_vector
                
                # Calculate the length/distance
                distance = om.MVector.length(new_vector)

            # Calculate the speed
            product = distance / working_units * framerate * self.speed_units[unit_index][1]

            # Set the value on the output speed attr
            product_data_handle = data.outputValue(speedometer.speed)
            product_data_handle.setDouble(product)
            
            # Set the plug as clean
            data.setClean(plug)      

            
    def postConstructor(self):
        
        # Define this node
        this_node = self.thisMObject()
        
        """ Query some constants and set them on the node """
        
        # Framerate
        framerate = om.MTime(1, om.MTime.kSeconds).asUnits(om.MTime.uiUnit())
        fps_plug = om.MPlug(this_node, self.framerate)
        fps_plug.setFloat(framerate)
        
        # Maya Working Units | How much is one meter in working units
        distance = om.MDistance(1, om.MDistance.kMeters)
        units = distance.asUnits(om.MDistance.uiUnit())
        units_plug = om.MPlug(this_node, self.working_units)
        units_plug.setFloat(units)

        """ Connect the the scenes time node to the time input of the speedometer """
        
        # Define time input plug
        time_input = om.MPlug(this_node, self.time_input)
        
        # Get Mayas Time Node
        dg_modifier = om.MDGModifier()
        mIT_object = om.MItDependencyNodes(om.MFn.kTime)
        
        # Connect Mayas time1 node to the time input
        if not mIT_object.isDone():
            time_object = mIT_object.thisNode()
            depend_node = om.MFnDependencyNode(time_object)
            
            if depend_node.name() == "time1":
                output_plug = depend_node.findPlug("outTime", False)
                dg_modifier.connect(output_plug, time_input)
                dg_modifier.doIt()
                
        """ Lock Attributes that the user should not touch. """
        separator_plug_00 = om.MPlug(this_node, self.separator_00)
        separator_plug_00.isLocked = True
        
        separator_plug_01 = om.MPlug(this_node, self.separator_01)
        separator_plug_01.isLocked = True
        
        separator_plug_02 = om.MPlug(this_node, self.separator_02)
        separator_plug_02.isLocked = True
        
        speed_plug = om.MPlug(this_node, self.speed)
        speed_plug.isLocked = True


    @classmethod
    def creator(cls):
        
        """ Returns an instance of the class """
        
        return speedometer()
   
    @classmethod
    def initialize(cls):
        
        """ Creating and Adding attrbiutes """
        # 0) Matrix Attributes
        matrix_attr = om.MFnMatrixAttribute()
        cls.input_mtx = matrix_attr.create("input_matrix", "matrixIn1", om.MFnMatrixArrayData.kFloatArray)
        matrix_attr.keyable = True
        
        # 1) Message Attributes
        message_attr = om.MFnMessageAttribute()
        
        cls.input_obj = message_attr.create("input_object", "obj")
        message_attr.keyable = True
        message_attr.readable = False
        
        # 2) Numeric Attributes
        numeric_attr = om.MFnNumericAttribute()
        cls.speed = numeric_attr.create("speed", "speed", om.MFnNumericData.kDouble, 1.0)
        numeric_attr.channelBox = True
        
        cls.distance = numeric_attr.create("distance", "distance", om.MFnNumericData.kDouble, 0.0)
        numeric_attr.keyable = True
        
        cls.framerate = numeric_attr.create("framerate", "fps", om.MFnNumericData.kDouble, 1.0)
        numeric_attr.channelBox = True
        
        cls.working_units = numeric_attr.create("working_units", "units", om.MFnNumericData.kDouble, 1.0)
        numeric_attr.channelBox = True
        
        cls.activated = numeric_attr.create("activated", "active", om.MFnNumericData.kBoolean, True)
        numeric_attr.keyable = True
        numeric_attr.channelBox = True
        
        # 3) Enum Attributes
        enum_attr = om.MFnEnumAttribute()
        
        cls.method = enum_attr.create("method", "method", 0)
        enum_attr.addField("Matrix", 0)
        enum_attr.addField("Distance", 1)
        enum_attr.channelBox = True
        
        cls.speed_unit = enum_attr.create("unit", "unit", 0)
        enum_attr.channelBox = True
        
        enum_attr.addField("km/h", 0)
        enum_attr.addField("mph", 1)
        enum_attr.addField("m/s", 2)
        enum_attr.addField("f/s", 3)
        
        # Separator attributes
        cls.separator_00 = enum_attr.create("evaluation", "evaluation", 0)
        enum_attr.setNiceNameOverride(" ")
        enum_attr.addField(" ", 0)
        enum_attr.channelBox = True
        
        
        cls.separator_01 = enum_attr.create("parameters", "parameters", 0)
        enum_attr.setNiceNameOverride(" ")
        enum_attr.channelBox = True
        enum_attr.addField(" ", 0)
        
        cls.separator_02 = enum_attr.create("output", "output", 0)
        enum_attr.setNiceNameOverride(" ")
        enum_attr.channelBox = True
        enum_attr.addField(" ", 0)
        
        # 4) Unit Attributes
        unit_attr = om.MFnUnitAttribute()
        cls.time_input = unit_attr.create("time_input", "time", unit_attr.kTime, 0.0)
        unit_attr.keyable = True
        
        """ Add attributes """
        cls.addAttribute(cls.activated)
        cls.addAttribute(cls.method)
       
        cls.addAttribute(cls.separator_00)
        cls.addAttribute(cls.time_input)
        cls.addAttribute(cls.framerate)
        cls.addAttribute(cls.working_units)
        cls.addAttribute(cls.distance)
        cls.addAttribute(cls.input_mtx)
        cls.addAttribute(cls.input_obj)
        
        cls.addAttribute(cls.separator_01)
        cls.addAttribute(cls.speed)
        cls.addAttribute(cls.speed_unit)

        """ Create attribute relation """
        cls.attributeAffects(cls.activated, cls.speed)
        cls.attributeAffects(cls.time_input, cls.speed)
        cls.attributeAffects(cls.input_mtx, cls.speed)
        cls.attributeAffects(cls.speed_unit, cls.speed)
        cls.attributeAffects(cls.distance, cls.speed)
        cls.attributeAffects(cls.method, cls.speed)
        cls.attributeAffects(cls.framerate, cls.speed)
        cls.attributeAffects(cls.working_units, cls.speed)
        

        

def initializePlugin(plugin):
    
    plugin_name = "speedometer"
    vendor = "Jacob Doehner"
    version = "1.0.0"
    
    plugin_fn = om.MFnPlugin(plugin, vendor, version)
    
    try:
        plugin_fn.registerNode(speedometer.TYPE_NAME,
                               speedometer.TYPE_ID,
                               speedometer.creator,
                               speedometer.initialize,
                               om.MPxNode.kDependNode
                               )
    except:
        om.MGlobal.displayError(f"Failed to register node: {speedometer.TYPE_NAME}")
    
def uninitializePlugin(plugin):
    
    plugin_fn = om.MFnPlugin(plugin)
    
    try:
        plugin_fn.deregisterNode(speedometer.TYPE_ID)
    except:
        om.MGlobal.displayError(f"Failed to deregister node: {speedometer.TYPE_NAME}")
 
    
if __name__ == "__main__":
    
    # Define plugin name
    plugin_name = "speedometer.py"
    
    # Force a new, clean scene
    cmds.file("X:/redgun2_rg2-13437/000-rnd/0000/3d/anim/rg2_000-rnd_0000_anim_v079_cob.ma", open=True, f=True)
    
    # Reload the plugin
    cmds.evalDeferred(f"if cmds.pluginInfo('{plugin_name}', q=True, loaded=True): cmds.unloadPlugin('{plugin_name}')")
    cmds.evalDeferred(f"if not cmds.pluginInfo('{plugin_name}', q=True, loaded=True): cmds.loadPlugin('{plugin_name}')")
    
    # Create a new divideDoubleLinear Node
    output = cmds.evalDeferred('cmds.createNode("speedometer")')
    cmds.evalDeferred('cmds.select("speedometer1")')
    #cmds.evalDeferred('cmds.select(clear=True)')
    
    
