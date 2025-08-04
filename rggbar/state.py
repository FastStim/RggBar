import os
import pickle

__all__ = ["load"]


def load(path="state/state.pkl"):
    state = None

    path = os.path.expanduser(path)
    path = os.path.abspath(path)

    if os.path.exists(path):
        state = read(path)

    return state


def read(path):
    try:
        with open(path, "rb") as file:
            return pickle.load(file)
    except EOFError:
        return None


def save(obj, path="state/state.pkl"):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as file:
            pickle.dump(obj, file, protocol=pickle.HIGHEST_PROTOCOL)

        return obj
    except EOFError:
        print('error')
        return None
