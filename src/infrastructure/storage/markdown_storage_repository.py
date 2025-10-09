from src.domain.entities.board import Board
from src.domain.entities.column import Column
from src.domain.entities.item import Item
from src.domain.repositories.storage_repository import StorageRepository
from src.utils.path_resolver import PathResolver
from src.utils.logger_factory import ContextAwareLogger
from src.infrastructure.storage.board_persistence import BoardPersistence
from src.infrastructure.storage.file_operations import find_item_file_by_id


class MarkdownStorageRepository(StorageRepository):
    def __init__(self, path_resolver: PathResolver, logger: ContextAwareLogger):
        self.path_resolver = path_resolver
        self.logger = logger
        self.persistence = BoardPersistence(path_resolver.get_data_dir())

    def delete_item_from_column(self, board: Board, item: Item, column: Column) -> bool:
        self.logger.debug(
            "Deleting item from column storage",
            board=board.name,
            column=column.name,
            item=item.title,
        )

        column_dir = self.path_resolver.get_column_directory(board.name, column.name)
        item_file = find_item_file_by_id(column_dir, item.id)

        if item_file and item_file.exists():
            try:
                item_file.unlink()
                self.logger.info(
                    "Successfully deleted item file",
                    board=board.name,
                    column=column.name,
                    item=item.title,
                )
                return True
            except Exception:
                self.logger.error(
                    "Failed to delete item file",
                    board=board.name,
                    column=column.name,
                    item=item.title,
                )
                return False

        self.logger.warning(
            "Item file not found for deletion",
            board=board.name,
            column=column.name,
            item=item.title,
        )
        return False

    def move_item_between_columns(
        self, board: Board, item: Item, old_column: Column, new_column: Column
    ) -> bool:
        self.logger.info(
            "Moving item between columns",
            board=board.name,
            item=item.title,
            column=f"{old_column.name} -> {new_column.name}",
        )

        # First save the item to the new column
        try:
            self.persistence.save_item_to_column(
                board.name,
                new_column.name,
                {
                    "id": item.id,
                    "title": item.title,
                    "description": item.description,
                    "parent_id": item.parent_id,
                    "created_at": item.created_at,
                    "moved_in_progress_at": item.moved_in_progress_at,
                    "moved_in_done_at": item.moved_in_done_at,
                    "worked_on_for": item.worked_on_for,
                },
            )

            self.logger.debug(
                "Saved item to new column",
                board=board.name,
                column=new_column.name,
                item=item.title,
            )

            # Then delete from the old column
            if self.delete_item_from_column(board, item, old_column):
                self.logger.info(
                    "Successfully moved item between columns",
                    board=board.name,
                    item=item.title,
                    column=f"{old_column.name} -> {new_column.name}",
                )
                return True
            else:
                # If delete failed, try to clean up the new file
                self.logger.warning(
                    "Failed to delete from old column, cleaning up new column",
                    board=board.name,
                    item=item.title,
                )
                self.delete_item_from_column(board, item, new_column)
                return False

        except Exception:
            self.logger.error(
                "Failed to save item to new column",
                board=board.name,
                column=new_column.name,
                item=item.title,
            )
            return False

    def save_board_to_storage(self, board: Board) -> None:
        self.logger.debug("Saving board to storage", board=board.name)

        try:
            # Save all columns and their items
            for column in board.columns:
                self.logger.debug("Saving column", board=board.name, column=column.name)

                # Ensure column directory exists
                self.path_resolver.get_column_directory(
                    board.name, column.name
                )

                # Save column metadata
                self.persistence.save_column_metadata(
                    board.name,
                    column.name,
                    {
                        "id": column.id,
                        "name": column.name,
                        "position": column.position,
                        "limit": column.limit,
                        "created_at": column.created_at,
                    },
                )

                # Save all items in this column
                for item in column.items:
                    self.persistence.save_item_to_column(
                        board.name,
                        column.name,
                        {
                            "id": item.id,
                            "title": item.title,
                            "description": item.description,
                            "parent_id": item.parent_id,
                            "created_at": item.created_at,
                            "moved_in_progress_at": item.moved_in_progress_at,
                            "moved_in_done_at": item.moved_in_done_at,
                            "worked_on_for": item.worked_on_for,
                        },
                    )

            self.logger.info("Successfully saved board to storage", board=board.name)

        except Exception:
            self.logger.error("Failed to save board to storage", board=board.name)
            raise

