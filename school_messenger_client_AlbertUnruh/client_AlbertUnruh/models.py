import datetime


class ID:
    EPOCH = property(lambda self: 1609455600000)  # type: int

    def __init__(self, id):  # noqa
        """
        Parameters
        ----------
        id: int, str
        """
        self._id = int(id)

    @property
    def id(self):
        """
        Returns
        -------
        int
        """
        return self._id

    @property
    def timestamp(self):
        """
        Returns
        -------
        datetime.datetime
        """
        return datetime.datetime.utcfromtimestamp(((self.id >> 15) + self.EPOCH) / 1000)
