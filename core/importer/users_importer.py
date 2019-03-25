from abc import ABCMeta, abstractmethod


class UsersImporter(metaclass=ABCMeta):

    @abstractmethod
    def import_all_users(self):
        pass

    @abstractmethod
    def import_from_username(self, username):
        pass
