from Products.Five import BrowserView


class Title(BrowserView):
    def __call__(self):
        return self.context.Title()
