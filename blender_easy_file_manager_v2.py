import bpy
import os
from bpy.props import StringProperty, EnumProperty, BoolProperty, CollectionProperty, IntProperty
from bpy.types import Operator, Panel, PropertyGroup, UIList


bl_info = {
    "name": "Easy File Manager",
    "author": "Your Name",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Animation",
    "description": "Easy file opening and asset linking with selection",
    "warning": "",
    "doc_url": "",
    "category": "Import-Export",
}


# Property for individual asset items
class AssetItem(PropertyGroup):
    name: StringProperty(name="Asset Name")
    selected: BoolProperty(name="Select", default=True)


# Property Group to store settings
class EasyFileManagerProperties(PropertyGroup):
    file_path: StringProperty(
        name="File Path",
        description="Paste the file path here",
        default="",
        subtype='FILE_PATH'
    )
    
    action_type: EnumProperty(
        name="Action",
        description="Choose what to do with the file",
        items=[
            ('OPEN', "Open File", "Open the .blend file"),
            ('APPEND', "Append", "Append objects/data from file"),
            ('LINK', "Link", "Link objects/data from file"),
        ],
        default='OPEN'
    )
    
    asset_type: EnumProperty(
        name="Asset Type",
        description="Type of asset to link/append",
        items=[
            ('OBJECT', "Objects", "Link/Append objects"),
            ('COLLECTION', "Collections", "Link/Append collections"),
            ('MATERIAL', "Materials", "Link/Append materials"),
            ('NODEGROUP', "Node Groups", "Link/Append node groups"),
            ('WORLD', "Worlds", "Link/Append worlds"),
        ],
        default='OBJECT'
    )
    
    link_collections: BoolProperty(
        name="Link as Collection Instance",
        description="Link collection as instance in the scene",
        default=True
    )
    
    available_assets: CollectionProperty(type=AssetItem)
    assets_scanned: BoolProperty(default=False)
    active_asset_index: IntProperty(name="Active Asset Index", default=0)


# UIList for displaying available assets
class EASY_UL_AssetList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.scale_y = 0.8
            row.prop(item, "selected", text="")
            row.label(text=item.name, icon='OUTLINER_OB_GROUP_INSTANCE' if context.scene.easy_file_manager.asset_type == 'COLLECTION' else 'OBJECT_DATA')


# Operator to scan file for available assets
class EASY_OT_ScanFile(Operator):
    bl_idname = "easy.scan_file"
    bl_label = "Scan File"
    bl_description = "Scan the file for available assets"
    
    def execute(self, context):
        props = context.scene.easy_file_manager
        file_path = props.file_path.strip().strip('"').strip("'").strip()
        
        if not file_path:
            self.report({'ERROR'}, "Please enter a file path first")
            return {'CANCELLED'}
        
        file_path = os.path.normpath(file_path)
        file_path = bpy.path.abspath(file_path)
        
        if not os.path.exists(file_path):
            self.report({'ERROR'}, f"File not found: {file_path}")
            return {'CANCELLED'}
        
        if not file_path.endswith('.blend'):
            self.report({'ERROR'}, "File must be a .blend file")
            return {'CANCELLED'}
        
        # Clear existing items
        props.available_assets.clear()
        
        # Scan file for assets
        try:
            with bpy.data.libraries.load(file_path, link=False) as (data_from, data_to):
                if props.asset_type == 'OBJECT':
                    asset_list = data_from.objects
                elif props.asset_type == 'COLLECTION':
                    asset_list = data_from.collections
                elif props.asset_type == 'MATERIAL':
                    asset_list = data_from.materials
                elif props.asset_type == 'NODEGROUP':
                    asset_list = data_from.node_groups
                elif props.asset_type == 'WORLD':
                    asset_list = data_from.worlds
                
                # Add to list
                for asset_name in asset_list:
                    item = props.available_assets.add()
                    item.name = asset_name
                    item.selected = True  # Select all by default
            
            props.assets_scanned = True
            
            if len(props.available_assets) == 0:
                self.report({'WARNING'}, f"No {props.asset_type.lower()}s found in file")
            else:
                self.report({'INFO'}, f"Found {len(props.available_assets)} {props.asset_type.lower()}(s)")
                
        except Exception as e:
            self.report({'ERROR'}, f"Error scanning file: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}


# Operator to select/deselect all assets
class EASY_OT_SelectAllAssets(Operator):
    bl_idname = "easy.select_all_assets"
    bl_label = "Select All"
    bl_description = "Select or deselect all assets"
    
    action: EnumProperty(
        items=[
            ('SELECT', "Select All", ""),
            ('DESELECT', "Deselect All", ""),
        ]
    )
    
    def execute(self, context):
        props = context.scene.easy_file_manager
        select_value = (self.action == 'SELECT')
        
        for item in props.available_assets:
            item.selected = select_value
        
        return {'FINISHED'}


# Operator to execute file operations
class EASY_OT_ExecuteFileAction(Operator):
    bl_idname = "easy.execute_file_action"
    bl_label = "Execute"
    bl_description = "Execute the selected action"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.easy_file_manager
        file_path = props.file_path.strip()
        
        # Validate file path
        if not file_path:
            self.report({'ERROR'}, "Please enter a file path")
            return {'CANCELLED'}
        
        # Remove quotes if present (common when copy-pasting)
        file_path = file_path.strip('"').strip("'").strip()
        
        # Handle Windows paths - convert backslashes to forward slashes or use raw path
        # Also expand any relative paths
        file_path = os.path.normpath(file_path)
        file_path = bpy.path.abspath(file_path)
        
        if not os.path.exists(file_path):
            # Show what we're actually looking for to help debug
            self.report({'ERROR'}, f"File not found. Looking for: {file_path}")
            return {'CANCELLED'}
        
        if not file_path.endswith('.blend'):
            self.report({'ERROR'}, "File must be a .blend file")
            return {'CANCELLED'}
        
        # Execute action
        try:
            if props.action_type == 'OPEN':
                bpy.ops.wm.open_mainfile(filepath=file_path)
                self.report({'INFO'}, f"Opened: {os.path.basename(file_path)}")
                
            elif props.action_type in ['APPEND', 'LINK']:
                self.link_or_append_assets(context, file_path, props)
                
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}
    
    def link_or_append_assets(self, context, file_path, props):
        is_link = (props.action_type == 'LINK')
        
        # Get selected asset names
        selected_assets = [item.name for item in props.available_assets if item.selected]
        
        if not selected_assets:
            self.report({'WARNING'}, "No assets selected")
            return
        
        imported_items = []
        
        # Load only selected assets from file
        with bpy.data.libraries.load(file_path, link=is_link) as (data_from, data_to):
            if props.asset_type == 'OBJECT':
                data_to.objects = [name for name in data_from.objects if name in selected_assets]
                imported_items = data_to.objects
                
            elif props.asset_type == 'COLLECTION':
                data_to.collections = [name for name in data_from.collections if name in selected_assets]
                imported_items = data_to.collections
                
            elif props.asset_type == 'MATERIAL':
                data_to.materials = [name for name in data_from.materials if name in selected_assets]
                imported_items = data_to.materials
                
            elif props.asset_type == 'NODEGROUP':
                data_to.node_groups = [name for name in data_from.node_groups if name in selected_assets]
                imported_items = data_to.node_groups
                
            elif props.asset_type == 'WORLD':
                data_to.worlds = [name for name in data_from.worlds if name in selected_assets]
                imported_items = data_to.worlds
        
        # Post-processing based on asset type
        if props.asset_type == 'COLLECTION':
            if is_link and props.link_collections:
                # Create collection instances
                count = 0
                for coll in imported_items:
                    if coll is not None:
                        empty = bpy.data.objects.new(f"{coll.name}_instance", None)
                        empty.instance_type = 'COLLECTION'
                        empty.instance_collection = coll
                        context.scene.collection.objects.link(empty)
                        count += 1
                self.report({'INFO'}, f"Created {count} collection instance(s)")
            else:
                # Just link collections to scene
                count = 0
                for coll in imported_items:
                    if coll is not None and coll.name not in context.scene.collection.children:
                        context.scene.collection.children.link(coll)
                        count += 1
                action_text = "Linked" if is_link else "Appended"
                self.report({'INFO'}, f"{action_text} {count} collection(s)")
                
        elif props.asset_type == 'OBJECT':
            # Link objects to scene
            count = 0
            for obj in imported_items:
                if obj is not None:
                    if obj.name not in context.scene.collection.objects:
                        context.scene.collection.objects.link(obj)
                        count += 1
            action_text = "Linked" if is_link else "Appended"
            self.report({'INFO'}, f"{action_text} {count} object(s) to scene")
            
        else:
            # Materials, node groups, worlds are just loaded into data
            action_text = "Linked" if is_link else "Appended"
            count = len([x for x in imported_items if x is not None])
            self.report({'INFO'}, f"{action_text} {count} {props.asset_type.lower()}(s)")


# Operator to browse for file
class EASY_OT_BrowseFile(Operator):
    bl_idname = "easy.browse_file"
    bl_label = "Browse"
    bl_description = "Browse for a .blend file"
    
    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default='*.blend', options={'HIDDEN'})
    
    def execute(self, context):
        context.scene.easy_file_manager.file_path = self.filepath
        context.scene.easy_file_manager.assets_scanned = False
        context.scene.easy_file_manager.available_assets.clear()
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# UI Panel
class EASY_PT_FileManagerPanel(Panel):
    bl_label = "Easy File Manager"
    bl_idname = "EASY_PT_file_manager"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Animation'
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False
        
        props = context.scene.easy_file_manager
        
        # File path input - compact
        row = layout.row(align=True)
        row.scale_y = 0.9
        row.prop(props, "file_path", text="")
        row.operator("easy.browse_file", text="", icon='FILEBROWSER')
        
        # Action type - compact
        row = layout.row(align=True)
        row.scale_y = 0.8
        row.prop(props, "action_type", expand=True)
        
        # Asset options (only show for append/link)
        if props.action_type in ['APPEND', 'LINK']:
            col = layout.column(align=True)
            col.scale_y = 0.9
            col.prop(props, "asset_type", text="")
            
            # Scan button - compact
            col.operator("easy.scan_file", text="Scan Assets", icon='VIEWZOOM')
            
            # Show asset list if scanned
            if props.assets_scanned and len(props.available_assets) > 0:
                col.separator(factor=0.5)
                
                # Select/Deselect all buttons - compact
                row = col.row(align=True)
                row.scale_y = 0.8
                op = row.operator("easy.select_all_assets", text="All")
                op.action = 'SELECT'
                op = row.operator("easy.select_all_assets", text="None")
                op.action = 'DESELECT'
                
                # Asset list with scroll - max 5 visible rows
                col.template_list("EASY_UL_AssetList", "", props, "available_assets", props, "active_asset_index", rows=5, maxrows=5)
                
                # Selected count - compact
                row = col.row()
                row.scale_y = 0.7
                selected_count = sum(1 for item in props.available_assets if item.selected)
                row.label(text=f"Selected: {selected_count}/{len(props.available_assets)}", icon='INFO')
            
            if props.asset_type == 'COLLECTION' and props.action_type == 'LINK':
                row = col.row()
                row.scale_y = 0.8
                row.prop(props, "link_collections", text="As Instance")
        
        # Execute button - compact
        layout.separator(factor=0.5)
        row = layout.row()
        row.scale_y = 1.2
        
        if props.action_type == 'OPEN':
            row.operator("easy.execute_file_action", text="Open File", icon='FILE_FOLDER')
        elif props.action_type == 'APPEND':
            row.operator("easy.execute_file_action", text="Append Selected", icon='APPEND_BLEND')
        else:
            row.operator("easy.execute_file_action", text="Link Selected", icon='LINK_BLEND')


# Registration
classes = (
    AssetItem,
    EasyFileManagerProperties,
    EASY_UL_AssetList,
    EASY_OT_ScanFile,
    EASY_OT_SelectAllAssets,
    EASY_OT_ExecuteFileAction,
    EASY_OT_BrowseFile,
    EASY_PT_FileManagerPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.easy_file_manager = bpy.props.PointerProperty(type=EasyFileManagerProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Scene, 'easy_file_manager'):
        del bpy.types.Scene.easy_file_manager

if __name__ == "__main__":
    register()