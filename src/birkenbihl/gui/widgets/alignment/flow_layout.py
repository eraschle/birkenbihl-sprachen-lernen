"""Flow layout for horizontal word arrangement with wrapping."""

from PySide6.QtCore import QRect, QSize
from PySide6.QtWidgets import QLayout, QLayoutItem, QWidget


class FlowLayout(QLayout):
    """Flow layout that arranges items horizontally with automatic wrapping.

    Items flow from left to right, wrapping to new rows when needed.
    Used for displaying word tags in unassigned pool.
    """

    def __init__(self, parent: QWidget | None = None, margin: int = 0, spacing: int = -1):
        """Initialize flow layout.

        Args:
            parent: Parent widget
            margin: Layout margin
            spacing: Space between items
        """
        super().__init__(parent)
        self._item_list: list[QLayoutItem] = []
        self.setContentsMargins(margin, margin, margin, margin)
        if spacing >= 0:
            self.setSpacing(spacing)

    def addItem(self, item: QLayoutItem) -> None:
        """Add item to layout.

        Args:
            item: Layout item to add
        """
        self._item_list.append(item)

    def count(self) -> int:
        """Return number of items in layout.

        Returns:
            Item count
        """
        return len(self._item_list)

    def itemAt(self, index: int) -> QLayoutItem | None:
        """Get item at index.

        Args:
            index: Item index

        Returns:
            Layout item or None if index out of range
        """
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index: int) -> QLayoutItem:
        """Remove and return item at index.

        Args:
            index: Item index

        Returns:
            Removed item or empty spacer if out of range
        """
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        # Qt expects non-None, but we return empty item when out of range
        from PySide6.QtWidgets import QSpacerItem
        return QSpacerItem(0, 0)

    def sizeHint(self) -> QSize:
        """Return size hint for layout.

        Returns:
            Preferred size
        """
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        """Calculate minimum size needed.

        Returns:
            Minimum size
        """
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())

        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def setGeometry(self, rect: QRect) -> None:
        """Arrange items within given rectangle.

        Args:
            rect: Rectangle to arrange items in
        """
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        """Arrange items and return height used.

        Args:
            rect: Rectangle to arrange in
            test_only: If True, only calculate height

        Returns:
            Height used
        """
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self._item_list:
            widget = item.widget()
            if not widget:
                continue

            space_x = spacing
            space_y = spacing

            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                from PySide6.QtCore import QPoint
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()
