import googleapi

running = True

def main():

    print("Started OpenGPT! Type your questions here.")

    while running:
        user_input = input()
        print("Running...")
        print(googleapi.send_message(user_input))

