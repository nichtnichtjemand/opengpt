import aiapi


def test_conversation_save_and_load(tmp_path, monkeypatch):

    monkeypatch.setattr(aiapi, "get_chats_dir", lambda: tmp_path)

    conversation = aiapi.Conversation(mcp=None, model="pytest")

    conversation.add_ui_entry("user", "Hi OpenGPT from a test!")
    conversation.add_ui_entry("ai", "Hi test from OpenGPT!")

    chat_id = conversation.chat_id

    loaded_conversation = aiapi.Conversation.load(mcp=None, chat_id_or_path=chat_id)

    assert loaded_conversation.model == "pytest"
    assert loaded_conversation.chat_id == chat_id
    assert len(loaded_conversation.ui_history) == 2
    assert loaded_conversation.ui_history[1]["text"] == "Hi test from OpenGPT!"
