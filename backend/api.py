from . import auth,launch,java

credentials = auth.authenticate()

instance = launch.Instance("path/to/instance")
instance.memory = 4096