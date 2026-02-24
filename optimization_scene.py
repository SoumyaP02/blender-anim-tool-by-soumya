import bpy

bl_info = {
    "name": "One-Click Performance Optimizer_soumya",
    "author": "soumya patra",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Animation",
    "description": "Optimize Blender settings for better FPS with one click",
    "category": "System",
}

class PERFORMANCE_OT_optimize(bpy.types.Operator):
    """Optimize Blender settings for better performance"""
    bl_idname = "performance.optimize"
    bl_label = "Optimize Performance"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        
        # Switch to EEVEE (faster than Cycles)
        scene.render.engine = 'BLENDER_EEVEE'
        self.report({'INFO'}, "Switched to EEVEE render engine")
        
        # EEVEE Shadow Settings - Disable/Reduce shadows
        eevee = scene.eevee
        eevee.use_shadows = False
        eevee.use_soft_shadows = False
        self.report({'INFO'}, "Disabled EEVEE shadows")
        
        # Disable expensive EEVEE effects
        eevee.use_gtao = False  # Ambient Occlusion
        eevee.use_bloom = False
        eevee.use_ssr = False  # Screen Space Reflections
        eevee.use_volumetric_shadows = False
        eevee.use_motion_blur = False
        self.report({'INFO'}, "Disabled expensive EEVEE effects")
        
        # Simplify Settings
        scene.render.use_simplify = True
        scene.render.simplify_subdivision =0  # Disable subdivision in viewport
        scene.render.simplify_subdivision_render = 2  # Low subdivision for render
        scene.render.simplify_volumes = 0  # Low subdivision for render	
        scene.render.simplify_child_particles = 0  # Reduce particles
        scene.render.simplify_child_particles_render = 0.5
        self.report({'INFO'}, "Enabled Simplify settings")
        
        # Disable expensive object settings in scene
        for obj in scene.objects:
            # Disable modifiers in viewport
            for mod in obj.modifiers:
                mod.show_viewport = False
            
            # Simplify particle systems
            if hasattr(obj, 'particle_systems'):
                for psys in obj.particle_systems:
                    psys.settings.display_percentage = 10
        
        self.report({'INFO'}, "Simplified objects and particles")
        
        # Reduce texture quality
        scene.render.use_high_quality_normals = False
        
        # Set lower samples for EEVEE
        eevee.taa_render_samples = 32
        eevee.taa_samples = 8  # Viewport samples
        
        self.report({'INFO'}, "✓ Performance optimization complete!")
        return {'FINISHED'}


class PERFORMANCE_OT_restore(bpy.types.Operator):
    """Restore default quality settings"""
    bl_idname = "performance.restore"
    bl_label = "Restore Quality"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        eevee = scene.eevee
        
        # Re-enable shadows
        eevee.use_shadows = True
        eevee.use_soft_shadows = True
        
        # Re-enable effects
        eevee.use_gtao = True
        eevee.use_bloom = False
        eevee.use_ssr = True
        
        # Disable simplify
        scene.render.use_simplify = False
        
        # Re-enable modifiers
        for obj in scene.objects:
            for mod in obj.modifiers:
                mod.show_viewport = True
            
            if hasattr(obj, 'particle_systems'):
                for psys in obj.particle_systems:
                    psys.settings.display_percentage = 100
        
        # Higher samples
        eevee.taa_render_samples = 64
        eevee.taa_samples = 16
        
        self.report({'INFO'}, "✓ Quality settings restored")
        return {'FINISHED'}


class PERFORMANCE_PT_panel(bpy.types.Panel):
    """Performance Optimizer Panel"""
    bl_label = "Performance Optimizer"
    bl_idname = "PERFORMANCE_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Animation'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Main buttons in one row
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("performance.optimize", icon='SHADERFX', text="⚡ Optimize FPS")
        row.operator("performance.restore", icon='LOOP_BACK', text="Restore Quality")


# Registration
classes = (
    PERFORMANCE_OT_optimize,
    PERFORMANCE_OT_restore,
    PERFORMANCE_PT_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()