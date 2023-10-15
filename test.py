import os
import uuid

os.environ["ADMIN_PASSWD"] = str(uuid.uuid4())
print(os.getenv("ADMIN_PASSWD"))