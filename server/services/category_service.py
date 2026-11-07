"""
Category Service
Encapsulates domain logic and business validation for categories.
Provides the Service layer between Category Routes and CategoryRepository.
"""

from typing import List, Dict, Any, Optional
from server.repositories.category_repository import CategoryRepository


class CategoryService:
    """Orchestrates category retrieval, validation, and creation."""

    def __init__(
        self,
        category_repo: Optional[CategoryRepository] = None,
        db_path: Optional[str] = None,
    ):
        self.category_repo = category_repo or CategoryRepository(db_path)

    def get_all_categories(self) -> List[Dict[str, Any]]:
        """Retrieve all registered categories."""
        return self.category_repo.get_all()

    def get_category_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a category by primary key ID."""
        return self.category_repo.get_by_id(category_id)

    def validate_category_name(self, name: Any) -> str:
        """Validate and clean category name. Raises ValueError on empty/duplicate."""
        if name is None:
            raise ValueError("Category name cannot be empty.")
        clean_name = str(name).strip()
        if not clean_name:
            raise ValueError("Category name cannot be empty.")

        existing = self.category_repo.get_by_name(clean_name)
        if existing:
            raise ValueError(f"Category '{clean_name}' already exists.")
        return clean_name

    def create_category(self, name: Any) -> Dict[str, Any]:
        """Validate and create a new category."""
        clean_name = self.validate_category_name(name)
        cat_id = self.category_repo.create(clean_name)
        new_cat = self.category_repo.get_by_id(cat_id)
        if not new_cat:
            raise RuntimeError(f"Failed to retrieve created category with ID {cat_id}.")
        return new_cat
