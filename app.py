import flet as ft

import aiapi
import mcp_manager


async def main(page: ft.Page):
    page.title = "OpenGPT"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#000000"
    page.padding = 0

    page.fonts = {
        "Roboto": "roboto.ttf",
        "Emoji": "NotoColorEmoji.ttf",
        "monospace": "robotomono.ttf",
    }

    default_text_style = ft.TextStyle(
        color="#FFFFFF",
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

    mcp = mcp_manager.MCPManager("resources/mcp/main_server.py")
    await mcp.connect()
    conversation = aiapi.Conversation(
        mcp=mcp, provider="groq", model="openai/gpt-oss-120b"
    )

    chat_history = ft.ListView(
        expand=True,
        spacing=20,
        padding=ft.Padding.symmetric(vertical=24, horizontal=16),
        auto_scroll=True,
    )

    status_text = ft.Text(size=12, color="#8E8E93", italic=True)

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
                        bgcolor="#27272A",
                        padding=ft.Padding.symmetric(horizontal=18, vertical=12),
                        border_radius=ft.BorderRadius.all(20),
                        width=480 if len(text) > 60 else None,
                    )
                ],
            )
        elif type == "ai":
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
                            md_style_sheet=ai_markdown_style,
                        ),
                    ),
                ],
            )
        elif type == "tool":
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
                        ),
                    ),
                ],
            )

    def ui_tool_status(tool_name: str, args: dict):
        chat_history.controls.append(
            create_message_bubble(f"Uses tool {tool_name} with {args}", type="tool")
        )
        page.update()

    async def send_message(e):
        message = input_text.value.strip()
        if not message:
            return

        input_text.value = ""
        input_text.disabled = True
        send_button.disabled = True
        status_text.value = "OpenGPT is thinking..."
        chat_history.controls.append(create_message_bubble(message, type="user"))
        page.update()

        try:
            reply = await conversation.send_message(
                message=message, on_tool_call=ui_tool_status
            )
            chat_history.controls.append(create_message_bubble(reply, type="ai"))
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
            input_text.disabled = False
            send_button.disabled = False
            page.update()
            await input_text.focus()

    input_text = ft.TextField(
        hint_text="Message to OpenGPT...",
        hint_style=ft.TextStyle(
            color="#71717A",
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
        bgcolor="#FFFFFF",
        icon_size=20,
        on_click=send_message,
    )

    input_bar = ft.Container(
        bgcolor="#212121",
        border=ft.Border.all(1, "#212121"),
        border_radius=26,
        padding=ft.Padding.only(left=20, right=8, top=6, bottom=6),
        content=ft.Row(
            controls=[input_text, send_button],
            vertical_alignment=ft.CrossAxisAlignment.END,
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

    page.add(
        ft.Row(
            controls=[main_column],
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )
    )


async def run():
    await ft.run_async(main, assets_dir="resources/assets")
