class Note:
    def __init__(self, title, content):
        self.title = title
        self.content = content

    def to_dict(self):
        return {"title": self.title, "content": self.content}