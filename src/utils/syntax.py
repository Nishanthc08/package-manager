from __future__ import annotations

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor


class BashHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = []
        self._multi_line_rules: list[tuple[QRegularExpression, QRegularExpression, QTextCharFormat]] = []
        self._build_rules()

    def _fmt(self, color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
        f = QTextCharFormat()
        f.setForeground(QColor(color))
        if bold:
            f.setFontWeight(QFont.Bold)
        if italic:
            f.setFontItalic(True)
        return f

    def _build_rules(self):
        # Shebang
        rule = QRegularExpression(r"^#!.+")
        fmt = self._fmt("#89b4fa", bold=True)
        self._rules.append((rule, fmt))

        # Comments
        rule = QRegularExpression(r"#[^\n]*")
        fmt = self._fmt("#6c7086", italic=True)
        self._rules.append((rule, fmt))

        # Keywords
        keywords = (
            r"\b(if|then|else|elif|fi|case|esac|for|while|until|do|done|"
            r"in|function|return|exit|break|continue|select|time|"
            r"declare|local|export|readonly|unset|"
            r"trap|wait|eval|exec|shift|source|type|"
            r"set|unset|read|printf|echo|test|kill|"
            r"let|mapfile|readarray)\b"
        )
        rule = QRegularExpression(keywords)
        fmt = self._format_from_style("#cba6f7", bold=True)
        self._rules.append((rule, fmt))

        # Double-quoted strings with variable interpolation awareness
        rule = QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"')
        fmt = self._fmt("#a6e3a1")
        self._rules.append((rule, fmt))

        # Single-quoted strings
        rule = QRegularExpression(r"'[^']*'")
        fmt = self._fmt("#f9e2af")
        self._rules.append((rule, fmt))

        # Variable expansion: ${...}
        rule = QRegularExpression(r"\$\{[^}]+\}")
        fmt = self._fmt("#fab387")
        self._rules.append((rule, fmt))

        # Variable expansion: $var (simple)
        rule = QRegularExpression(r"\$[a-zA-Z_][a-zA-Z0-9_]*")
        fmt = self._fmt("#fab387")
        self._rules.append((rule, fmt))

        # Command substitution: $(...)
        rule = QRegularExpression(r"\$\([^)]+\)")
        fmt = self._fmt("#89dceb")
        self._rules.append((rule, fmt))

        # Backtick command substitution
        rule = QRegularExpression(r"`[^`]+`")
        fmt = self._fmt("#89dceb")
        self._rules.append((rule, fmt))

        # Numbers
        rule = QRegularExpression(r"\b[0-9]+\b")
        fmt = self._fmt("#f38ba8")
        self._rules.append((rule, fmt))

        # Operators
        rule = QRegularExpression(r"(;;|&&|\|\||<<|>>|2>&1|>&2|&>|<>|<&|>&|\|)")
        fmt = self._fmt("#89b4fa", bold=True)
        self._rules.append((rule, fmt))

        # Redirections
        rule = QRegularExpression(r"(>|<|>>|<<|\|)\s*")
        fmt2 = self._fmt("#89b4fa")
        self._rules.append((rule, fmt2))

    def _format_from_style(self, color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
        f = QTextCharFormat()
        f.setForeground(QColor(color))
        if bold:
            f.setFontWeight(QFont.Bold)
        if italic:
            f.setFontItalic(True)
        return f

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


class ControlHighlighter(QSyntaxHighlighter):
    _FIELD_NAMES = [
        "Package", "Version", "Maintainer", "Description", "Architecture",
        "Section", "Priority", "Essential", "Homepage", "Source",
        "Depends", "Pre-Depends", "Recommends", "Suggests",
        "Breaks", "Conflicts", "Provides", "Replaces", "Built-Using",
        "Installed-Size", "Multi-Arch", "Origin", "Bugs", "Tags",
        "Enhances",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = []
        self._build_rules()

    def _fmt(self, color: str, bold: bool = False) -> QTextCharFormat:
        f = QTextCharFormat()
        f.setForeground(QColor(color))
        if bold:
            f.setFontWeight(QFont.Bold)
        return f

    def _build_rules(self):
        # Field names (bold colored)
        field_pattern = r"^(" + "|".join(self._FIELD_NAMES) + r")\s*:"
        rule = QRegularExpression(field_pattern, QRegularExpression.MultilineOption)
        fmt = self._fmt("#89b4fa", bold=True)
        self._rules.append((rule, fmt))

        # Field values after the colon (for single-line fields)
        rule = QRegularExpression(r":\s(.+)$", QRegularExpression.MultilineOption)
        fmt = self._fmt("#cdd6f4")
        self._rules.append((rule, fmt))

        # Continuation lines (space-prefixed)
        rule = QRegularExpression(r"^\s+\S.+", QRegularExpression.MultilineOption)
        fmt = self._fmt("#a6adc8")
        self._rules.append((rule, fmt))

        # Comment lines
        rule = QRegularExpression(r"^#.*", QRegularExpression.MultilineOption)
        fmt = self._fmt("#6c7086", bold=False)
        self._rules.append((rule, fmt))

        # URLs in fields
        rule = QRegularExpression(r"https?://[^\s]+")
        fmt = self._fmt("#89dceb")
        self._rules.append((rule, fmt))

        # Version numbers in dependency fields
        rule = QRegularExpression(r"\([<>=!]+\s*[^)]+\)")
        fmt = self._fmt("#f9e2af")
        self._rules.append((rule, fmt))

        # Package names in dependency lists (after field name)
        rule = QRegularExpression(r"(?<=:)\s*([a-zA-Z0-9][a-zA-Z0-9+\-.]+)")
        fmt2 = self._fmt("#a6e3a1")
        self._rules.append((rule, fmt2))

        # Architecture values
        rule = QRegularExpression(r"\b(amd64|i386|arm64|armhf|armel|all|mips64el|ppc64el|s390x|riscv64)\b")
        fmt = self._fmt("#f38ba8")
        self._rules.append((rule, fmt))

        # yes/no values
        rule = QRegularExpression(r"\b(yes|no)\b")
        fmt = self._fmt("#fab387", bold=True)
        self._rules.append((rule, fmt))

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
