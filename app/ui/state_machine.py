import logging

# Simple in-memory state store (UserID -> StateDict)
# In a production multi-user bot, this should be in Redis/DB,
# but for a Userbot (single user usually), memory is fine.
USER_STATES = {}

class StateMachine:
    """
    Manages the user's current step in a wizard flow.
    """

    @staticmethod
    def get_state(user_id):
        return USER_STATES.get(user_id, {})

    @staticmethod
    def set_state(user_id, key, value):
        if user_id not in USER_STATES:
            USER_STATES[user_id] = {}
        USER_STATES[user_id][key] = value

    @staticmethod
    def clear_state(user_id):
        if user_id in USER_STATES:
            del USER_STATES[user_id]

    @staticmethod
    def set_step(user_id, step_name):
        StateMachine.set_state(user_id, 'step', step_name)

    @staticmethod
    def get_step(user_id):
        return StateMachine.get_state(user_id).get('step', None)
