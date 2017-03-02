# -*- coding: utf-8 -*-
from plone.resource.directory import PersistentResourceDirectory
from Products.Five.browser import BrowserView

import json


class FileUploadView(BrowserView):
    """
    Handle file uploads
    """

    def __call__(self):
        filedata = self.request.form.get("file", None)

        if filedata is None:
            return json.dumps({'failure':'error'})
        
        directory = PersistentResourceDirectory(self.context)
        name = filedata.filename.encode('utf-8')
        data = filedata.read()

        try:
            directory.writeFile(name, data)
            self.request.response.setHeader('Content-Type', 'application/json')
        except:
            return json.dumps({'failure':'error'})

        return json.dumps({'success':'create'})
