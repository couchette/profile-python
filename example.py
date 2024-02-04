from instrumentor import *


@PROFILE_FUNCTION
def hello_world():
    with PROFILE_SCOPE("print"):
        print("Hello World!")
    return None


if __name__ == "__main__":

    PROFILE_BEGIN_SESSION("example", "example_profile.json")
    hello_world()
    PROFILE_END_SESSION()
