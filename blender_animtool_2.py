bl_info = {
    "name": "Animation Tools Suite_Soumya",
    "author": "Animation Tools",
    "version": (1, 2, 1),
    "blender": (2, 80, 0),
    "location": "3D Viewport > Sidebar > Animation Tab",
    "description": "Animation toolset for F-Curves, Motion Paths, and Auto Tween",
    "category": "Animation",
}

import bpy
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import FloatProperty, PointerProperty
from mathutils import Vector, Quaternion


# =============================================================================
# F-CURVE TOOLS
# =============================================================================

class GRAPH_OT_set_linear(Operator):
    bl_idname = "graph.set_linear"
    bl_label = "Linear"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        fcurves_found = []
        for obj in context.selected_objects:
            if obj.animation_data and obj.animation_data.action:
                fcurves_found.extend(obj.animation_data.action.fcurves)

        if not fcurves_found:
            self.report({'WARNING'}, "No F-curves found")
            return {'CANCELLED'}

        for fcurve in fcurves_found:
            while fcurve.modifiers:
                fcurve.modifiers.remove(fcurve.modifiers[0])
            fcurve.extrapolation = 'LINEAR'

        return {'FINISHED'}


class GRAPH_OT_set_constant(Operator):
    bl_idname = "graph.set_constant"
    bl_label = "Constant"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        fcurves_found = []
        for obj in context.selected_objects:
            if obj.animation_data and obj.animation_data.action:
                fcurves_found.extend(obj.animation_data.action.fcurves)

        if not fcurves_found:
            self.report({'WARNING'}, "No F-curves found")
            return {'CANCELLED'}

        for fcurve in fcurves_found:
            while fcurve.modifiers:
                fcurve.modifiers.remove(fcurve.modifiers[0])
            fcurve.extrapolation = 'CONSTANT'

        return {'FINISHED'}


class GRAPH_OT_set_cycle(Operator):
    bl_idname = "graph.set_cycle"
    bl_label = "Cycle"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        fcurves_found = []
        for obj in context.selected_objects:
            if obj.animation_data and obj.animation_data.action:
                fcurves_found.extend(obj.animation_data.action.fcurves)

        if not fcurves_found:
            self.report({'WARNING'}, "No F-curves found")
            return {'CANCELLED'}

        for fcurve in fcurves_found:
            while fcurve.modifiers:
                fcurve.modifiers.remove(fcurve.modifiers[0])
            mod = fcurve.modifiers.new(type='CYCLES')
            mod.mode_before = 'REPEAT'
            mod.mode_after = 'REPEAT'

        return {'FINISHED'}


class GRAPH_OT_set_cycle_offset(Operator):
    bl_idname = "graph.set_cycle_offset"
    bl_label = "Cycle Offset"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        fcurves_found = []
        for obj in context.selected_objects:
            if obj.animation_data and obj.animation_data.action:
                fcurves_found.extend(obj.animation_data.action.fcurves)

        if not fcurves_found:
            self.report({'WARNING'}, "No F-curves found")
            return {'CANCELLED'}

        for fcurve in fcurves_found:
            while fcurve.modifiers:
                fcurve.modifiers.remove(fcurve.modifiers[0])
            mod = fcurve.modifiers.new(type='CYCLES')
            mod.mode_before = 'REPEAT_OFFSET'
            mod.mode_after = 'REPEAT_OFFSET'

        return {'FINISHED'}


# =============================================================================
# MOTION PATHS
# =============================================================================

class MOTIONPATH_OT_calculate(Operator):
    bl_idname = "motionpath.calculate"
    bl_label = "Motion Paths"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode == 'POSE':
            try:
                bpy.ops.pose.paths_calculate()
            except:
                return {'CANCELLED'}
        else:
            for obj in context.selected_objects:
                context.view_layer.objects.active = obj
                try:
                    bpy.ops.object.paths_calculate()
                except:
                    pass

        return {'FINISHED'}


class MOTIONPATH_OT_clear(Operator):
    bl_idname = "motionpath.clear"
    bl_label = "Clear"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode == 'POSE':
            try:
                bpy.ops.pose.paths_clear()
            except:
                pass
        else:
            for obj in context.selected_objects:
                context.view_layer.objects.active = obj
                try:
                    bpy.ops.object.paths_clear()
                except:
                    pass

        return {'FINISHED'}


# =============================================================================
# AUTO TWEEN
# =============================================================================

def get_keyframes_around_current(obj, current_frame):
    if not obj.animation_data or not obj.animation_data.action:
        return None, None

    keyframes = []
    for fc in obj.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            frame = int(kp.co[0])
            if frame not in keyframes:
                keyframes.append(frame)

    keyframes.sort()

    prev_frame = None
    next_frame = None

    for frame in keyframes:
        if frame < current_frame:
            prev_frame = frame
        elif frame > current_frame:
            next_frame = frame
            break

    return prev_frame, next_frame


def interpolate_object_transforms(obj, prev_frame, next_frame, current_frame, blend_factor):
    scene = bpy.context.scene

    scene.frame_set(prev_frame)
    prev_loc = obj.location.copy()
    prev_rot = obj.rotation_euler.copy() if obj.rotation_mode == 'XYZ' else obj.rotation_quaternion.copy()
    prev_scale = obj.scale.copy()

    scene.frame_set(next_frame)
    next_loc = obj.location.copy()
    next_rot = obj.rotation_euler.copy() if obj.rotation_mode == 'XYZ' else obj.rotation_quaternion.copy()
    next_scale = obj.scale.copy()

    scene.frame_set(current_frame)

    obj.location = prev_loc.lerp(next_loc, blend_factor)

    if obj.rotation_mode == 'XYZ':
        obj.rotation_euler = Vector((
            prev_rot[0] + (next_rot[0] - prev_rot[0]) * blend_factor,
            prev_rot[1] + (next_rot[1] - prev_rot[1]) * blend_factor,
            prev_rot[2] + (next_rot[2] - prev_rot[2]) * blend_factor
        ))
    else:
        obj.rotation_quaternion = Quaternion(prev_rot).slerp(Quaternion(next_rot), blend_factor)

    obj.scale = prev_scale.lerp(next_scale, blend_factor)

    obj.keyframe_insert(data_path="location")
    obj.keyframe_insert(data_path="rotation_euler" if obj.rotation_mode == 'XYZ' else "rotation_quaternion")
    obj.keyframe_insert(data_path="scale")


def apply_tween(blend_factor):
    context = bpy.context
    current_frame = context.scene.frame_current

    for obj in context.selected_objects:
        prev, next = get_keyframes_around_current(obj, current_frame)
        if prev and next:
            interpolate_object_transforms(obj, prev, next, current_frame, blend_factor)


class TweenSettings(PropertyGroup):

    def update_tween_left(self, context):
        apply_tween(self.tween_left_factor)

    def update_tween_right(self, context):
        apply_tween(self.tween_right_factor)

    def update_overshoot_left(self, context):
        apply_tween(-self.overshoot_left_factor)

    def update_overshoot_right(self, context):
        apply_tween(1.0 + self.overshoot_right_factor)

    tween_left_factor: FloatProperty(
        default=0.25, min=0.0, max=1.0, subtype='FACTOR', update=update_tween_left)

    tween_right_factor: FloatProperty(
        default=0.75, min=0.0, max=1.0, subtype='FACTOR', update=update_tween_right)

    overshoot_left_factor: FloatProperty(
        default=0.1, min=0.0, max=1.0, subtype='FACTOR', update=update_overshoot_left)

    overshoot_right_factor: FloatProperty(
        default=0.1, min=0.0, max=1.0, subtype='FACTOR', update=update_overshoot_right)


# =============================================================================
# UI PANELS
# =============================================================================

class ANIMATION_PT_tools_suite(Panel):
    bl_label = "Animation Tools Suite"
    bl_idname = "ANIMATION_PT_tools_suite"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Animation'

    def draw(self, context):
        pass


class ANIMATION_PT_fcurve_tools(Panel):
    bl_label = "F-Curve Tools"
    bl_parent_id = "ANIMATION_PT_tools_suite"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Animation'

    def draw(self, context):
        row = self.layout.row(align=True)
        row.operator("graph.set_cycle", text="Cycle")
        row.operator("graph.set_cycle_offset", text="Cycle+")
        row.operator("graph.set_linear", text="Linear")
        row.operator("graph.set_constant", text="Const")


class ANIMATION_PT_motion_paths(Panel):
    bl_label = "Motion Paths"
    bl_parent_id = "ANIMATION_PT_tools_suite"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Animation'

    def draw(self, context):
        row = self.layout.row(align=True)
        row.operator("motionpath.calculate", text="Calc")
        row.operator("motionpath.clear", text="Clear")


class ANIMATION_PT_auto_tween(Panel):
    bl_label = "Auto Tween Machine"
    bl_parent_id = "ANIMATION_PT_tools_suite"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Animation'

    def draw(self, context):
        ts = context.scene.tween_settings
        row = self.layout.row(align=True)
        row.prop(ts, "tween_left_factor", slider=True)
        row.prop(ts, "tween_right_factor", slider=True)

        row = self.layout.row(align=True)
        row.prop(ts, "overshoot_left_factor", slider=True)
        row.prop(ts, "overshoot_right_factor", slider=True)


# =============================================================================
# REGISTRATION
# =============================================================================

classes = (
    GRAPH_OT_set_linear,
    GRAPH_OT_set_constant,
    GRAPH_OT_set_cycle,
    GRAPH_OT_set_cycle_offset,
    MOTIONPATH_OT_calculate,
    MOTIONPATH_OT_clear,
    TweenSettings,
    ANIMATION_PT_tools_suite,
    ANIMATION_PT_fcurve_tools,
    ANIMATION_PT_motion_paths,
    ANIMATION_PT_auto_tween,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.tween_settings = PointerProperty(type=TweenSettings)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.tween_settings


if __name__ == "__main__":
    register()