"""A tiny HTML reader for page tests: a tree of elements with their attributes and text, standard library only."""
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class Node:
    def __init__(self, tag, attrs, parent=None):
        self.tag = tag
        self.attrs = {k: (v if v is not None else "") for k, v in attrs}
        self.parent = parent
        self.children = []  # Node or str

    @property
    def classes(self):
        return self.attrs.get("class", "").split()

    def text(self):
        parts = [c if isinstance(c, str) else c.text() for c in self.children]
        return " ".join("".join(parts).split())

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.walk()

    def find_all(self, tag=None, **attrs):
        return [n for n in self.walk() if (tag is None or n.tag == tag) and all(n.attrs.get(k.replace("_", "-")) == v for k, v in attrs.items())]


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", [])
        self.current = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.current)
        self.current.children.append(node)
        if tag not in VOID:
            self.current = node

    def handle_startendtag(self, tag, attrs):
        self.current.children.append(Node(tag, attrs, self.current))

    def handle_endtag(self, tag):
        node = self.current
        while node is not self.root and node.tag != tag:
            node = node.parent
        if node is not self.root:
            self.current = node.parent

    def handle_data(self, data):
        self.current.children.append(data)


def parse(html):
    builder = _Builder()
    builder.feed(html)
    return builder.root


def forms(root):
    """Every form as {action, method, fields: {name: value}, buttons: [text]}; fields lists the named inputs."""
    out = []
    for form in root.find_all("form"):
        fields = {n.attrs["name"]: n.attrs.get("value", "") for n in form.find_all("input") if "name" in n.attrs}
        out.append(
            {
                "action": form.attrs.get("action", ""),
                "method": form.attrs.get("method", "get").lower(),
                "fields": fields,
                "buttons": [b.text() for b in form.find_all("button")],
                "node": form,
            }
        )
    return out


def form_with_button(root, button_text):
    matches = [f for f in forms(root) if any(button_text == b for b in f["buttons"])]
    assert len(matches) == 1, f"expected one form with the button {button_text!r}, found {len(matches)}"
    return matches[0]
