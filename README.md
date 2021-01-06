# OrthoViewLite
Modified Version of [OrthoView](https://github.com/kklmn/OrthoView) by [Konstantin Klementiev](https://github.com/kklmn/) with File Selector

### Requirements

- PyQt5
- cv2
- matplotlib

If you want another start directory in TreeView change line 155

```self.mylistwidget.setRootIndex(self.fileModel.index(QStandardPaths.standardLocations(QStandardPaths.PicturesLocation)[0]))```

for example using the root of your system

```self.mylistwidget.setRootIndex(self.fileModel.index("/"))```

![alt text](https://github.com/Axel-Erfurt/OrthoViewLite/blob/main/screenshot.png)
