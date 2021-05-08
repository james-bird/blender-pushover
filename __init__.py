# import the bpy module to access blender API
import bpy
from bpy.props import StringProperty, IntProperty, BoolProperty
import http.client, urllib, ssl
import requests
from pathlib import Path
from datetime import datetime
import tempfile
import imbuf

bl_info = {
    "name": "Pushover notifier",
    "category": "User Interface",
    "blender": (2, 80, 0),
}

class PushOverSend():

    def __init__(self):
        self.user = bpy.context.preferences.addons['blender-pushover'].preferences.user
        self.token = bpy.context.preferences.addons['blender-pushover'].preferences.token
        self.context = ssl._create_unverified_context()
        self.conn = http.client.HTTPSConnection("api.pushover.net:443", context=self.context)

    def send_image(self, title, str, file_path):
        r = requests.post("https://api.pushover.net/1/messages.json", data={
            "title": title,
            "token": self.token,
            "user": self.user,
            "message": str},
            files={
            "attachment": (Path(file_path).name, open(file_path, "rb"), "image/png")
        })

    def send_string(self, title, str):
        self.conn.request("POST", "/1/messages.json",
                          urllib.parse.urlencode({
                              "title": title,
                              "token": self.token,
                              "user": self.user,
                              "message": str,
                          }), {"Content-type": "application/x-www-form-urlencoded"},)
        self.conn.getresponse()

    def send_test_message(self):
        self.send_string("Test message", "Hello, World!")


def notify(self):

    txt_message = bpy.context.scene.custom_props.text_msg_toggle
    img_message = bpy.context.scene.custom_props.img_msg_toggle
    scaling =  bpy.context.scene.custom_props.img_reduce_res/100
    now = datetime.fromtimestamp(round(datetime.now().timestamp()))

    file_name = Path(bpy.data.filepath).name
    frame_number = bpy.context.scene.frame_current
    title_string = "Rendered {}".format(file_name)
    message_str = "Rendered {}\nFrame number {}\n{}".format(file_name, frame_number, now)

    strt_frame =  bpy.context.scene.frame_start
    # end_frame = bpy.context.scene.frame_end


    skp_no = bpy.context.scene.custom_props.frame_skp
    pushover = PushOverSend()



    if (frame_number - strt_frame) % (skp_no+1) == 0:
        if img_message == True:
            render_file_path = tempfile.gettempdir() + "image_file.png"
            render_file_path_scaled = tempfile.gettempdir() + "image_file_scaled.png"
            bpy.data.images["Render Result"].save_render(render_file_path)
            imb = imbuf.load(render_file_path)
            new_size = tuple([round(scaling*x) for x in imb.size])
            imb.resize(new_size)
            imbuf.write(imb, render_file_path_scaled)
            pushover.send_image(title_string, message_str, render_file_path_scaled)
        elif txt_message == True:
            pushover.send_string(title_string, message_str)


class CustomPropertyGroup(bpy.types.PropertyGroup):
    text_msg_toggle: bpy.props.BoolProperty(name='text_msg_toggle')
    img_msg_toggle: bpy.props.BoolProperty(name='img_msg_toggle')
    img_reduce_res: bpy.props.IntProperty(name='img_reduce_res', min=5, max=100, subtype = 'PERCENTAGE', default = 50)
    frame_skp: bpy.props.IntProperty(name='frame_skp', min=0, soft_max=10, default = 0)

class CUSTOM_PT_ToolShelf(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_label = 'Pushover Notification'
    bl_context = 'render'
    bl_category = 'View'


    def draw(self, context):
        layout = self.layout
        layout.label(text="Pushover messaging options:")
        subrow = layout.row(align=True)
        subrow.prop(context.scene.custom_props, 'text_msg_toggle', text='Send message when render complete')
        subrow = layout.row(align=True)
        subrow.prop(context.scene.custom_props, 'img_msg_toggle', text='Send rendered image when render complete')
        subrow = layout.row(align=True)
        subrow.prop(context.scene.custom_props, 'img_reduce_res', text='Sent image scaling')
        subrow = layout.row(align=True)
        subrow.prop(context.scene.custom_props, 'frame_skp', text='Number of frames to skip')
        subrow = layout.row(align=True)
        layout.operator('custom.send_test_message', text='Send test message')


class CustomSimpleOperator(bpy.types.Operator):

    bl_idname = 'custom.send_test_message'
    bl_label = 'Send test message'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        pushover = PushOverSend()
        pushover.send_test_message()
        self.report({'INFO'}, "Sent test message!")
        return {'FINISHED'}


class ExampleAddonPreferences(bpy.types.AddonPreferences):

    bl_idname = __name__

    user: StringProperty(
        name="user",
        default="",
    )

    token: StringProperty(
        name="token",
        default="",
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Pushover user and token information.")
        layout.prop(self, "user")
        layout.prop(self, "token")


def register():
    bpy.utils.register_class(CustomPropertyGroup)
    bpy.types.Scene.custom_props = bpy.props.PointerProperty(type=CustomPropertyGroup)
    bpy.utils.register_class(CustomSimpleOperator)
    bpy.utils.register_class(CUSTOM_PT_ToolShelf)
    bpy.utils.register_class(ExampleAddonPreferences)
    bpy.app.handlers.render_complete.append(notify)
    bpy.app.handlers.render_write.append(notify)

def unregister():
    del bpy.types.Scene.custom_props
    bpy.utils.unregister_class(CustomPropertyGroup)
    bpy.utils.unregister_class(CustomSimpleOperator)
    bpy.utils.unregister_class(CUSTOM_PT_ToolShelf)
    bpy.utils.unregister_class(ExampleAddonPreferences)
    bpy.app.handlers.render_complete.remove(notify)
    bpy.app.handlers.render_write.remove(notify)

if __name__ == '__main__':
    register()
