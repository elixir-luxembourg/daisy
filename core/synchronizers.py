from abc import ABC, abstractmethod
from typing import Dict, List, Tuple


class AccountSynchronizationException(Exception):
    pass


class AccountSynchronizationMethod(ABC):
    """
    Class that represents a method of obtaining the list of users
    which then will be used to synchronize the account informations
    """

    @abstractmethod
    def get_list_of_users(self) -> List[Dict]:
        """
        Should return a list of dictionaries with user information,
        like: {'id': '', 'email': '', 'first_name': '', etc. }
        """
        pass

    @abstractmethod
    def test_connection(self) -> None:
        """
        Should test the connection to the data source and raise an exception
        if there is something wrong
        """
        pass


class AccountSynchronizer(ABC):
    """
    Class that does the synchronization of the account information
    based on the information provided by the synchronizer class
    """

    def __init__(self, synchronizer: AccountSynchronizationMethod = None):
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Should test the connection of the synchronizer and raise an exception
        if there is something wrong.
        """
        pass

    @abstractmethod
    def synchronize(self) -> bool:
        """
        Should perform the synchronization itself
        """
        pass

    @abstractmethod
    def check_for_problems(self) -> bool:
        """
        Should go through the incoming information
        and see if there will be any problems with updates
        (e.g. duplicated entry)
        """
        pass


class DummySynchronizationMethod(AccountSynchronizationMethod):
    """
    This synchronizer will never report that there is something to change in the accounts
    """

    def __init__(self, config: Dict = None, connect=False) -> None:
        pass

    def test_connection(self) -> bool:
        return True

    def get_list_of_users(self) -> List[Dict]:
        return []


class DummyAccountSynchronizer(AccountSynchronizer):
    """
    This synchronizer will never change the accounts
    (moreover it will allow to skip passing the synchronizer in the constructor)
    """

    def __init__(self, synchronizer: AccountSynchronizationMethod = None):
        pass

    def test_connection(self):
        return True

    def compare(self) -> Tuple[List, List, List]:
        return [], [], []

    def synchronize(self) -> bool:
        return True

    def check_for_problems(self) -> bool:
        return True
