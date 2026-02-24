"""
Animation Library for Blender
Works with all Blender versions (2.8+)
Allows viewing and applying actions to selected armature/rig characters
"""

bl_info = {
    "name": "Animation Library_soumya",
    "author": "soumya",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Animation Tab",
    "description": "Browse and apply actions to objects with advanced management features",
    "category": "Animation",
}

import bpy
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import StringProperty, IntProperty, BoolProperty


# ==================== OPERATORS ====================

class ANIMLIB_OT_apply_action(Operator):
    """Apply selected action to active object"""
    bl_idname = "animlib.apply_action"
    bl_label = "Apply Action"
    bl_options = {'REGISTER', 'UNDO'}
    
    action_name: StringProperty(name="Action Name")
    
    def execute(self, context):
        obj = context.active_object
        
        # Check if object is valid
        if not obj:
            self.report({'ERROR'}, "No active object selected")
            return {'CANCELLED'}
        
        # Get the action
        action = bpy.data.actions.get(self.action_name)
        if not action:
            self.report({'ERROR'}, f"Action '{self.action_name}' not found")
            return {'CANCELLED'}
        
        # Create animation data if it doesn't exist
        if not obj.animation_data:
            obj.animation_data_create()
        
        # Apply the action
        obj.animation_data.action = action
        
        self.report({'INFO'}, f"Applied action: {self.action_name}")
        return {'FINISHED'}


class ANIMLIB_OT_remove_action(Operator):
    """Remove action from active object"""
    bl_idname = "animlib.remove_action"
    bl_label = "Clear Action"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        
        if not obj:
            self.report({'ERROR'}, "No object selected")
            return {'CANCELLED'}
        
        if obj.animation_data and obj.animation_data.action:
            obj.animation_data.action = None
            self.report({'INFO'}, "Action cleared")
        else:
            self.report({'INFO'}, "No action to clear")
        
        return {'FINISHED'}


class ANIMLIB_OT_toggle_fake_user(Operator):
    """Toggle fake user for action (protects from deletion)"""
    bl_idname = "animlib.toggle_fake_user"
    bl_label = "Toggle Fake User"
    bl_options = {'REGISTER', 'UNDO'}
    
    action_name: StringProperty(name="Action Name")
    
    def execute(self, context):
        action = bpy.data.actions.get(self.action_name)
        if not action:
            self.report({'ERROR'}, f"Action '{self.action_name}' not found")
            return {'CANCELLED'}
        
        action.use_fake_user = not action.use_fake_user
        
        if action.use_fake_user:
            self.report({'INFO'}, f"Fake user enabled for '{self.action_name}'")
        else:
            self.report({'INFO'}, f"Fake user disabled for '{self.action_name}'")
        
        return {'FINISHED'}


class ANIMLIB_OT_new_action(Operator):
    """Create a new action"""
    bl_idname = "animlib.new_action"
    bl_label = "New Action"
    bl_options = {'REGISTER', 'UNDO'}
    
    action_name: StringProperty(
        name="Action Name",
        default="Action"
    )
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "action_name")
    
    def execute(self, context):
        obj = context.active_object
        
        if not obj:
            self.report({'ERROR'}, "No object selected")
            return {'CANCELLED'}
        
        # Create new action
        new_action = bpy.data.actions.new(name=self.action_name)
        
        # Create animation data if it doesn't exist
        if not obj.animation_data:
            obj.animation_data_create()
        
        # Assign the new action
        obj.animation_data.action = new_action
        
        self.report({'INFO'}, f"Created new action: {self.action_name}")
        return {'FINISHED'}


class ANIMLIB_OT_duplicate_action(Operator):
    """Duplicate an action"""
    bl_idname = "animlib.duplicate_action"
    bl_label = "Duplicate Action"
    bl_options = {'REGISTER', 'UNDO'}
    
    action_name: StringProperty(name="Action Name")
    
    def execute(self, context):
        action = bpy.data.actions.get(self.action_name)
        if not action:
            self.report({'ERROR'}, f"Action '{self.action_name}' not found")
            return {'CANCELLED'}
        
        # Duplicate the action
        new_action = action.copy()
        new_action.name = f"{action.name}_copy"
        
        # Apply to active object if available
        obj = context.active_object
        if obj:
            if not obj.animation_data:
                obj.animation_data_create()
            obj.animation_data.action = new_action
        
        self.report({'INFO'}, f"Duplicated action: {new_action.name}")
        return {'FINISHED'}


class ANIMLIB_OT_delete_action(Operator):
    """Delete an action"""
    bl_idname = "animlib.delete_action"
    bl_label = "Delete Action"
    bl_options = {'REGISTER', 'UNDO'}
    
    action_name: StringProperty(name="Action Name")
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
    
    def execute(self, context):
        action = bpy.data.actions.get(self.action_name)
        if not action:
            self.report({'ERROR'}, f"Action '{self.action_name}' not found")
            return {'CANCELLED'}
        
        # Remove the action
        bpy.data.actions.remove(action)
        
        self.report({'INFO'}, f"Deleted action: {self.action_name}")
        return {'FINISHED'}


class ANIMLIB_OT_refresh_list(Operator):
    """Refresh the action list"""
    bl_idname = "animlib.refresh_list"
    bl_label = "Refresh"
    bl_description = "Refresh the action list"
    
    def execute(self, context):
        self.report({'INFO'}, "Action list refreshed")
        return {'FINISHED'}


class ANIMLIB_OT_filter_actions(Operator):
    """Filter actions by search term"""
    bl_idname = "animlib.filter_actions"
    bl_label = "Filter"
    
    def execute(self, context):
        return {'FINISHED'}


# ==================== UI PANEL ====================

class ANIMLIB_PT_main_panel(Panel):
    """Main Animation Library Panel"""
    bl_label = "Animation Library"
    bl_idname = "ANIMLIB_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Animation'
    
    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        scene = context.scene
        
        # ===== ACTIVE OBJECT INFO =====
        row = layout.row()
        row.label(text="Active:", icon='OBJECT_DATA')
        
        if obj:
            # Get appropriate icon based on object type
            icon_map = {
                'ARMATURE': 'ARMATURE_DATA',
                'MESH': 'MESH_DATA',
                'CURVE': 'CURVE_DATA',
                'CAMERA': 'CAMERA_DATA',
                'LIGHT': 'LIGHT_DATA',
                'EMPTY': 'EMPTY_DATA',
            }
            obj_icon = icon_map.get(obj.type, 'OBJECT_DATA')
            row.label(text=f"{obj.name}", icon=obj_icon)
            
            # Current action on same line if available
            if obj.animation_data and obj.animation_data.action:
                row = layout.row()
                row.label(text=f"Using: {obj.animation_data.action.name}", icon='ACTION')
                row.operator("animlib.remove_action", text="", icon='X')
        else:
            row.label(text="None selected", icon='ERROR')
        
        layout.separator()
        
        # ===== SEARCH AND NEW ACTION =====
        row = layout.row(align=True)
        row.prop(scene, "animlib_search", text="", icon='VIEWZOOM', placeholder="Search...")
        row.operator("animlib.refresh_list", text="", icon='FILE_REFRESH')
        row.operator("animlib.new_action", text="", icon='ADD')
        
        # ===== ACTION LIST =====
        row = layout.row()
        row.label(text=f"Actions ({len(bpy.data.actions)}):", icon='ACTION')
        
        # Get all actions
        actions = bpy.data.actions
        search_term = scene.animlib_search.lower()
        
        # Filter actions by search term
        filtered_actions = [
            action for action in actions
            if search_term in action.name.lower()
        ]
        
        if len(filtered_actions) == 0:
            layout.label(text="No actions found", icon='INFO')
        else:
            # Display actions in a compact list
            for action in sorted(filtered_actions, key=lambda x: x.name):
                # Check if this is the current action
                is_current = False
                if obj and obj.animation_data:
                    if obj.animation_data.action == action:
                        is_current = True
                
                # Action name and buttons on same line
                row = layout.row(align=True)
                
                # Fake user toggle (shield icon)
                fake_user_icon = 'FAKE_USER_ON' if action.use_fake_user else 'FAKE_USER_OFF'
                op = row.operator("animlib.toggle_fake_user", text="", icon=fake_user_icon)
                op.action_name = action.name
                
                # Action name with icon
                if is_current:
                    row.label(text=action.name, icon='RADIOBUT_ON')
                else:
                    row.label(text=action.name, icon='ACTION')
                
                # Frame range info (compact format)
                if action.frame_range:
                    start_frame = int(action.frame_range[0])
                    end_frame = int(action.frame_range[1])
                    row.label(text=f"[{start_frame}-{end_frame}]")
                
                # Apply button
                if is_current:
                    op = row.operator("animlib.apply_action", text="", icon='CHECKMARK')
                    op.action_name = action.name
                    op_row = row.row()
                    op_row.enabled = False
                else:
                    op = row.operator("animlib.apply_action", text="", icon='PLAY')
                    op.action_name = action.name
                
                # Duplicate button
                op = row.operator("animlib.duplicate_action", text="", icon='DUPLICATE')
                op.action_name = action.name
                
                # Delete button
                op = row.operator("animlib.delete_action", text="", icon='TRASH')
                op.action_name = action.name
                
                layout.separator(factor=0.3)


# ==================== PROPERTIES ====================

def register_properties():
    """Register scene properties"""
    bpy.types.Scene.animlib_search = StringProperty(
        name="Search",
        description="Filter actions by name",
        default="",
    )


def unregister_properties():
    """Unregister scene properties"""
    if hasattr(bpy.types.Scene, 'animlib_search'):
        del bpy.types.Scene.animlib_search


# ==================== REGISTRATION ====================

classes = (
    ANIMLIB_OT_apply_action,
    ANIMLIB_OT_remove_action,
    ANIMLIB_OT_toggle_fake_user,
    ANIMLIB_OT_new_action,
    ANIMLIB_OT_duplicate_action,
    ANIMLIB_OT_delete_action,
    ANIMLIB_OT_refresh_list,
    ANIMLIB_OT_filter_actions,
    ANIMLIB_PT_main_panel,
)


def register():
    """Register all classes and properties"""
    for cls in classes:
        bpy.utils.register_class(cls)
    register_properties()
    print("Animation Library registered successfully!")


def unregister():
    """Unregister all classes and properties"""
    unregister_properties()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("Animation Library unregistered")


# ==================== MAIN ====================

if __name__ == "__main__":
    register()