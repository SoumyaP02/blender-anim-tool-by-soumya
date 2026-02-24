import bpy
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import FloatProperty
from mathutils import Vector, Quaternion

# Addon information
bl_info = {
    "name": "Auto Tween Machine",
    "author": "soumya",
    "version": (1, 0),
    "blender": (4, 0, 0),
    "location": "3D Viewport > Sidebar > Animation Tab",
    "description": "Auto-applying tween machine with sliders",
    "category": "Animation",
}

def get_keyframes_around_current(obj, current_frame):
    """Find the previous and next keyframes around current frame"""
    prev_frame = None
    next_frame = None
    
    if not obj.animation_data or not obj.animation_data.action:
        return None, None
    
    # Get all keyframe points
    keyframes = []
    for fcurve in obj.animation_data.action.fcurves:
        for keyframe in fcurve.keyframe_points:
            frame = int(keyframe.co[0])
            if frame not in keyframes:
                keyframes.append(frame)
    
    keyframes.sort()
    
    # Find prev and next keyframes
    for frame in keyframes:
        if frame < current_frame:
            prev_frame = frame
        elif frame > current_frame:
            next_frame = frame
            break
    
    return prev_frame, next_frame

def interpolate_object_transforms(obj, prev_frame, next_frame, current_frame, blend_factor):
    """Interpolate object transforms between two keyframes"""
    scene = bpy.context.scene
    
    # Store current frame
    original_frame = scene.frame_current
    
    # Get transform at previous keyframe
    scene.frame_set(prev_frame)
    prev_loc = obj.location.copy()
    prev_rot = obj.rotation_euler.copy() if obj.rotation_mode == 'XYZ' else obj.rotation_quaternion.copy()
    prev_scale = obj.scale.copy()
    
    # Get transform at next keyframe
    scene.frame_set(next_frame)
    next_loc = obj.location.copy()
    next_rot = obj.rotation_euler.copy() if obj.rotation_mode == 'XYZ' else obj.rotation_quaternion.copy()
    next_scale = obj.scale.copy()
    
    # Go back to current frame
    scene.frame_set(current_frame)
    
    # Interpolate location
    new_loc = prev_loc.lerp(next_loc, blend_factor)
    obj.location = new_loc
    
    # Interpolate rotation
    if obj.rotation_mode == 'XYZ':
        # Euler rotation
        new_rot = Vector((
            prev_rot[0] + (next_rot[0] - prev_rot[0]) * blend_factor,
            prev_rot[1] + (next_rot[1] - prev_rot[1]) * blend_factor,
            prev_rot[2] + (next_rot[2] - prev_rot[2]) * blend_factor
        ))
        obj.rotation_euler = new_rot
    else:
        # Quaternion rotation
        prev_quat = Quaternion(prev_rot)
        next_quat = Quaternion(next_rot)
        new_rot = prev_quat.slerp(next_quat, blend_factor)
        obj.rotation_quaternion = new_rot
    
    # Interpolate scale
    new_scale = prev_scale.lerp(next_scale, blend_factor)
    obj.scale = new_scale
    
    # Insert keyframes
    obj.keyframe_insert(data_path="location")
    obj.keyframe_insert(data_path="rotation_euler" if obj.rotation_mode == 'XYZ' else "rotation_quaternion")
    obj.keyframe_insert(data_path="scale")

def interpolate_bone_transforms(bone, armature, prev_frame, next_frame, current_frame, blend_factor):
    """Interpolate bone transforms between two keyframes"""
    scene = bpy.context.scene
    
    # Store current frame
    original_frame = scene.frame_current
    
    # Get pose at previous keyframe
    scene.frame_set(prev_frame)
    prev_loc = bone.location.copy()
    prev_rot = bone.rotation_euler.copy() if bone.rotation_mode == 'XYZ' else bone.rotation_quaternion.copy()
    prev_scale = bone.scale.copy()
    
    # Get pose at next keyframe
    scene.frame_set(next_frame)
    next_loc = bone.location.copy()
    next_rot = bone.rotation_euler.copy() if bone.rotation_mode == 'XYZ' else bone.rotation_quaternion.copy()
    next_scale = bone.scale.copy()
    
    # Go back to current frame
    scene.frame_set(current_frame)
    
    # Interpolate transforms
    bone.location = prev_loc.lerp(next_loc, blend_factor)
    
    if bone.rotation_mode == 'XYZ':
        new_rot = Vector((
            prev_rot[0] + (next_rot[0] - prev_rot[0]) * blend_factor,
            prev_rot[1] + (next_rot[1] - prev_rot[1]) * blend_factor,
            prev_rot[2] + (next_rot[2] - prev_rot[2]) * blend_factor
        ))
        bone.rotation_euler = new_rot
    else:
        prev_quat = Quaternion(prev_rot)
        next_quat = Quaternion(next_rot)
        bone.rotation_quaternion = prev_quat.slerp(next_quat, blend_factor)
    
    bone.scale = prev_scale.lerp(next_scale, blend_factor)
    
    # Insert keyframes
    bone.keyframe_insert(data_path="location")
    bone.keyframe_insert(data_path="rotation_euler" if bone.rotation_mode == 'XYZ' else "rotation_quaternion")
    bone.keyframe_insert(data_path="scale")

def apply_tween(blend_factor):
    """Apply tween with given blend factor"""
    context = bpy.context
    scene = context.scene
    current_frame = scene.frame_current
    
    tweened_count = 0
    
    # Check if we're in pose mode
    if context.mode == 'POSE' and context.selected_pose_bones:
        # POSE MODE - Tween selected bones
        armature = context.active_object
        selected_bones = context.selected_pose_bones
        
        for bone in selected_bones:
            prev_frame, next_frame = get_keyframes_around_current(armature, current_frame)
            
            if prev_frame is not None and next_frame is not None:
                interpolate_bone_transforms(bone, armature, prev_frame, next_frame, current_frame, blend_factor)
                tweened_count += 1
    
    else:
        # OBJECT MODE - Tween selected objects
        selected_objects = context.selected_objects
        
        if selected_objects:
            for obj in selected_objects:
                prev_frame, next_frame = get_keyframes_around_current(obj, current_frame)
                
                if prev_frame is not None and next_frame is not None:
                    interpolate_object_transforms(obj, prev_frame, next_frame, current_frame, blend_factor)
                    tweened_count += 1
    
    return tweened_count

# Properties for tween settings with auto-update
class TweenSettings(PropertyGroup):
    def update_tween_left(self, context):
        """Auto-apply tween towards previous keyframe"""
        apply_tween(self.tween_left_factor)
    
    def update_tween_right(self, context):
        """Auto-apply tween towards next keyframe"""
        apply_tween(self.tween_right_factor)
    
    def update_overshoot_left(self, context):
        """Auto-apply overshoot towards previous keyframe"""
        apply_tween(-self.overshoot_left_factor)
    
    def update_overshoot_right(self, context):
        """Auto-apply overshoot towards next keyframe"""
        apply_tween(1.0 + self.overshoot_right_factor)
    
    tween_left_factor: FloatProperty(
        name="Tween Left",
        description="Tween towards previous keyframe",
        default=0.25,
        min=0.0,
        max=1.0,
        precision=2,
        subtype='FACTOR',
        update=update_tween_left
    )
    
    tween_right_factor: FloatProperty(
        name="Tween Right",
        description="Tween towards next keyframe",
        default=0.75,
        min=0.0,
        max=1.0,
        precision=2,
        subtype='FACTOR',
        update=update_tween_right
    )
    
    overshoot_left_factor: FloatProperty(
        name="Overshoot Left",
        description="Overshoot beyond previous keyframe",
        default=0.1,
        min=0.0,
        max=1.0,
        precision=2,
        subtype='FACTOR',
        update=update_overshoot_left
    )
    
    overshoot_right_factor: FloatProperty(
        name="Overshoot Right", 
        description="Overshoot beyond next keyframe",
        default=0.1,
        min=0.0,
        max=1.0,
        precision=2,
        subtype='FACTOR',
        update=update_overshoot_right
    )

# UI Panel
class TWEEN_PT_panel(Panel):
    bl_label = "Auto Tween Machine"
    bl_idname = "TWEEN_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Animation'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        tween_settings = scene.tween_settings
        
        # Tween sliders in one row
        layout.label(text="Tween:")
        row = layout.row()
        row.prop(tween_settings, "tween_left_factor", slider=True)
        row.prop(tween_settings, "tween_right_factor", slider=True)
        
        # Overshoot sliders in one row
        layout.label(text="Overshoot:")
        row = layout.row()
        row.prop(tween_settings, "overshoot_left_factor", slider=True)
        row.prop(tween_settings, "overshoot_right_factor", slider=True)

# Registration
classes = [
    TweenSettings,
    TWEEN_PT_panel,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Add properties to scene
    bpy.types.Scene.tween_settings = bpy.props.PointerProperty(type=TweenSettings)
    
    print("Auto Tween Machine addon registered")

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    # Remove properties from scene
    del bpy.types.Scene.tween_settings
    
    print("Auto Tween Machine addon unregistered")

if __name__ == "__main__":
    register()
