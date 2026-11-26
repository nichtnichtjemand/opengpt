import os
import subprocess

import flet as ft

import aiapi
import mcp_manager
from config import get_api_key, save_api_key


async def main(page: ft.Page, mcp):
    page.title = "OpenGPT"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#f5ebe0"
    page.padding = 0
    page.fonts = {
        "Roboto": "roboto.ttf",
        "Emoji": "NotoColorEmoji.ttf",
        "monospace": "robotomono.ttf",
    }
    page.window.icon = "icon.png"

    default_text_style = ft.TextStyle(
        color="#000000",
        font_family="Roboto",
        font_family_fallback=["Emoji"],
    )

    custom_theme = ft.Theme(
        color_scheme_seed=ft.Colors.BLACK,
        use_material3=True,
        font_family="Roboto",
        text_theme=ft.TextTheme(
            body_medium=default_text_style,
            body_large=default_text_style,
            body_small=default_text_style,
            title_medium=default_text_style,
            title_large=default_text_style,
            label_large=default_text_style,
        ),
    )

    page.theme = custom_theme
    page.dark_theme = custom_theme

    can_submit = True

    if not get_api_key("GROQ_API_KEY"):
        key_field = ft.TextField(
            label="Groq API Key",
            password=True,
            can_reveal_password=True,
            autofocus=True,
            width=420,
        )

        def save_key(_):
            try:
                save_api_key("GROQ_API_KEY", key_field.value or "")
            except ValueError as error:
                key_field.error_text = str(error)
                page.update()
                return

            aiapi.reset_api_clients()
            key_dialog.open = False
            page.update()

        key_field.on_submit = save_key
        key_dialog = ft.AlertDialog(
            modal=True,
            title="Groq API Key erforderlich",
            content=ft.Column(
                controls=[
                    ft.Text("Enter your Qroq API key."),
                    key_field,
                ],
                tight=True,
                spacing=12,
            ),
            actions=[
                ft.TextButton(content="Save", on_click=save_key),
            ],
        )
        page.show_dialog(key_dialog)

    conversation = aiapi.Conversation(
        # mcp=mcp,
        # provider="groq",
        # model="openai/gpt-oss-120b",
        mcp=mcp,
        provider="google",
        model="gemini-3.5-flash-lite",
    )

    chat_history = ft.ListView(
        expand=True,
        spacing=20,
        padding=ft.Padding.symmetric(vertical=24, horizontal=16),
        auto_scroll=True,
    )

    status_text = ft.Text(size=12, color="#8E8E93", italic=True)

    def load_conversation(chat_id):
        nonlocal conversation

        conversation = aiapi.Conversation.load(chat_id, mcp=mcp)

        chat_history.controls.clear()

        for item in conversation.ui_history:
            chat_history.controls.append(
                create_message_bubble(item["text"], item["type"])
            )

        status_text.value = ""
        input_text.value = ""
        page.update()

    ai_markdown_style = ft.MarkdownStyleSheet(
        p_text_style=default_text_style,
        h1_text_style=default_text_style,
        h2_text_style=default_text_style,
        h3_text_style=default_text_style,
        h4_text_style=default_text_style,
        h5_text_style=default_text_style,
        h6_text_style=default_text_style,
        list_bullet_text_style=default_text_style,
        blockquote_text_style=default_text_style,
        code_text_style=default_text_style,
    )

    tool_markdown_style = ft.MarkdownStyleSheet(
        p_text_style=ft.TextStyle(
            color="#454545",
            font_family="Roboto",
            font_family_fallback=["Emoji"],
        ),
    )

    def open_folder(path):
        path = os.path.abspath(path)

        if not os.path.isdir(path):
            status_text.value = f"Folder not found: {path}"
            page.update()
            return

        try:
            subprocess.Popen(
                ["xdg-open", path],
                start_new_session=True,
            )
        except OSError as error:
            status_text.value = f"Error while opening: {error}"
            page.update()

    def create_message_bubble(text, type):
        if type == "user":
            return ft.Row(
                alignment=ft.MainAxisAlignment.END,
                controls=[
                    ft.Container(
                        content=ft.Text(
                            text,
                            size=15,
                            color="#FFFFFF",
                            style=default_text_style,
                        ),
                        bgcolor="#38383A",
                        padding=ft.Padding.symmetric(horizontal=18, vertical=12),
                        border_radius=ft.BorderRadius.all(20),
                        width=480 if len(text) > 60 else None,
                    )
                ],
            )

        if type == "ai":
            content = [
                ft.Markdown(
                    text,
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                    md_style_sheet=ai_markdown_style,
                    on_tap_link=handle_markdown_link,
                )
            ]

            if "Created successfully:" in text:
                path = (
                    text.split("Created successfully:", 1)[1]
                    .strip()
                    .splitlines()[0]
                    .strip()
                    .strip("`\"'")
                )

                content.append(
                    ft.TextButton(
                        content="Open folder",
                        icon=ft.Icons.FOLDER_OPEN,
                        on_click=lambda e: open_folder(path),
                    )
                )

            return ft.Row(
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.only(top=4),
                        content=ft.Column(
                            controls=content,
                            spacing=4,
                            horizontal_alignment=ft.CrossAxisAlignment.START,
                        ),
                    )
                ],
            )

        if type == "tool":
            return ft.Row(
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.only(top=4),
                        content=ft.Markdown(
                            text,
                            selectable=True,
                            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                            md_style_sheet=tool_markdown_style,
                            on_tap_link=handle_markdown_link,
                        ),
                    )
                ],
            )

    def ui_tool_status(tool_name: str, args: dict):
        if tool_name == "get_skill":
            message = f"Reads about {args['name']}"
        elif tool_name == "workspace_write_file":
            message = "Writes a file"
        elif tool_name == "workspace_run_shell":
            message = "Runs a command"
        elif tool_name == "workspace_export_folder":
            message = "Exports files"
        elif tool_name == "workspace_list_files":
            message = "Reads all files"
        elif tool_name == "secret":
            message = "Reads the secret"
        elif tool_name == "get_weather":
            message = "Gets the weather"
        elif tool_name == "system_status":
            message = "Checks the system status"
        elif tool_name == "get_memory":
            message = "Remembers information about you"
        elif tool_name == "add_memory_block" or tool_name == "edit_memory":
            message = "Saves memory aout you"
        elif tool_name == "reset_memory" or tool_name == "remove_memory_block":
            message = "Deletes information about you"
        elif tool_name == "search_online":
            message = "Searches online"
        else:
            message = f"Runs tool {tool_name} {args}"
        chat_history.controls.append(create_message_bubble(message, type="tool"))
        page.update()

    async def handle_markdown_link(e: ft.Event[ft.Markdown]):
        await ft.UrlLauncher().launch_url(e.data)

    async def send_message(e):
        message = input_text.value.strip()
        if not message:
            return
        nonlocal can_submit
        if not can_submit:
            return
        can_submit = False

        input_text.value = ""
        send_button.disabled = True
        status_text.value = "OpenGPT is thinking..."
        chat_history.controls.append(create_message_bubble(message, type="user"))
        page.update()

        try:
            reply = await conversation.send_message(
                message=message, on_tool_call=ui_tool_status
            )
            chat_history.controls.append(create_message_bubble(reply, type="ai"))
            refresh_chat_list()
        except Exception as err:  # noqa: BLE001
            chat_history.controls.append(
                ft.Text(
                    f"An error occurred: {err}",
                    color=ft.Colors.RED_400,
                    style=default_text_style,
                )
            )

        finally:
            status_text.value = ""
            send_button.disabled = False
            can_submit = True
            page.update()
            await input_text.focus()

    chat_list = ft.Column(
        spacing=4,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    def refresh_chat_list():
        saved_chats = aiapi.Conversation.list_saved_chats()
        chat_list.controls.clear()

        for chat in saved_chats:
            chat_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.CHAT_OUTLINED,
                                size=18,
                                color="#62564f",
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        chat["title"],
                                        size=13,
                                        weight=ft.FontWeight.W_500,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Text(
                                        chat["model"],
                                        size=10,
                                        color="#8E8178",
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=10,
                    border_radius=10,
                    on_click=lambda e, chat_id=chat["chat_id"]: load_conversation(
                        chat_id
                    ),
                    ink=True,
                )
            )

        page.update()

    def open_settings():
        groq_key_field = ft.TextField(
            label="Groq API Key",
            password=True,
            can_reveal_password=True,
            value=get_api_key("GROQ_API_KEY") or "",
            width=400,
        )

        google_key_field = ft.TextField(
            label="Google API Key",
            password=True,
            can_reveal_password=True,
            value=get_api_key("GOOGLE_API_KEY") or "",
            width=400,
        )

        def save_settings(e):
            try:
                save_api_key("GROQ_API_KEY", groq_key_field.value or "")
                save_api_key("GOOGLE_API_KEY", google_key_field.value or "")

                aiapi.reset_api_clients()

                page.pop_dialog()
                page.update()

            except ValueError as error:
                status_text.value = str(error)
                page.update()

        settings_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Settings"),
            content=ft.Column(
                controls=[
                    ft.Text("API Keys", weight=ft.FontWeight.BOLD),
                    groq_key_field,
                    google_key_field,
                ],
                tight=True,
                spacing=15,
                width=400,
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=lambda e: page.pop_dialog(),
                ),
                ft.TextButton(
                    "Save",
                    on_click=save_settings,
                ),
            ],
        )

        page.show_dialog(settings_dialog)

    input_text = ft.TextField(
        hint_text="Message to OpenGPT...",
        hint_style=ft.TextStyle(
            color="#3A3A3A",
            font_family="Roboto",
            font_family_fallback=["Emoji"],
        ),
        text_style=default_text_style,
        border=ft.InputBorder.NONE,
        filled=False,
        expand=True,
        multiline=True,
        min_lines=1,
        max_lines=5,
        shift_enter=True,
        on_submit=send_message,
        text_size=15,
    )

    send_button = ft.IconButton(
        icon=ft.Icons.ARROW_UPWARD_ROUNDED,
        icon_color="#121214",
        bgcolor="#d5bdaf",
        icon_size=20,
        on_click=send_message,
    )

    input_bar = ft.Container(
        bgcolor="#e3d5ca",
        border=ft.Border.all(1, "#e3d5ca"),
        border_radius=26,
        padding=ft.Padding.only(left=20, right=8, top=6, bottom=6),
        content=ft.Row(
            controls=[input_text, send_button],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    main_column = ft.Container(
        width=780,
        expand=True,
        padding=ft.Padding.only(bottom=20, left=16, right=16),
        content=ft.Column(
            controls=[
                chat_history,
                ft.Container(content=status_text, padding=ft.Padding.only(left=12)),
                input_bar,
            ],
            spacing=8,
        ),
    )
    sidebar = ft.Container(
        width=260,
        bgcolor="#e4ccb8",
        padding=14,
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Button(
                        "New Chat",
                        on_click=lambda e: new_conversation(),
                        expand=True,
                    ),
                    padding=ft.Padding.only(bottom=8),
                ),
                ft.TextButton(
                    "Settings",
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    on_click=lambda e: open_settings(),
                ),
                ft.Divider(color="#ecded2"),
                ft.Container(
                    content=ft.Text(
                        "Conversations",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color="#8E8178",
                    ),
                    padding=ft.Padding.only(left=8, top=8, bottom=8),
                ),
                chat_list,
            ],
            expand=True,
            spacing=4,
        ),
    )

    def new_conversation():
        nonlocal conversation

        conversation = aiapi.Conversation(
            mcp=mcp,
            provider="google",
            model="gemini-3.5-flash-lite",
        )

        chat_history.controls.clear()
        status_text.value = ""
        input_text.value = ""

        refresh_chat_list()
        page.update()

    page.add(
        ft.Row(
            controls=[
                sidebar,
                main_column,
            ],
            spacing=0,
            expand=True,
        )
    )

    refresh_chat_list()
    page.window.visible = True
    page.update()


async def run():
    mcp = mcp_manager.MCPManager("resources/mcp/main_server.py")

    try:
        await mcp.connect()

        async def app_main(page: ft.Page):
            await main(page, mcp)

        await ft.run_async(
            app_main, assets_dir="assets", view=ft.AppView.FLET_APP_HIDDEN
        )
    finally:
        await mcp.close()
