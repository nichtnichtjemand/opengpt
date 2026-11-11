import googleapi

running = True

def main():

    print("Started OpenGPT! Type your questions here.")
    conversation = googleapi.Conversation()

    while running:
        user_input = input()
        print("Running...")
        print(conversation.send_message(user_input))

