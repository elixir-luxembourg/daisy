from abc import ABCMeta, abstractmethod


class UsersImporter(metaclass=ABCMeta):
    @abstractmethod
    def import_all_users(self):
        pass
