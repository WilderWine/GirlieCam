from firebase_admin import db




def register_user(email: str, password: str):
    def sanitize_email(email):
        return email.replace('.', '_dot_').replace('@', '_at_')
    try:
        email_key = email.lower()
        new_name = email_key.split('@')[0]
        email_key = sanitize_email(email_key)
        user_ref = db.reference(f'users/{email_key}')


        if user_ref.get() is None:
            user_ref.set({
                'name': new_name,
                'password': password,
                'filters': {},
                'stickers': {},
                'masks': {}
            })
            print("Successfully resistered!")
            return True
        else:
            print("User exists!")
            return False
    except Exception as e:
        print(f"Error while register: {e}")
        return False

def login_user(email: str, password: str):
    def sanitize_email(email):
        return email.replace('.', '_dot_').replace('@', '_at_')
    try:
        email_key = email.lower()
        email_key = sanitize_email(email_key)
        user_ref = db.reference(f'users/{email_key}')
        user_data = user_ref.get()
        if user_data is not None:
            if user_data['password'] == password:
                print("Successfully entered!")
                print("Userdata:", user_data)
                return user_data
            else:
                print("Wrong password!")
                return None
        else:
            print("No such user!")
    except Exception as e:
        print(f"Error while login: {e}")
        return None