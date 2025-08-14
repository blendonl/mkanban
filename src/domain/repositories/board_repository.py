from abc import ABC, abstractmethod
from typing import List, Optional
from ...core.types import BoardId
from ..entities.board import Board


class BoardRepository(ABC):
    @abstractmethod
    def load_all_boards(self) -> List[Board]:
        pass

    @abstractmethod
    def load_board_by_id(self, board_id: BoardId) -> Optional[Board]:
        pass

    @abstractmethod
    def load_board_by_name(self, board_name: str) -> Optional[Board]:
        pass

    @abstractmethod
    def save_board(self, board: Board) -> None:
        pass

    @abstractmethod
    def delete_board(self, board_id: BoardId) -> bool:
        pass

    @abstractmethod
    def list_board_names(self) -> List[str]:
        pass

    @abstractmethod
    def create_sample_board(self, name: str) -> Board:
        pass