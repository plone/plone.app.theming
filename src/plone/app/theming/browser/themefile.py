# -*- coding: utf-8 -*-
from Products.Five.browser import BrowserView
from plone.resource.directory import PersistentResourceDirectory
import json

class FileUploadView(BrowserView):
    """
    Handle file uploads
    """

    def __call__(self):
        filedata = self.request.form.get("file", None)

        if filedata is None:
            return

        directory = PersistentResourceDirectory(self.context)

        name = filedata.filename.encode('utf-8')
        data = filedata.read().encode('utf-8')

        directory.writeFile(name, data)

        self.request.response.setHeader('Content-Type', 'application/json')

        return json.dumps({'sucess':'create'})
