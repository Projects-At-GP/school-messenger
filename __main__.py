from NAA.web import API

from school_messenger.versions import (
    V0,
    V1
)


api = API(host="0.0.0.0", port=3333, name="School Messenger",
          version_pattern="v{version}", default=0)


api.add_version(version=0)(V0)  # test-version without database
api.add_version(version=1)(V1)


api(debug=True, reload=True)
